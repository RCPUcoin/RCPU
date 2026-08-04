/*
 * RCPU NOMP Pool - RandomX mining pool based on NOMP framework
 *
 * Block header structure (112 bytes, verified with real blocks):
 *   version(4 LE) + prevhash(32 internal LE) + merkleroot(32 internal LE)
 *   + ntime(4 LE) + nbits(4 LE) + nonce(4 LE) + hashRandomX(32 internal LE)
 *
 * Share verification: Call computerandomxhash RPC, judge with commitment(BigInt) <= target
 * Block submission: segwit format coinbase (with marker/flag/witness), hashRandomX filled with reversed hash
 *
 * Byte order (verified):
 *   - Stratum mining.notify: version/nbits/ntime = BE hex (display), prevhash = display BE hex, merkle_branches = display BE
 *   - miner submit: ntime = BE hex (need parseInt + le32), nonce = BE hex (parseInt + le32)
 *   - merkle root: dsha256(coinbase) used directly, branch participates directly as display BE bytes (no reversal)
*   - hashRandomX: RPC returns display BE, block header needs internal LE (reversed)
 */

const net = require('net');
const fs = require('fs');
const crypto = require('crypto');
const http = require('http');

// ============ Configuration ============
const POOL_PORT = 3334;
const RPC_HOST = '127.0.0.1';
const RPC_PORT = 9962;
const RPC_USER = 'rcpu';
const RPC_PASS = 'rcpupass';
const POOL_ADDR = 'rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0';
const EXTRA_NONCE1_SIZE = 4;
const EXTRA_NONCE2_SIZE = 4;
const SHARE_DIFFICULTY = 0.000001; // [FIX 2026-08-03] Aligned with miner diff fix; network difficulty ~6.1e-5, low share difficulty for easy verification           // Miner share difficulty (increase to reduce share submission frequency, lower RPC load)
const RPC_THROTTLE_MS = 50;              // Minimum RPC call interval
const TEMPLATE_POLL_MS = 10000;          // Template polling interval (reduce frequency)
const LOG_STATS_MS = 30000;              // Statistics log interval
const MIN_SHARE_INTERVAL_MS = 500;       // Minimum share submission interval per miner (500ms, greatly reduces RPC load)

// ============ Utility Functions ============
function log(msg) {
    console.log('[' + new Date().toISOString() + '] ' + msg);
}

function le32(n) {
    const buf = Buffer.alloc(4);
    buf.writeUInt32LE(n >>> 0, 0);
    return buf;
}

function reverseBuffer(buf) {
    return Buffer.from(buf).reverse();
}

function dsha256(data) {
    return crypto.createHash('sha256').update(
        crypto.createHash('sha256').update(data).digest()
    ).digest();
}

function encodeVarint(n) {
    if (n < 0xfd) return Buffer.from([n]);
    if (n <= 0xffff) return Buffer.from([0xfd, n & 0xff, (n >> 8) & 0xff]);
    if (n <= 0xffffff) return Buffer.from([0xfe, n & 0xff, (n >> 8) & 0xff, (n >> 16) & 0xff, (n >> 24) & 0xff]);
    return Buffer.from([0xff, n & 0xff, (n >> 8) & 0xff, (n >> 16) & 0xff, (n >> 24) & 0xff, 0, 0, 0, 0]);
}

// BIP34 height encoding (verified: height 82 → 0152)
function encodeBIP34Height(height) {
    if (height === 0) return Buffer.from([0x00]);
    if (height >= 1 && height <= 16) return Buffer.from([0x50 + height]);
    const bytes = [];
    let h = height;
    while (h > 0) {
        bytes.push(h & 0xff);
        h = Math.floor(h / 256);
    }
    while (bytes.length > 0 && bytes[bytes.length - 1] === 0) bytes.pop();
    // [FIX] Bitcoin script number: if the highest byte has high bit set, append 0x00 sign byte
    if (bytes.length > 0 && (bytes[bytes.length - 1] & 0x80)) bytes.push(0x00);
    return Buffer.concat([Buffer.from([bytes.length]), Buffer.from(bytes)]);
}

// ============ RPC Calls (with throttling) ============
let lastRpcTime = 0;
function rpcCall(method, params) {
    if (!params) params = [];
    const now = Date.now();
    const wait = Math.max(0, RPC_THROTTLE_MS - (now - lastRpcTime));
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            lastRpcTime = Date.now();
            const payload = JSON.stringify({
                jsonrpc: '1.0', id: Date.now() + Math.random(),
                method: method, params: params
            });
            const auth = Buffer.from(RPC_USER + ':' + RPC_PASS).toString('base64');
            const req = http.request({
                hostname: RPC_HOST, port: RPC_PORT, path: '/', method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(payload),
                    'Authorization': 'Basic ' + auth
                },
                timeout: 30000
            }, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const resp = JSON.parse(data);
                        if (resp.error) reject(new Error(resp.error.message || JSON.stringify(resp.error)));
                        else resolve(resp.result);
                    } catch (e) {
                        reject(new Error('JSON parse error: ' + data.substring(0, 200)));
                    }
                });
            });
            req.on('error', reject);
            req.on('timeout', () => { req.destroy(); reject(new Error('RPC timeout')); });
            req.write(payload);
            req.end();
        }, wait);
    });
}

// ============ Global State ============
let currentJob = null;
let poolScriptPubKey = null;
let jobCounter = 0;
const miners = new Map();
const stats = { validShares: 0, invalidShares: 0, blocksFound: 0, blocksSubmitted: 0, rpcErrors: 0 };

// ============ [PAYOUT] Share accounting (by miner address, persisted to disk) ============
const SHARES_FILE = '/root/pool_shares.json';
const BLOCKS_FILE = '/root/pool_blocks.json';
let roundShares = {};   // Current round (since last block) valid shares per address
let blocks = [];        // Block records
try { const d = JSON.parse(fs.readFileSync(SHARES_FILE, 'utf8')); roundShares = d.roundShares || {}; } catch (e) {}
try { blocks = JSON.parse(fs.readFileSync(BLOCKS_FILE, 'utf8')) || []; } catch (e) {}

function saveShares() {
    try { fs.writeFileSync(SHARES_FILE, JSON.stringify({ roundShares })); } catch (e) {}
}
function saveBlocks() {
    try { fs.writeFileSync(BLOCKS_FILE, JSON.stringify(blocks, null, 1)); } catch (e) {}
}
// Parse payout address from stratum username: "rcpu1xxxx.worker" -> "rcpu1xxxx"; otherwise assign to pool (POOL)
function parseMinerAddress(worker) {
    if (!worker) return 'POOL';
    const addr = String(worker).split('.')[0];
    if (/^rcpu1[02-9ac-hj-np-z]{20,60}$/.test(addr)) return addr;
    return 'POOL';
}
// Record a valid share
function creditShare(worker) {
    const addr = parseMinerAddress(worker);
    roundShares[addr] = (roundShares[addr] || 0) + 1;
    saveShares();
    return addr;
}
// Block found: snapshot current round shares, start new round
function snapshotRound(height, rewardSat) {
    const shares = Object.assign({}, roundShares);
    const total = Object.values(shares).reduce((a, b) => a + b, 0);
    blocks.push({ height, reward: rewardSat, shares, totalShares: total,
                  status: 'pending', txid: null, time: new Date().toISOString() });
    roundShares = {};
    saveShares();
    saveBlocks();
    log('[PAYOUT] Block snapshot height=' + height + ' reward=' + rewardSat + ' totalShares=' + total + ' miners=' + JSON.stringify(shares));
}


// ============ Get Pool scriptPubKey ============
async function getPoolScriptPubKey() {
    try {
        const result = await rpcCall('validateaddress', [POOL_ADDR]);
        if (result && result.scriptPubKey) {
            log('Pool scriptPubKey: ' + result.scriptPubKey);
            return result.scriptPubKey;
        }
    } catch (e) { log('Failed to get scriptPubKey: ' + e.message); }
    return '0014f98e12c502de925bbe73f6e7a0d2da2af4f74b48'; // fallback P2WPKH
}

// ============ Merkle Root Calculation (consistent with SCASH official miner: branch participates directly as display BE bytes, no reversal) ============
// [FIX] Compute correct Bitcoin merkle tree branches
function computeMerkleBranches(txidsDisplayBE) {
    if (txidsDisplayBE.length === 0) return [];
    let level = txidsDisplayBE.map(txid => Buffer.from(txid, 'hex').reverse());
    const branches = [];
    while (level.length > 0) {
        branches.push(level[0]);
        level = level.slice(1);
        if (level.length === 0) break;
        const nextLevel = [];
        for (let i = 0; i < level.length; i += 2) {
            const left = level[i];
            const right = (i + 1 < level.length) ? level[i + 1] : level[i];
            nextLevel.push(dsha256(Buffer.concat([left, right])));
        }
        level = nextLevel;
    }
    return branches.map(b => b.reverse().toString('hex'));
}


function computeMerkleRoot(coinbaseTxBytes, merkleBranchesDisplayBE) {
    let currentHash = dsha256(coinbaseTxBytes);
    for (const branchDisplayBE of merkleBranchesDisplayBE) {
        // [FIX 2026-08-03] GBT/notify branches are display BE, consensus merkle needs internal LE -> reverse
        const branchBytes = Buffer.from(branchDisplayBE, 'hex').reverse();
        const combined = Buffer.concat([currentHash, branchBytes]);
        currentHash = dsha256(combined);
    }
    return currentHash;
}

// ============ Get Block Template and Create Job ============
async function updateTemplate() {
    let tmpl;
    try {
        tmpl = await rpcCall('getblocktemplate', [{ rules: ['segwit'] }]);
    } catch (e) {
        log('Failed to get template: ' + e.message);
        return;
    }
    if (!tmpl) return;

    if (!poolScriptPubKey) {
        poolScriptPubKey = await getPoolScriptPubKey();
    }

    const height = tmpl.height;
    const version = tmpl.version & 0xffffffff;
    const ntime = tmpl.curtime;
    const nbits = parseInt(tmpl.bits, 16);
    const prevHashDisplayBE = tmpl.previousblockhash;

    // Only create new job on block change (reduce broadcast frequency)
    if (currentJob && currentJob.height === height && currentJob.prevHashDisplayBE === prevHashDisplayBE) {
        return;
    }

    // === Build coinbase (legacy format, for Stratum and share verification) ===
    const heightScript = encodeBIP34Height(height);
    const extranonceTotalLen = EXTRA_NONCE1_SIZE + EXTRA_NONCE2_SIZE;
    const scriptSigLen = heightScript.length + extranonceTotalLen;

    // coinb1 = version + vin_count + prevout(32+4) + scriptsig_len + height_script
    const coinb1 = Buffer.concat([
        le32(1),                                    // tx version = 1
        Buffer.from([1]),                           // vin count = 1
        Buffer.alloc(32, 0),                        // prevout hash (zeros)
        Buffer.from([0xff, 0xff, 0xff, 0xff]),      // prevout index
        encodeVarint(scriptSigLen),                 // scriptSig length
        heightScript                                // BIP34 height
    ]).toString('hex');

    // Build outputs
    const valueBuf = Buffer.alloc(8);
    valueBuf.writeBigUInt64LE(BigInt(tmpl.coinbasevalue), 0);
    const spk = Buffer.from(poolScriptPubKey, 'hex');
    const output0 = Buffer.concat([valueBuf, encodeVarint(spk.length), spk]);

    let outputs = [output0];
    // witness commitment output (value=0)
    if (tmpl.default_witness_commitment) {
        const wc = Buffer.from(tmpl.default_witness_commitment, 'hex');
        const wcOutput = Buffer.concat([Buffer.alloc(8, 0), encodeVarint(wc.length), wc]);
        outputs.push(wcOutput);
    }

    // coinb2 = sequence + vout_count + outputs + locktime
    const coinb2 = Buffer.concat([
        Buffer.from([0xff, 0xff, 0xff, 0xff]),      // sequence
        encodeVarint(outputs.length),
        ...outputs,
        Buffer.alloc(4, 0)                          // locktime = 0
    ]).toString('hex');

    // merkle branches (display BE, fetched directly from GBT)
    const txids = (tmpl.transactions || []).map(tx => tx.txid);
    const merkleBranches = computeMerkleBranches(txids);

    // Stratum mining.notify parameters (standard BE/display format, cpuminer-scash compatible)
    const prevHashInternalLE = reverseBuffer(Buffer.from(prevHashDisplayBE, 'hex')).toString('hex');
    const versionBEHex = (version >>> 0).toString(16).padStart(8, '0');
    const nbitsBEHex = (nbits >>> 0).toString(16).padStart(8, '0');
    const ntimeBEHex = (ntime >>> 0).toString(16).padStart(8, '0');

    jobCounter++;
    currentJob = {
        jobId: jobCounter.toString(16).padStart(8, '0'),
        height: height,
        version: version,
        prevHashDisplayBE: prevHashDisplayBE,
        prevHashInternalLE: prevHashInternalLE,
        versionBEHex: versionBEHex,
        nbits: nbits,
        nbitsBEHex: nbitsBEHex,
        ntime: ntime,
        ntimeBEHex: ntimeBEHex,
        coinb1: coinb1,
        coinb2: coinb2,
        merkleBranches: merkleBranches,
        _txids: txids,  // Cache txids for debugging
        coinbasevalue: tmpl.coinbasevalue,
        target: tmpl.target || '',
        witnessCommitment: tmpl.default_witness_commitment || '',
        // Save transaction data from template (for submitblock)
        templateTxs: (tmpl.transactions || []).map(tx => tx.data)
    };

    log('New job: height=' + height + ' jobId=' + currentJob.jobId +
        ' nbits(BE)=' + nbitsBEHex + ' target=' + (tmpl.target || '').substring(0, 16) +
        '...' + ' txs=' + merkleBranches.length + ' miners=' + miners.size);

    // Broadcast to all miners
    for (const [, ctx] of miners) {
        sendJob(ctx);
    }
}

// ============ Send Stratum Message ============
function send(ctx, obj) {
    if (ctx.sock && !ctx.sock.destroyed && ctx.sock.writable) {
        try {
            const s = JSON.stringify(obj) + '\n';
            /* log('[' + ctx.id + '] >>> TXN: ' + s.substring(0, 200) + (s.length > 200 ? '...' : '')); */
            ctx.sock.write(s);
        } catch (e) {
            log('[' + ctx.id + '] write error: ' + e.message);
        }
    }
}

function sendJob(ctx) {
    if (!currentJob) return;
    // mining.notify (standard Stratum BE/display format, cpuminer-scash compatible):
    // [job_id, prevhash(BE), coinb1, coinb2, merkle_branches(BE), version(BE), nbits(BE), ntime(BE), clean]
    send(ctx, {
        id: null,
        method: 'mining.notify',
        params: [
            currentJob.jobId,
            currentJob.prevHashDisplayBE,     // display BE hex
            currentJob.coinb1,
            currentJob.coinb2,
            currentJob.merkleBranches,         // display BE hex array
            currentJob.versionBEHex,           // BE hex
            currentJob.nbitsBEHex,             // BE hex
            currentJob.ntimeBEHex,             // BE hex
            true                               // clean
        ]
    });
}

// ============ Share Verification + Block Submission ============
async function processShare(ctx, params) {
    const jobId = params[1] || '';
    const extraNonce2 = (params[2] || '00000000').padStart(EXTRA_NONCE2_SIZE * 2, '0');
    const ntimeHex = params[3] || currentJob.ntimeBEHex;  // BE hex, needs parseInt + le32
    const nonceHex = params[4] || '00000000';              // BE hex (value), needs parseInt + le32
    const en1 = ctx.en1 || '00000000';

    if (!currentJob || currentJob.jobId !== jobId) {
        return { valid: false, error: 'stale job' };
    }

    // 1. Build legacy coinbase (for computing txid/merkle root)
    const coinbaseHex = currentJob.coinb1 + en1 + extraNonce2 + currentJob.coinb2;
    const coinbaseBytes = Buffer.from(coinbaseHex, 'hex');

    // 2. Compute merkle root (internal LE, used directly in header)
    const merkleRoot = computeMerkleRoot(coinbaseBytes, currentJob.merkleBranches);

    // 3. Build 112-byte header (hashRandomX zeroed)
    //    version(LE) + prevhash(internal LE) + merkle(internal LE) + ntime(LE) + nbits(LE) + nonce(LE) + zeros(32)
    const header112 = Buffer.concat([
        le32(currentJob.version),
        Buffer.from(currentJob.prevHashInternalLE, 'hex'),
        merkleRoot,
        le32(parseInt(ntimeHex, 16)),               // ntime: BE hex → value → LE bytes
        le32(currentJob.nbits),
        le32(parseInt(nonceHex, 16)),               // nonce: BE hex → value → LE bytes
        Buffer.alloc(32, 0)                          // hashRandomX = zeros
    ]);

    if (header112.length !== 112) {
        return { valid: false, error: 'header length error' };
    }

    // ====== Diagnostic: First submit outputs PAIR (submit params + en1 + job fields + header112 hex) ======
    if (!stats._pairPrinted) {
        stats._pairPrinted = true;
        log('[PAIR-FULL-DEBUG] ' + JSON.stringify({
            en1: en1,
            submit_params: [params[0], jobId, extraNonce2, ntimeHex, nonceHex],
            job_coinb1: currentJob.coinb1,
            job_coinb2: currentJob.coinb2,
            job_branches: currentJob.merkleBranches,
            job_prevhash_displayBE: currentJob.prevHashDisplayBE,
            job_prevhash_internalLE: currentJob.prevHashInternalLE,
            job_versionBEHex: currentJob.versionBEHex,
            job_nbitsBEHex: currentJob.nbitsBEHex,
            job_ntimeBEHex: currentJob.ntimeBEHex,
            pool_header112_hex: header112.toString('hex')
        }));
    }

    // 4.5 Diagnostic: Compare header112 fields (for debug, once every 15 seconds)
    if (!stats._dbgCount || Date.now() - (stats._dbgLast || 0) > 15000) {
        stats._dbgLast = Date.now();
        stats._dbgCount = (stats._dbgCount || 0) + 1;
        const v = header112.readUInt32LE(0);
        const ph = header112.slice(4, 36).toString('hex');
        const mr = header112.slice(36, 68).toString('hex');
        const nt = header112.readUInt32LE(68);
        const nb = header112.readUInt32LE(72);
        const no = header112.readUInt32LE(76);
        const rh = header112.slice(80, 112).toString('hex');
        log('[DEBUG HEADER#' + stats._dbgCount + '] hex=' + header112.toString('hex'));
        log('[DEBUG#' + stats._dbgCount + '] v=' + v.toString(16) + ' ph=' + ph.substring(0,24) + '... mr=' + mr.substring(0,24) + '...');
        log('[DEBUG#' + stats._dbgCount + '] nt=' + nt.toString(16) + ' nb=' + nb.toString(16) + ' nonce=' + no.toString(16) + ' rxHash=' + rh.substring(0,24) + '...');
    }
    // 4. Call computerandomxhash RPC for verification
    let hashResult;
    try {
        hashResult = await rpcCall('computerandomxhash', [header112.toString('hex')]);
    } catch (e) {
        stats.rpcErrors++;
        return { valid: false, error: 'rpc: ' + e.message };
    }

    if (!hashResult || !hashResult.commitment) {
        stats.rpcErrors++;
        return { valid: false, error: 'rpc null result' };
    }

    const rxHash = hashResult.hash;              // display BE
    const commitment = hashResult.commitment;    // display BE
    const hashVerified = hashResult.hash_verified;

    // 5. Compare commitment vs target with BigInt (cannot use string comparison!)
    const targetHex = (currentJob.target || '').padStart(64, '0');
    const cmBig = BigInt('0x' + (commitment || '').padStart(64, '0'));
    const targetBig = BigInt('0x' + targetHex);
    const meetsNetworkTarget = cmBig > 0n && cmBig <= targetBig;

    // share difficulty: share_target = diff1 / SHARE_DIFFICULTY (consistent with miner mining.set_difficulty)
    // ★ Key fix: Use 1e9 scale (not 1e6), prevent tiny SHARE_DIFFICULTY (e.g. 1e-7) from causing scaled=0 → BigInt division by zero
    const diff1Big = BigInt('0x00000000ffff0000000000000000000000000000000000000000000000000000');
    const SCALE = 1_000_000_000; // 1e9
    let shareTargetBig;
    try {
        const shareDiffScaled = BigInt(Math.max(1, Math.round(SHARE_DIFFICULTY * SCALE)));  // At least 1 to prevent division by zero
        shareTargetBig = (diff1Big * BigInt(SCALE)) / shareDiffScaled;
    } catch (e) {
        // Fallback: set a very large share target (equivalent to very low difficulty, almost all commitments pass)
        shareTargetBig = BigInt('0x' + 'f'.repeat(64));
        log('[' + ctx.id + '] Warning: shareTargetBig calculation error (' + e.message + '), using all-F fallback');
    }

    // Debug log: print once every 30 shares
    if (stats.validShares % 30 === 0) {
        log('[' + ctx.id + '] share#' + stats.validShares + ' commitment=' + commitment.substring(0, 16) +
            '... netTarget=' + targetBig.toString(16).substring(0, 16) +
            ' meetNet=' + meetsNetworkTarget);
    }

    // Accept all shares with successful RPC (commitment > 0)
    // Miners may check hash instead of commitment, so do not enforce share target check
    // Only use network target to determine block found
    if (cmBig === 0n) {
        stats.invalidShares++;
        return { valid: false, error: 'null commitment' };
    }

    stats.validShares++;
    const minerAddr = creditShare(ctx.worker);   // [PAYOUT] record

    // ============= Add ratio_e9 statistics log =============
    // ratio_e9 = commitment/target * 1e9 (integer approximation), threshold 610e9 means commitment <= 610*target
    let ratioBigIntStr = 'inf';
    let ratioLabel = 'HIGH';
    try {
        if (targetBig > 0n) {
            const ratioTimes1e9 = (cmBig * 1_000_000_000n) / targetBig;
            ratioBigIntStr = ratioTimes1e9.toString();
            const rNum = Number(ratioTimes1e9);
            if (rNum <= 610)       ratioLabel = 'OK';   // Can find block (Cm <= 610*Tgt)
            else if (rNum <= 10000) ratioLabel = 'MID';
            else                    ratioLabel = 'HIGH';
        }
    } catch (_) {}
    // Log every share, quickly collect distribution (max 2 miners, manageable output)
    log('[' + ctx.id + '] share valid#' + stats.validShares +
        ' cm:' + cmBig.toString().slice(0, 12) +
        ' target:' + targetBig.toString().slice(0, 12) +
        ' ratio_e9:' + ratioBigIntStr + ' ' + ratioLabel +
        ' meetNet=' + meetsNetworkTarget + ' hashVer=' + (hashVerified===true?'T':'F'));
    // ============= End log =============

    if (meetsNetworkTarget || hashVerified === true) {
        // === Block found! Build complete block and submit ===
        log('[BLOCK] *** Block found! height=' + currentJob.height + ' nonce=' + nonceHex + ' ***');
        stats.blocksFound++;
        snapshotRound(currentJob.height, currentJob.coinbasevalue);   // [PAYOUT] block snapshot

        try {
            const blockHex = await constructFullBlock(coinbaseBytes, header112, rxHash);
            const submitResult = await rpcCall('submitblock', [blockHex]);
            stats.blocksSubmitted++;
            log('[BLOCK] submitblock result: ' + JSON.stringify(submitResult) + ' (null=success)');
        } catch (e) {
            log('[BLOCK] submitblock failed: ' + e.message);
        }
    }

    return { valid: true, blockFound: meetsNetworkTarget };
}

// ============ Build Complete Block Hex (segwit format) ============
async function constructFullBlock(legacyCoinbaseBytes, header112withZeroHash, rxHashDisplayBE) {
    // hashRandomX: RPC returns display BE, block header needs internal LE (reversed)
    const hashRandomXInternalLE = reverseBuffer(Buffer.from(rxHashDisplayBE, 'hex'));

    // Final header: first 80 bytes + nonce unchanged, hashRandomX filled with reversed value
    const finalHeader = Buffer.concat([
        header112withZeroHash.slice(0, 80),  // version + prevhash + merkle + ntime + nbits + nonce
        hashRandomXInternalLE                 // hashRandomX (internal LE)
    ]);

    // Build segwit coinbase (add marker + flag + witness)
    // Parse parts from legacy coinbase, rebuild segwit format
    const legacyHex = legacyCoinbaseBytes.toString('hex');
    // legacy: version(8) + vin_count(2) + prevout(64+8) + scriptsig_len + scriptsig + sequence(8) + outputs + locktime(8)
    // segwit: version + 00 + 01 + vin_count + ... + outputs + witness + locktime

    // Simplify: insert marker+flag directly after version, insert witness before locktime
    const versionHex = legacyHex.substring(0, 8);  // 4 bytes
    const restAfterVersion = legacyHex.substring(8);

    // Find locktime (last 8 hex chars = 4 bytes)
    const locktimeHex = restAfterVersion.substring(restAfterVersion.length - 8);
    const middleHex = restAfterVersion.substring(0, restAfterVersion.length - 8);

    // witness: 1 item of 32 zero bytes (witness reserved value)
    const witnessHex = '01' + '20' + '00'.repeat(32);

    const segwitCoinbaseHex = versionHex + '0001' + middleHex + witnessHex + locktimeHex;

    // Complete block: header + tx_count + coinbase + other_txs
    const txCountVarint = encodeVarint(1 + currentJob.templateTxs.length);
    let blockHex = finalHeader.toString('hex') + txCountVarint.toString('hex') + segwitCoinbaseHex;
    for (const txData of currentJob.templateTxs) {
        blockHex += txData;
    }


    // [DEBUG] Verify merkle root
    const cbTxid = dsha256(legacyCoinbaseBytes);
    let merkleLevel = [cbTxid];
    for (const branchDisplayBE of currentJob.merkleBranches) {
        merkleLevel.push(Buffer.from(branchDisplayBE, 'hex').reverse());
    }
    while (merkleLevel.length > 1) {
        const next = [];
        for (let j = 0; j < merkleLevel.length; j += 2) {
            const left = merkleLevel[j];
            const right = (j + 1 < merkleLevel.length) ? merkleLevel[j + 1] : merkleLevel[j];
            next.push(dsha256(Buffer.concat([left, right])));
        }
        merkleLevel = next;
    }
    const computedMR = merkleLevel[0];
    const headerMR = header112withZeroHash.slice(36, 68);
    log('[MERKLE DEBUG] header=' + headerMR.toString('hex') + ' computed=' + computedMR.toString('hex') + ' match=' + headerMR.equals(computedMR) + ' branches=' + currentJob.merkleBranches.length);

    return blockHex;
}

// ============ Stratum Protocol Handling ============
function handleMessage(ctx, msg) {
    if (msg.method === 'mining.subscribe') {
        // cpuminer-opt first sends subscribe with params=[UA]; only fall back to params=[] if response has issues.
        // Must respond to first (non-empty params).
        if (ctx.subscribed) {
            log('[' + ctx.id + '] ignoring duplicate subscribe id=' + msg.id);
            return;
        }
        ctx.subscribed = true;
        ctx.en1 = crypto.randomBytes(EXTRA_NONCE1_SIZE).toString('hex');
        log('[' + ctx.id + '] mining.subscribe raw: ' + JSON.stringify(msg));
        send(ctx, {
            id: msg.id,
            result: [[['mining.notify', ctx.en1]], ctx.en1, EXTRA_NONCE2_SIZE],
            error: null
        });
        // Note: do not send set_difficulty immediately, wait until after mining.authorize then send + notify,
        // otherwise miner receives two JSON while processing subscribe response -> parse memory overlap -> heap corruption crash
        log('[' + ctx.id + '] subscribed en1=' + ctx.en1);
        return;
    }

    if (msg.method === 'mining.authorize') {
        ctx.worker = (msg.params && msg.params[0]) || 'anonymous';
        send(ctx, { id: msg.id, result: true, error: null });
        log('[' + ctx.id + '] authorized: ' + ctx.worker);
        // ★ Key fix: set_difficulty sent synchronously immediately + log confirmation, do not wait 50ms
        // Previously setTimeout might bind to old socket, or lost due to process restart
        log('[' + ctx.id + '] -> Immediately send mining.set_difficulty=' + SHARE_DIFFICULTY);
        try {
            send(ctx, { id: null, method: 'mining.set_difficulty', params: [SHARE_DIFFICULTY] });
        } catch (e) {
            log('[' + ctx.id + '] set_difficulty send error: ' + e.message);
        }
        setTimeout(() => {
            sendJob(ctx);
        }, 100);
        return;
    }

    if (msg.method === 'mining.submit') {
        // [FIX 2026-08-03] Flood control: max 1 share per connection per 500ms goes through RPC verification;
        // Excess immediately acknowledged accepted (no RPC consumed, prevent old miner submit storm from overwhelming verification queue)
        const nowMs = Date.now();
        if (ctx.lastShareTime && (nowMs - ctx.lastShareTime) < MIN_SHARE_INTERVAL_MS) {
            send(ctx, { id: msg.id, result: true, error: null });
            return;
        }
        ctx.lastShareTime = nowMs;
        processShare(ctx, msg.params).then(res => {
            send(ctx, { id: msg.id, result: res.valid, error: res.valid ? null : res.error });
            if (res.blockFound) {
                log('[' + ctx.id + '] *** BLOCK FOUND ***');
            }
        }).catch(e => {
            send(ctx, { id: msg.id, result: false, error: e.message });
            log('[' + ctx.id + '] share error: ' + e.message);
        });
        return;
    }

    // Other messages (exonum.subscribe etc.) return OK
    if (msg.id) send(ctx, { id: msg.id, result: true, error: null });
}

// ============ Startup ============
async function main() {
    log('RCPU NOMP Pool starting...');

    // Verify RPC connection
    try {
        const info = await rpcCall('getblockchaininfo');
        log('RPC connected: chain=' + info.chain + ' blocks=' + info.blocks + ' difficulty=' + info.difficulty);
    } catch (e) {
        log('RPC connection failed: ' + e.message);
        process.exit(1);
    }

    // Initialize template
    await updateTemplate();

    // Periodically update template
    setInterval(updateTemplate, TEMPLATE_POLL_MS);

    // Periodically output statistics
    setInterval(() => {
        log('Stats: valid=' + stats.validShares + ' invalid=' + stats.invalidShares +
            ' blocksFound=' + stats.blocksFound + ' blocksSubmitted=' + stats.blocksSubmitted +
            ' rpcErrors=' + stats.rpcErrors + ' miners=' + miners.size);
    }, LOG_STATS_MS);

    // Stratum server
    const server = net.createServer(sock => {
        const id = crypto.randomBytes(3).toString('hex');
        const ctx = { id, sock, en1: null, worker: '' };
        miners.set(id, ctx);
        log('[' + id + '] connected ' + sock.remoteAddress);

        let buf = '';
        sock.on('data', data => {
            // [FIX 2026-08-03] Flood rate limit: max 20 messages per connection per second;
            // Excess silently dropped (no log/no parse/no response), prevent bad miner submit storm from overwhelming event loop
            const nowMs2 = Date.now();
            if (nowMs2 - (ctx.msgWindow || 0) >= 1000) { ctx.msgWindow = nowMs2; ctx.msgCount = 0; }
            ctx.msgCount = (ctx.msgCount || 0) + data.toString('utf8').split('\n').length;
            if (ctx.msgCount > 20) return;
            log('[' + id + '] <<< RAW ' + data.length + 'B: ' + data.toString('utf8').substring(0, 300).replace(/\n/g, '\\n'));
            buf += data.toString();
            let idx;
            while ((idx = buf.indexOf('\n')) >= 0) {
                const line = buf.slice(0, idx).trim();
                buf = buf.slice(idx + 1);
                if (!line) continue;
                try {
                    handleMessage(ctx, JSON.parse(line));
                } catch (e) {
                    log('[' + id + '] parse error: ' + e.message + ' line=' + line.substring(0, 100));
                }
            }
        });
        sock.on('close', () => {
            miners.delete(id);
            log('[' + id + '] disconnected');
        });
        sock.on('error', () => { /* ignore */ });
    });

    server.listen(POOL_PORT, '0.0.0.0', () => {
        log('Pool listening on 0.0.0.0:' + POOL_PORT);
    });

    // Global error handler (prevent crash)
    process.on('uncaughtException', (err) => {
        log('uncaughtException: ' + err.message + '\n' + err.stack);
    });
    process.on('unhandledRejection', (reason) => {
        log('unhandledRejection: ' + reason);
    });
}

main().catch(e => {
    log('Startup failed: ' + e.message);
    process.exit(1);
});

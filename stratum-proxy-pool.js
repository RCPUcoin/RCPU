const net = require('net');
const crypto = require('crypto');
const RandomX = require('randomx.js');
const blake2b = require('blake2b');

const SHARED_PORT = 8080;
const PRIVATE_PORTS = new Map([
    [8081, 'rcpu1q8f7ltdsjh4k3zavgxf64zkukw9s66z82n3th20'],
    [8082, 'rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0']
]);

const RPC_HOST = '127.0.0.1';
const RPC_PORT = 6988;
const MIN_SHARE_DIFFICULTY = 0.000024;
const POOL_FEE = 0;
const PAYOUT_THRESHOLD = 100;

let jobCounter = 0;
let currentJob = null;
let previousJob = null;
const miners = new Map();
const shares = new Map();

let randomxCache = null;
let randomxVM = null;
let blockReward = 500000000000;

const ADDRESS_ALIASES = new Map([
    ["rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0.t3", "rcpu1q8f7ltdsjh4k3zavgxf64zkukw9s66z82n3th20"]
]);

const SCRIPT_PUB_KEY_MAP = new Map([
    ["rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0", "0014f98e12c502de925bbe73f6e7a0d2da2af4f74b48"],
    ["rcpu1q8f7ltdsjh4k3zavgxf64zkukw9s66z82n3th20", "00143a7df5b612bd6d1175883275515b967161ad08ea"]
]);

function resolveAddress(address) {
    return ADDRESS_ALIASES.get(address) || address;
}

function addressToScriptPubKey(address) {
    if (!address) {
        log("Invalid address: null");
        return '76a91400000000000000000000000000000000000000000088ac';
    }
    const lowerAddr = address.toLowerCase();
    if (SCRIPT_PUB_KEY_MAP.has(lowerAddr)) {
        return SCRIPT_PUB_KEY_MAP.get(lowerAddr);
    }
    log("Unknown address, using default: " + address);
    return '76a91400000000000000000000000000000000000000000088ac';
}

async function initRandomX(seedHash) {
    try {
        const seedBuffer = Buffer.from(seedHash, 'hex');
        randomxCache = RandomX.randomx_init_cache(seedBuffer);
        randomxVM = RandomX.randomx_create_vm(randomxCache);
        log("RandomX initialized with seed: " + seedHash.substring(0, 16) + "...");
    } catch (e) {
        log("RandomX initialization error: " + e.message);
    }
}

function hashRandomX(blob) {
    if (!randomxVM) {
        log("RandomX VM not initialized");
        return null;
    }
    try {
        const inputBuffer = Buffer.from(blob, 'hex');
        const result = randomxVM.calculate_hex_hash(inputBuffer);
        return result;
    } catch (e) {
        log("RandomX hash error: " + e.message);
        return null;
    }
}

function calculateCommitment(rxHash, header) {
    const input = Buffer.from(header, 'hex');
    const hashIn = Buffer.from(rxHash, 'hex');
    const output = Buffer.alloc(32);
    blake2b(32, null).update(input).update(hashIn).digest(output);
    return output.toString('hex');
}

function compareHashToTarget(hash, target) {
    const hashBigInt = BigInt('0x' + hash);
    const targetBigInt = BigInt('0x' + target);
    return hashBigInt <= targetBigInt;
}

function targetToDifficulty(target) {
    const maxTarget = BigInt("0x00000000ffff0000000000000000000000000000000000000000000000000000");
    const targetBigInt = BigInt("0x" + target);
    if (targetBigInt === 0n) return 1;
    // Handle fractional difficulties with scaling
    const scale = 1000000000n;
    const result = maxTarget * scale / targetBigInt;
    return Number(result) / 1000000000;
}

function log(msg) {
    console.log("[" + new Date().toISOString().replace('T', ' ').substring(0, 19) + "] " + msg);
}

function reverseHex(hex) {
    return hex.match(/.{2}/g).reverse().join('');
}

function sha256d(data) {
    const hash1 = crypto.createHash('sha256').update(data).digest();
    return crypto.createHash('sha256').update(hash1).digest();
}

function calculateSeedHash(epoch) {
    const seedString = "Scash/RandomX/Epoch/" + epoch;
    const h1 = crypto.createHash('sha256').update(seedString).digest();
    const h2 = crypto.createHash('sha256').update(h1).digest();
    return h2.toString('hex');
}

function varInt(n) {
    if (n < 0xfd) {
        return n.toString(16).padStart(2, '0');
    } else if (n <= 0xffff) {
        return 'fd' + n.toString(16).padStart(4, '0');
    } else {
        return 'fe' + n.toString(16).padStart(8, '0');
    }
}

function constructCoinbase(template, minerAddress, extraNonce1, extraNonce2) {
    const height = template.height;
    const coinbaseValue = template.coinbasevalue || 500000000000;
    
    let heightLEBytes = [];
    let h = height;
    while (h > 0) {
        heightLEBytes.push(h & 0xff);
        h >>= 8;
    }
    if (heightLEBytes.length === 0) {
        heightLEBytes = [0];
    }
    const pushHeightHex = varInt(heightLEBytes.length) + Buffer.from(heightLEBytes).toString('hex');
    
    const xnonce1 = extraNonce1 || '';
    const xnonce2 = extraNonce2 || '00000000';
    const extranonce = xnonce1 + xnonce2;
    
    const scriptSigContent = pushHeightHex + (extraNonce2 || '00000000');
    const scriptSigLen = scriptSigContent.length / 2;
    const scriptSigLenHex = varInt(scriptSigLen);
    const scriptSig = scriptSigLenHex + scriptSigContent;
    
    const scriptPubKey = addressToScriptPubKey(minerAddress);
    
    const valueHex = coinbaseValue.toString(16).padStart(16, '0');
    const valueLE = valueHex.match(/.{2}/g).reverse().join('');
    
    const witnessCommitment = template.default_witness_commitment || '6a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf9';
    
    const txHex = 
        '01000000' +
        '01' +
        '0000000000000000000000000000000000000000000000000000000000000000' +
        'ffffffff' +
        scriptSig +
        'ffffffff' +
        '02' +
        valueLE +
        varInt(scriptPubKey.length / 2) +
        scriptPubKey +
        '0000000000000000' +
        varInt(witnessCommitment.length / 2) +
        witnessCommitment +
        '00000000';
    
    return txHex;
}

function calculateTxId(txHex) {
    const hash1 = crypto.createHash('sha256').update(Buffer.from(txHex, 'hex')).digest();
    return crypto.createHash('sha256').update(hash1).digest().toString('hex');
}

function calculateMerkleRoot(txIds) {
    if (txIds.length === 0) {
        return '00'.repeat(32);
    }
    
    let hashes = txIds.map(id => Buffer.from(id, 'hex'));
    
    while (hashes.length > 1) {
        if (hashes.length % 2 !== 0) {
            hashes.push(hashes[hashes.length - 1]);
        }
        
        const newHashes = [];
        for (let i = 0; i < hashes.length; i += 2) {
            const combined = Buffer.concat([hashes[i], hashes[i + 1]]);
            const hash1 = crypto.createHash('sha256').update(combined).digest();
            newHashes.push(crypto.createHash('sha256').update(hash1).digest());
        }
        hashes = newHashes;
    }
    
    return hashes[0].toString('hex');
}

async function submitBlockToNode(job, nonce, ntime, minerAddress, extraNonce1, extraNonce2) {
    try {
        const addr = minerAddress || 'rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0';
        const xnonce1 = extraNonce1 || '';
        const xnonce2 = extraNonce2 || '00000000';

        const coinbaseTxNoWitness = constructCoinbase(job.template, addr, xnonce1, xnonce2);
        const coinbaseTxId = calculateTxId(coinbaseTxNoWitness);

        log("Coinbase txid: " + coinbaseTxId);
        log("Coinbase scriptSig: " + coinbaseTxNoWitness.substring(64, 64 + (parseInt(coinbaseTxNoWitness.substring(62, 64), 16) * 2 + 2)));

        const txIds = [coinbaseTxId];
        if (job.template.transactions) {
            for (const tx of job.template.transactions) {
                txIds.push(reverseHex(tx.txid));
            }
        }

        const merkleRoot = calculateMerkleRoot(txIds);

        log("Calculated merkle root: " + merkleRoot);
        log("GBT merkle root: " + (job.template.merkleroot || 'N/A'));

        const versionInt = job.template.version || 2;
        const versionBuffer = Buffer.alloc(4);
        versionBuffer.writeUInt32LE(versionInt, 0);
        const version = versionBuffer.toString('hex');
        const prevhash = reverseHex(job.prevhash);
        const merkleRootLE = reverseHex(merkleRoot);

        let ntimeInt;
        if (typeof ntime === 'string' && ntime.match(/^[0-9a-fA-F]+$/)) {
            ntimeInt = parseInt(ntime, 16);
        } else {
            ntimeInt = parseInt(ntime) || job.curtime;
        }

        const ntimeBuffer = Buffer.alloc(4);
        ntimeBuffer.writeUInt32LE(ntimeInt, 0);
        const ntimeLE = ntimeBuffer.toString('hex');

        const nbits = reverseHex(job.nbits);

        const blockHeader = version + prevhash + merkleRootLE + ntimeLE + nbits + nonce;

        const txCount = txIds.length;
        const txCountHex = varInt(txCount);

        const height = job.template.height;
        const coinbaseValue = job.template.coinbasevalue || 500000000000;

        let heightLEBytes = [];
        let h = height;
        while (h > 0) {
            heightLEBytes.push(h & 0xff);
            h >>= 8;
        }
        if (heightLEBytes.length === 0) {
            heightLEBytes = [0];
        }
        const pushHeightHex = varInt(heightLEBytes.length) + Buffer.from(heightLEBytes).toString('hex');

        const extranonce = xnonce1 + xnonce2;
        const scriptSigContent = pushHeightHex + (extraNonce2 || '00000000');
        const scriptSigLen = scriptSigContent.length / 2;
        const scriptSigLenHex = varInt(scriptSigLen);
        const scriptSig = scriptSigLenHex + scriptSigContent;

        const scriptPubKey = addressToScriptPubKey(addr);
        const valueHex = coinbaseValue.toString(16).padStart(16, '0');
        const valueLE = valueHex.match(/.{2}/g).reverse().join('');
        const witnessCommitment = job.template.default_witness_commitment || '6a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf9';

        const coinbaseTxWithWitness = 
            '01000000' +
            '00' +
            '01' +
            '01' +
            '0000000000000000000000000000000000000000000000000000000000000000' +
            'ffffffff' +
            scriptSig +
            'ffffffff' +
            '02' +
            valueLE + varInt(scriptPubKey.length / 2) + scriptPubKey +
            '0000000000000000' + varInt(witnessCommitment.length / 2) + witnessCommitment +
            '01' + '20' + '00'.repeat(32) +
            '00000000';

        let txHex = coinbaseTxWithWitness;
        if (job.template.transactions) {
            for (const tx of job.template.transactions) {
                txHex += tx.data;
            }
        }

        const blockHex = blockHeader + txCountHex + txHex;

        log("Block hex length: " + blockHex.length + " chars");
        log("Block header: " + blockHeader.substring(0, 80));

        const result = await makeRpcRequest('submitblock', [blockHex]);
        log("Block submit result: " + result);

        if (result === null || result === true) {
            log("*** BLOCK ACCEPTED BY NETWORK ***");
            await distributeRewards(job.shareDifficulty);
        } else {
            log("Block rejected: " + result);
        }
    } catch (e) {
        log("Error submitting block: " + e.message);
        log("Stack: " + e.stack);
    }
}
function makeRpcRequest(method, params) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            id: Date.now(),
            jsonrpc: '2.0',
            method: method,
            params: params
        });
        
        const auth = Buffer.from('rcpuuser:rcpupassword').toString('base64');
        
        const options = {
            hostname: RPC_HOST,
            port: RPC_PORT,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data),
                'Authorization': "Basic " + auth
            }
        };
        
        const req = require('http').request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => { body += chunk; });
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(body);
                    if (parsed.error) {
                        reject(new Error(parsed.error.message || 'RPC error'));
                    } else {
                        resolve(parsed.result || parsed);
                    }
                } catch (e) {
                    reject(new Error('Invalid JSON response: ' + body.substring(0, 200)));
                }
            });
        });
        
        req.on('error', (e) => reject(e));
        req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
        req.write(data);
        req.end();
    });
}

async function getBlockTemplate() {
    try {
        const response = await makeRpcRequest("getblocktemplate", [{ rules: ["segwit"] }]);
        if (response) {
            const miningInfo = await makeRpcRequest("getmininginfo", []);
            if (miningInfo && miningInfo.difficulty) {
                response.difficulty = miningInfo.difficulty;
            }
        }
        return response;
    } catch (e) {
        log("getblocktemplate error: " + e.message);
        return null;
    }
}

function bitsToTarget(bits) {
    const exponent = parseInt(bits.substring(0, 2), 16);
    const mantissa = parseInt(bits.substring(2), 16);
    const target = Buffer.alloc(32);
    const shift = (exponent - 3) * 8;
    if (shift >= 0 && shift < 256) {
        target.writeUInt32BE(mantissa, shift >> 3);
    }
    return target.toString('hex');
}

function createRandomXJob(template) {
    jobCounter++;
    const jobId = jobCounter.toString();

    const versionInt = template.version || 2;
    const versionBuffer = Buffer.alloc(4);
    versionBuffer.writeUInt32LE(versionInt, 0);
    const version = versionBuffer.toString('hex');
    const prevhash = reverseHex(template.previousblockhash);
    
    const coinbaseTx = constructCoinbase(template, 'rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0', '', '00000000');
    const coinbaseTxId = calculateTxId(coinbaseTx);
    
    const txIds = [coinbaseTxId];
    if (template.transactions) {
        for (const tx of template.transactions) {
            txIds.push(reverseHex(tx.txid));
        }
    }
    
    const merkleRoot = calculateMerkleRoot(txIds);
    const merkleRootLE = reverseHex(merkleRoot);
    
    const ntime = Buffer.alloc(4);
    ntime.writeUInt32BE(template.curtime, 0);
    const ntimeLE = ntime.toString('hex').match(/.{2}/g).reverse().join('');
    
    const nbits = reverseHex(template.bits);
    const nonce = '00000000';

    const blob = version + prevhash + merkleRootLE + ntimeLE + nbits + nonce;
    
    const epochDuration = template.rx_epoch_duration || 604800;
    const epoch = Math.floor(template.curtime / epochDuration);
    const seedHash = calculateSeedHash(epoch);
    const target = template.target || bitsToTarget(template.bits);
    const networkDifficulty = template.difficulty || targetToDifficulty(target);
    blockReward = template.coinbasevalue || 500000000000;
    
    const shareDifficulty = Math.min(MIN_SHARE_DIFFICULTY, networkDifficulty);
    const shareTarget = calculateTargetFromDifficulty(shareDifficulty);

    return {
        job_id: jobId,
        blob: blob,
        target: target,
        share_target: shareTarget,
        height: template.height || 0,
        seed_hash: seedHash,
        prevhash: template.previousblockhash,
        nbits: template.bits,
        curtime: template.curtime,
        algo: 'rx/0',
        networkDifficulty: networkDifficulty,
        shareDifficulty: shareDifficulty,
        template: template,
        coinbaseValue: blockReward
    };
}

function calculateTargetFromDifficulty(difficulty) {
    const maxTargetBigInt = BigInt('0x00000000ffff0000000000000000000000000000000000000000000000000000');
    // Handle fractional difficulties by scaling (e.g., 0.000024)
    // target = maxTarget / difficulty
    const scale = 1000000000n;
    const difficultyScaled = BigInt(Math.round(difficulty * 1000000000));
    const targetBigInt = maxTargetBigInt * scale / difficultyScaled;
    let targetHex = targetBigInt.toString(16);
    if (targetHex.length > 64) {
        targetHex = 'f'.repeat(64);
    }
    while (targetHex.length < 64) {
        targetHex = '0' + targetHex;
    }
    return targetHex;
}

function createXMRigLoginResponse(id, extraNonce1, job) {
    return JSON.stringify({
        id: id,
        jsonrpc: '2.0',
        result: {
            id: '',
            status: 'OK',
            job: {
                blob: job.blob,
                job_id: job.job_id,
                target: job.target,
                height: job.height,
                seed_hash: job.seed_hash,
                algo: 'rx/0',
                variant: 0
            },
            extra_nonce1: extraNonce1,
            extra_nonce2_size: 4
        }
    }) + '\n';
}

function createXMRigSubmitResponse(id, success) {
    return JSON.stringify({
        id: id,
        jsonrpc: '2.0',
        result: {
            status: success ? 'OK' : 'REJECTED'
        }
    }) + '\n';
}

function createXMRigJobNotify(job, newJob) {
    return JSON.stringify({
        id: null,
        jsonrpc: '2.0',
        method: 'job',
        params: {
            blob: job.blob,
            job_id: job.job_id,
            target: job.target,
            height: job.height,
            seed_hash: job.seed_hash,
            algo: 'rx/0',
            variant: 0,
            new_job: newJob !== undefined ? newJob : true
        }
    }) + '\n';
}

function createStratumSubscribeResponse(id, extraNonce1) {
    const subscriptionId = crypto.randomBytes(8).toString('hex');
    return JSON.stringify({
        id: id,
        result: [
            [
                ['mining.notify', subscriptionId],
                ['mining.set_difficulty', subscriptionId]
            ],
            '',
            4
        ],
        error: null
    }) + '\n';
}

function createStratumAuthorizeResponse(id, success) {
    return JSON.stringify({
        id: id,
        result: success,
        error: null
    }) + '\n';
}

function createStratumSetDifficulty(difficulty) {
    return JSON.stringify({
        id: null,
        method: 'mining.set_difficulty',
        params: [difficulty]
    }) + '\n';
}

function createStratumSubmitResponse(id, success) {
    return JSON.stringify({
        id: id,
        result: success,
        error: success ? null : { code: 20, message: 'stratum reject' }
    }) + '\n';
}

function createStratumJobNotify(job, subscriptionId, cleanJobs) {
    const ntime = Buffer.alloc(4);
    ntime.writeUInt32BE(job.curtime, 0);
    const ntimeHex = ntime.toString('hex');

    const versionHex = '20000000';

    const height = job.height;
    let heightLEBytes = [];
    let h = height;
    while (h > 0) {
        heightLEBytes.push(h & 0xff);
        h >>= 8;
    }
    if (heightLEBytes.length === 0) {
        heightLEBytes = [0];
    }
    const pushHeightHex = varInt(heightLEBytes.length) + Buffer.from(heightLEBytes).toString('hex');

    const scriptSigLen = (pushHeightHex.length / 2) + 4;
    const scriptSigLenHex = varInt(scriptSigLen);

    const coinb1 = '01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff' + scriptSigLenHex + pushHeightHex;

    const scriptPubKey = addressToScriptPubKey('rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0');
    const valueHex = (job.coinbaseValue).toString(16).padStart(16, '0');
    const valueLE = valueHex.match(/.{2}/g).reverse().join('');
    const witnessCommitment = job.template.default_witness_commitment || '6a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf9';

    const coinb2 = 'ffffffff02' + valueLE + varInt(scriptPubKey.length / 2) + scriptPubKey + '0000000000000000' + varInt(witnessCommitment.length / 2) + witnessCommitment + '00000000';

    return JSON.stringify({
        id: null,
        method: 'mining.notify',
        params: [
            job.job_id,
            reverseHex(job.prevhash),
            coinb1,
            coinb2,
            [],
            versionHex,
            job.nbits,
            ntimeHex,
            cleanJobs !== undefined ? cleanJobs : true
        ]
    }) + '\n';
}

function trackShare(address, difficulty) {
    const resolvedAddr = resolveAddress(address);
    if (!shares.has(resolvedAddr)) {
        shares.set(resolvedAddr, { count: 0, balance: 0 });
    }
    const stats = shares.get(resolvedAddr);
    stats.count++;
    log("Share tracked: " + resolvedAddr + " (total: " + stats.count + ")");
}

async function distributeRewards(shareDiff) {
    const totalShares = Array.from(shares.values()).reduce((sum, s) => sum + s.count, 0);
    if (totalShares === 0) {
        log("No shares to distribute rewards");
        return;
    }
    
    const rewardPerShare = (blockReward / 100000000000) * shareDiff / totalShares;
    log("=== DISTRIBUTING REWARDS ===");
    log("Total shares: " + totalShares + ", Reward per share: " + rewardPerShare.toFixed(8) + " RCPU");
    
    for (const [address, stats] of shares) {
        const reward = stats.count * rewardPerShare;
        if (reward >= PAYOUT_THRESHOLD) {
            try {
                log("Payout " + reward.toFixed(8) + " RCPU to " + address);
                await makeRpcRequest('sendtoaddress', [address, reward]);
                stats.balance = 0;
            } catch (e) {
                log("Failed to payout to " + address + ": " + e.message);
                stats.balance += reward;
            }
        } else {
            stats.balance += reward;
            log("Added " + reward.toFixed(8) + " RCPU to " + address + " balance (total: " + stats.balance.toFixed(8) + ")");
        }
        stats.count = 0;
    }
    
    log("=== REWARDS DISTRIBUTED ===");
}

function createServer(port) {
    const server = net.createServer((socket) => {
        const clientId = socket.remoteAddress + ":" + socket.remotePort;

        const minerInfo = {
            socket: socket,
            address: null,
            authorized: false,
            protocol: null,
            currentJobId: null,
            extraNonce1: null,
            subscriptionId: null,
            buffer: '',
            port: port
        };
        miners.set(clientId, minerInfo);

        socket.on('data', async (data) => {
            try {
                minerInfo.buffer += data.toString('utf8');
                const lines = minerInfo.buffer.split('\n');
                
                minerInfo.buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    let msg;
                    try {
                        msg = JSON.parse(line.trim());
                    } catch (e) {
                        continue;
                    }
                    
                    const id = msg.id !== undefined ? msg.id : null;
                    
                    if (!minerInfo.protocol) {
                        if (msg.method === 'login') {
                            minerInfo.protocol = 'xmrig';
                        } else if (msg.method === 'mining.subscribe') {
                            minerInfo.protocol = 'stratum';
                        }
                    }
                    
                    if (minerInfo.protocol === 'xmrig') {
                        if (msg.method === 'login') {
                            let address = msg.params.login || msg.params.user || 'unknown';
                            
                            if (PRIVATE_PORTS.has(port)) {
                                address = PRIVATE_PORTS.get(port);
                                log("Private port " + port + " forced address: " + address);
                            }
                            
                            address = resolveAddress(address);
                            minerInfo.address = address;
                            
                            const template = await getBlockTemplate();
                            if (template) {
                                const extraNonce1 = '';
                                const job = createRandomXJob(template);
                                minerInfo.currentJobId = job.job_id;
                                minerInfo.extraNonce1 = extraNonce1;
                                currentJob = job;
                                
                                socket.write(createXMRigLoginResponse(id, extraNonce1, job));
                                minerInfo.authorized = true;
                                log("XMRig Login OK: " + minerInfo.address + " (port: " + port + ")");
                            }
                        }
                        else if (msg.method === 'submit') {
                            if (!minerInfo.authorized) continue;
                            
                            const jobId = msg.params.job_id;
                            const nonce = msg.params.nonce;
                            const ntime = msg.params.ntime;
                            const submittedHash = msg.params.result;
                            
                            const job = currentJob;
                            if (!job || job.job_id !== jobId) {
                                log("XMRig submit: job not found " + jobId);
                                socket.write(createXMRigSubmitResponse(id, false));
                                continue;
                            }
                            
                            const customCoinbase = constructCoinbase(job.template, minerInfo.address, minerInfo.extraNonce1 || '', '00000000');
                            const customTxId = calculateTxId(customCoinbase);
                            const customTxIds = [customTxId];
                            if (job.template.transactions) {
                                for (const tx of job.template.transactions) {
                                    customTxIds.push(reverseHex(tx.txid));
                                }
                            }
                            const customMerkle = calculateMerkleRoot(customTxIds);
                            const customMerkleLE = reverseHex(customMerkle);

                            const version = job.blob.substring(0, 8);
                            const prevhash = job.blob.substring(8, 72);
                            const ntimeLE = ntime.match(/.{2}/g).reverse().join('');
                            const nbits = job.blob.substring(84, 92);
                            const customBlob = version + prevhash + customMerkleLE + ntimeLE + nbits + nonce;

                            const rxHash = hashRandomX(customBlob);

                            if (!rxHash) {
                                log("XMRig submit: RandomX hash failed, job=" + jobId);
                                socket.write(createXMRigSubmitResponse(id, false));
                                continue;
                            }

                            const header = customBlob;
                            const commitment = calculateCommitment(rxHash, header);

                            const isBlock = compareHashToTarget(commitment, job.target);
                            const isValidShare = compareHashToTarget(commitment, job.share_target);

                            log("XMRig submit: job=" + jobId + ", nonce=" + nonce + ", rx_hash=" + rxHash.substring(0,16) + "..., commitment=" + commitment.substring(0,16) + "...");
                            
                            if (isBlock) {
                                log("*** BLOCK FOUND *** job=" + jobId + ", nonce=" + nonce + ", commitment=" + commitment);
                                submitBlockToNode(job, nonce, ntime, minerInfo.address, minerInfo.extraNonce1, '00000000');
                                socket.write(createXMRigSubmitResponse(id, true));
                            } else if (isValidShare) {
                                trackShare(minerInfo.address, job.shareDifficulty);
                                log("XMRig share accepted: job=" + jobId + ", commitment=" + commitment.substring(0, 16) + "..., diff=" + job.shareDifficulty);
                                socket.write(createXMRigSubmitResponse(id, true));
                            } else {
                                log("XMRig share rejected: commitment too high, job=" + jobId);
                                socket.write(createXMRigSubmitResponse(id, false));
                            }
                        }
                        else if (msg.method === 'keepalived' || msg.method === 'ping') {
                            socket.write(JSON.stringify({ id: id, jsonrpc: '2.0', result: {} }) + '\n');
                        }
                    }
                    else if (minerInfo.protocol === 'stratum') {
                        if (msg.method === 'mining.subscribe') {
                            const extraNonce1 = '';
                            minerInfo.extraNonce1 = extraNonce1;
                            minerInfo.subscriptionId = crypto.randomBytes(8).toString('hex');
                            socket.write(createStratumSubscribeResponse(id, extraNonce1));
                            log("Stratum subscribe OK: " + clientId);
                        }
                        else if (msg.method === 'mining.authorize') {
                            let address = msg.params[0] || 'unknown';

                            if (PRIVATE_PORTS.has(port)) {
                                address = PRIVATE_PORTS.get(port);
                                log("Private port " + port + " forced address: " + address);
                            }

                            address = resolveAddress(address);
                            minerInfo.address = address;
                            minerInfo.authorized = true;
                            socket.write(createStratumAuthorizeResponse(id, true));

                            if (currentJob) {
                                socket.write(createStratumSetDifficulty(currentJob.shareDifficulty));
                                log("Sent mining.set_difficulty: " + currentJob.shareDifficulty + " to " + clientId);
                                socket.write(createStratumJobNotify(currentJob, minerInfo.subscriptionId, true));
                                minerInfo.currentJobId = currentJob.job_id;
                            }
                            log("Stratum authorize OK: " + minerInfo.address + " (port: " + port + ")");
                        }
                        else if (msg.method === 'mining.submit') {
                            if (!minerInfo.authorized) {
                                socket.write(createStratumSubmitResponse(id, false));
                                continue;
                            }
                            const workerName = msg.params[0];
                            const jobId = msg.params[1];
                            const extraNonce2 = msg.params[2];
                            const ntime = msg.params[3];
                            const nonce = msg.params[4];

                            const job = currentJob;
                            const prevJob = previousJob;
                            let activeJob = null;
                            if (job && job.job_id === jobId) {
                                activeJob = job;
                            } else if (prevJob && prevJob.job_id === jobId) {
                                activeJob = prevJob;
                            }
                            if (!activeJob) {
                                log("Stratum submit: job not found " + jobId + " (current=" + (job ? job.job_id : 'null') + ", prev=" + (prevJob ? prevJob.job_id : 'null') + ")");
                                socket.write(createStratumSubmitResponse(id, false));
                                continue;
                            }

                            const customCoinbase = constructCoinbase(activeJob.template, minerInfo.address, minerInfo.extraNonce1 || '', extraNonce2 || '00000000');
                            const customTxId = calculateTxId(customCoinbase);
                            const customTxIds = [customTxId];
                            if (activeJob.template.transactions) {
                                for (const tx of activeJob.template.transactions) {
                                    customTxIds.push(reverseHex(tx.txid));
                                }
                            }
                            const customMerkle = calculateMerkleRoot(customTxIds);
                            const customMerkleLE = reverseHex(customMerkle);

                            const version = activeJob.blob.substring(0, 8);
                            const prevhash = activeJob.blob.substring(8, 72);
                            const ntimeLE = ntime.match(/.{2}/g).reverse().join('');
                            const nbits = activeJob.blob.substring(84, 92);
                            const customBlob = version + prevhash + customMerkleLE + ntimeLE + nbits + nonce;

                            const rxHash = hashRandomX(customBlob);

                            if (!rxHash) {
                                log("Stratum submit: RandomX hash failed, job=" + jobId);
                                socket.write(createStratumSubmitResponse(id, false));
                                continue;
                            }

                            const header = customBlob;
                            const commitment = calculateCommitment(rxHash, header);

                            const isBlock = compareHashToTarget(commitment, activeJob.target);
                            const isValidShare = compareHashToTarget(commitment, activeJob.share_target);

                            log("Stratum submit: job=" + jobId + ", nonce=" + nonce + ", xnonce2=" + extraNonce2 + ", rx_hash=" + rxHash.substring(0,16) + "..., commitment=" + commitment.substring(0,16) + "...");

                            if (isBlock) {
                                log("*** BLOCK FOUND *** job=" + jobId + ", nonce=" + nonce + ", commitment=" + commitment);
                                submitBlockToNode(activeJob, nonce, ntime, minerInfo.address, minerInfo.extraNonce1, extraNonce2);
                                socket.write(createStratumSubmitResponse(id, true));
                            } else if (isValidShare) {
                                trackShare(minerInfo.address, activeJob.shareDifficulty);
                                log("Stratum share accepted: job=" + jobId + ", commitment=" + commitment.substring(0, 16) + "..., diff=" + activeJob.shareDifficulty);
                                socket.write(createStratumSubmitResponse(id, true));
                            } else {
                                log("Stratum share rejected: commitment too high (" + commitment.substring(0, 16) + "...), share_target=" + activeJob.share_target.substring(0, 16) + "..., shareDiff=" + activeJob.shareDifficulty + ", job=" + jobId);
                                socket.write(createStratumSubmitResponse(id, false));
                            }
                        }
                    }
                }
            } catch (e) {
                log("Error from " + clientId + ": " + e.message);
            }
        });

        socket.on('error', (err) => {
            if (err.code !== 'ECONNRESET') {
                log("Socket error from " + clientId + ": " + err.message);
            }
        });

        socket.on('close', () => {
            log("Client disconnected: " + clientId + " (" + minerInfo.protocol + ")");
            miners.delete(clientId);
        });
    });
    
    server.listen(port, () => {
        const isPrivate = PRIVATE_PORTS.has(port);
        const address = isPrivate ? PRIVATE_PORTS.get(port) : 'shared';
        log("RCPU Mining Pool " + (isPrivate ? "Private" : "Shared") + " listening on port " + port + (isPrivate ? " (address: " + address + ")" : ""));
    });
    
    return server;
}

(async () => {
    log("Pool Fee: " + POOL_FEE + "%");
    log("Payout Threshold: " + PAYOUT_THRESHOLD + " RCPU");
    
    createServer(SHARED_PORT);
    
    PRIVATE_PORTS.forEach((address, port) => {
        createServer(port);
    });
    
    const template = await getBlockTemplate();
    if (template) {
        currentJob = createRandomXJob(template);
        log("Initial job: height=" + currentJob.height + ", diff=" + currentJob.networkDifficulty.toFixed(8));
        log("Share difficulty: " + currentJob.shareDifficulty + ", share_target=" + currentJob.share_target.substring(0, 16) + "...");
        log("Network target: " + currentJob.target.substring(0, 16) + "...");
        log("Blob length: " + currentJob.blob.length + " chars");
        await initRandomX(currentJob.seed_hash);
    }
    
    setInterval(async () => {
        log("=== POOL STATUS ===");
        log("Miners connected: " + miners.size);
        log("Shares tracked:");
        shares.forEach((stats, address) => {
            log("  " + address + ": " + stats.count + " shares, " + stats.balance.toFixed(8) + " RCPU");
        });
        log("====================");
    }, 300000);
})();

setInterval(async () => {
    let job = null;
    let difficultyChanged = false;
    let templateChanged = false;

    try {
        const template = await getBlockTemplate();
        if (template) {
            job = createRandomXJob(template);

            templateChanged = !currentJob ||
                currentJob.height !== job.height ||
                currentJob.prevhash !== job.prevhash;

            difficultyChanged = !currentJob ||
                Math.abs((currentJob.shareDifficulty || 0) - job.shareDifficulty) > 1e-9;

            if (templateChanged) {
                if (currentJob && currentJob.seed_hash !== job.seed_hash) {
                    log("Seed hash changed, reinitializing RandomX...");
                    await initRandomX(job.seed_hash);
                }

                previousJob = currentJob;
                currentJob = job;

                log("New job broadcast: " + job.job_id + ", height=" + job.height + ", diff=" + job.networkDifficulty.toFixed(8) + ", shareDiff=" + job.shareDifficulty + ", seed=" + job.seed_hash.substring(0, 16) + "...");
            }
        }
    } catch (e) {
        log("getBlockTemplate error in keepalive: " + e.message);
    }

    if (currentJob) {
        miners.forEach((miner) => {
            if (miner.authorized && miner.socket.writable) {
                try {
                    if (miner.protocol === 'xmrig') {
                        miner.socket.write(createXMRigJobNotify(currentJob, templateChanged));
                        miner.currentJobId = currentJob.job_id;
                    } else if (miner.protocol === 'stratum') {
                        if (difficultyChanged) {
                            miner.socket.write(createStratumSetDifficulty(currentJob.shareDifficulty));
                        }
                        miner.socket.write(createStratumJobNotify(currentJob, miner.subscriptionId, templateChanged));
                        miner.currentJobId = currentJob.job_id;
                    }
                } catch (e) {
                    log("Error sending keepalive to " + miner.socket.remoteAddress + ": " + e.message);
                }
            }
        });
    }
}, 30000);





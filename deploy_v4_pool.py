import paramiko
import base64

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

pool_code = '''const net = require('net');
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
const MIN_SHARE_DIFFICULTY = 1;
const POOL_FEE = 0;
const PAYOUT_THRESHOLD = 100;

let jobCounter = 0;
let currentJob = null;
const miners = new Map();
const shares = new Map();

let randomxCache = null;
let randomxVM = null;
let blockReward = 500000000000;

const ADDRESS_ALIASES = new Map([
    ["rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0.t3", "rcpu1q8f7ltdsjh4k3zavgxf64zkukw9s66z82n3th20"]
]);

function resolveAddress(address) {
    return ADDRESS_ALIASES.get(address) || address;
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
    const maxTarget = BigInt("0xffff000000000000000000000000000000000000000000000000000000000000");
    const targetBigInt = BigInt("0x" + target);
    return Number(targetBigInt / maxTarget);
}

function log(msg) {
    console.log("[" + new Date().toISOString().replace('T', ' ').substring(0, 19) + "] " + msg);
}

function addressToScriptPubKey(address) {
    if (!address || !address.startsWith('rcpu1')) {
        log("Invalid address: " + address);
        return '76a9140000000000000000000000000000000000000000088ac';
    }
    try {
        const addr = address.substring(4);
        const decoded = base58Decode(addr);
        if (decoded.length < 25) {
            throw new Error('Invalid address length');
        }
        const data = decoded.slice(0, -4);
        const hash160 = data.toString('hex');
        return '76a914' + hash160 + '88ac';
    } catch (e) {
        log("Address conversion error: " + e.message);
        return '76a9140000000000000000000000000000000000000000088ac';
    }
}

function base58Decode(input) {
    const ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
    let result = BigInt(0);
    for (let i = 0; i < input.length; i++) {
        const char = input[i];
        const index = ALPHABET.indexOf(char);
        if (index === -1) {
            throw new Error('Invalid base58 character');
        }
        result = result * BigInt(58) + BigInt(index);
    }
    let hex = result.toString(16);
    if (hex.length % 2 !== 0) {
        hex = '0' + hex;
    }
    const buffer = Buffer.from(hex, 'hex');
    const zeroCount = input.split('').filter(c => c === '1').length;
    const zeros = Buffer.alloc(zeroCount, 0);
    return Buffer.concat([zeros, buffer]);
}

function constructCoinbaseTransaction(template, minerAddress, extraNonce1, extraNonce2) {
    const height = template.height;
    const coinbaseValue = template.coinbasevalue || 500000000000;
    
    let heightBytes = [];
    if (height < 0xfd) {
        heightBytes = [height];
    } else if (height <= 0xffff) {
        heightBytes = [0xfd, height & 0xff, (height >> 8) & 0xff];
    } else if (height <= 0xffffffff) {
        heightBytes = [0xfe, height & 0xff, (height >> 8) & 0xff, (height >> 16) & 0xff, (height >> 24) & 0xff];
    }
    
    const heightPushOp = heightBytes.length.toString(16).padStart(2, '0');
    const heightHex = Buffer.from(heightBytes).toString('hex');
    
    const xnonce1 = extraNonce1 || '';
    const xnonce2 = extraNonce2 || '00000000';
    const extranonce = xnonce1 + xnonce2;
    
    const scriptSigLen = 1 + heightBytes.length + extranonce.length / 2;
    let scriptSigLenHex;
    if (scriptSigLen < 0xfd) {
        scriptSigLenHex = scriptSigLen.toString(16).padStart(2, '0');
    } else if (scriptSigLen <= 0xffff) {
        scriptSigLenHex = 'fd' + scriptSigLen.toString(16).padStart(4, '0');
    } else {
        scriptSigLenHex = 'fe' + scriptSigLen.toString(16).padStart(8, '0');
    }
    
    const scriptSig = scriptSigLenHex + heightPushOp + heightHex + extranonce;
    
    const scriptPubKey = addressToScriptPubKey(minerAddress);
    
    const valueHex = (coinbaseValue).toString(16).padStart(16, '0');
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
        (scriptPubKey.length / 2).toString(16).padStart(2, '0') +
        scriptPubKey +
        '0000000000000000' +
        witnessCommitment +
        '00000000';
    
    return txHex;
}

function calculateMerkleRoot(txDataList) {
    if (txDataList.length === 0) {
        return '00'.repeat(32);
    }
    
    let hashes = txDataList.map(tx => {
        const hash1 = crypto.createHash('sha256').update(Buffer.from(tx, 'hex')).digest();
        return crypto.createHash('sha256').update(hash1).digest();
    });
    
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
        
        const coinbaseTx = constructCoinbaseTransaction(job.template, addr, xnonce1, xnonce2);
        
        const txDataList = [coinbaseTx];
        const merkleRoot = calculateMerkleRoot(txDataList);
        
        log("Constructed coinbase tx: " + coinbaseTx.substring(0, 100) + "...");
        log("Coinbase tx length: " + coinbaseTx.length + " chars");
        log("Calculated merkle root: " + merkleRoot);
        log("GBT merkle root: " + (job.template.merkleroot || 'N/A'));
        
        const version = '20000000';
        const prevhash = reverseHex(job.prevhash);
        const merkleRootLE = reverseHex(merkleRoot);
        
        let ntimeInt;
        if (typeof ntime === 'string' && ntime.match(/^[0-9a-fA-F]+$/)) {
            ntimeInt = parseInt(ntime, 16);
        } else {
            ntimeInt = parseInt(ntime) || job.curtime;
        }
        
        const ntimeBuffer = Buffer.alloc(4);
        ntimeBuffer.writeUInt32BE(ntimeInt, 0);
        const ntimeLE = ntimeBuffer.toString('hex').match(/.{2}/g).reverse().join('');
        
        const nbits = reverseHex(job.nbits);
        
        const blockHeader = version + prevhash + merkleRootLE + ntimeLE + nbits + nonce;
        
        log("Block header length: " + blockHeader.length + " chars");
        log("Block header: " + blockHeader.substring(0, 80) + "...");
        
        const txCount = txDataList.length;
        let txCountHex;
        if (txCount < 0xfd) {
            txCountHex = txCount.toString(16).padStart(2, '0');
        } else if (txCount <= 0xffff) {
            txCountHex = 'fd' + txCount.toString(16).padStart(4, '0');
        } else {
            txCountHex = 'fe' + txCount.toString(16).padStart(8, '0');
        }
        
        const witnessMarker = '00';
        const witnessFlag = '01';
        const coinbaseWitnessReserved = '20' + '00'.repeat(32);
        const witnessHex = witnessMarker + witnessFlag + coinbaseWitnessReserved;
        
        let txHex = '';
        for (const tx of txDataList) {
            txHex += tx;
        }
        
        const blockHex = blockHeader + txCountHex + witnessHex + txHex;
        
        log("Total block hex length: " + blockHex.length + " chars (" + blockHex.length / 2 + " bytes)");
        log("Block hex start: " + blockHex.substring(0, 100));
        
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

function reverseHex(hex) {
    return hex.match(/.{2}/g).reverse().join('');
}

function createRandomXJob(template) {
    jobCounter++;
    const jobId = jobCounter.toString();

    const version = '20000000';
    const prevhash = reverseHex(template.previousblockhash);
    
    let merkleRoot = '00'.repeat(32);
    if (template.merkleroot) {
        merkleRoot = reverseHex(template.merkleroot);
    }
    
    const ntime = Buffer.alloc(4);
    ntime.writeUInt32BE(template.curtime, 0);
    const ntimeLE = ntime.toString('hex').match(/.{2}/g).reverse().join('');
    
    const nbits = reverseHex(template.bits);
    const nonce = '00000000';

    const blob = version + prevhash + merkleRoot + ntimeLE + nbits + nonce;
    
    const seedHash = template.previousblockhash;
    const target = template.target || bitsToTarget(template.bits);
    const networkDifficulty = template.difficulty || targetToDifficulty(target);
    blockReward = template.coinbasevalue || 500000000000;
    
    const maxTarget = 'ff'.repeat(32);
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
    const maxTargetBigInt = BigInt('0x' + 'ffff000000000000000000000000000000000000000000000000000000000000');
    const targetBigInt = maxTargetBigInt / BigInt(Math.max(1, difficulty));
    let targetHex = targetBigInt.toString(16);
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
    }) + '\\n';
}

function createXMRigSubmitResponse(id, success) {
    return JSON.stringify({
        id: id,
        jsonrpc: '2.0',
        result: {
            status: success ? 'OK' : 'REJECTED'
        }
    }) + '\\n';
}

function createXMRigJobNotify(job) {
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
            new_job: true
        }
    }) + '\\n';
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
            extraNonce1,
            4
        ],
        error: null
    }) + '\\n';
}

function createStratumAuthorizeResponse(id, success) {
    return JSON.stringify({
        id: id,
        result: success,
        error: null
    }) + '\\n';
}

function createStratumSubmitResponse(id, success) {
    return JSON.stringify({
        id: id,
        result: success,
        error: success ? null : { code: 20, message: 'stratum reject' }
    }) + '\\n';
}

function createStratumJobNotify(job, subscriptionId) {
    const ntime = Buffer.alloc(4);
    ntime.writeUInt32BE(job.curtime, 0);
    const ntimeHex = ntime.toString('hex');
    
    const versionHex = '20000000';
    
    const height = job.height;
    let heightBytes = [];
    if (height < 0xfd) {
        heightBytes = [height];
    } else if (height <= 0xffff) {
        heightBytes = [0xfd, height & 0xff, (height >> 8) & 0xff];
    }
    const heightPushOp = heightBytes.length.toString(16).padStart(2, '0');
    const heightHex = Buffer.from(heightBytes).toString('hex');
    
    const scriptSigLen = 1 + heightBytes.length + 4;
    const scriptSigLenHex = scriptSigLen.toString(16).padStart(2, '0');
    
    const coinb1 = '0100000001000000000000000000000000000000000000000000000000000000000000000ffffffff' + scriptSigLenHex + heightPushOp + heightHex;
    
    const scriptPubKey = addressToScriptPubKey('rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0');
    const valueHex = (job.coinbaseValue).toString(16).padStart(16, '0');
    const valueLE = valueHex.match(/.{2}/g).reverse().join('');
    const witnessCommitment = job.template.default_witness_commitment || '6a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf9';
    
    const coinb2 = 'ffffffff02' + valueLE + (scriptPubKey.length / 2).toString(16).padStart(2, '0') + scriptPubKey + '0000000000000000' + witnessCommitment + '00000000';
    
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
            true
        ]
    }) + '\\n';
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
                const lines = minerInfo.buffer.split('\\n');
                
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
                                const extraNonce1 = crypto.randomBytes(4).toString('hex');
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
                            
                            const isValidShare = compareHashToTarget(submittedHash, job.share_target);
                            const isBlock = compareHashToTarget(submittedHash, job.target);
                            
                            if (isBlock) {
                                log("*** BLOCK FOUND *** job=" + jobId + ", nonce=" + nonce + ", hash=" + submittedHash);
                                submitBlockToNode(job, nonce, ntime, minerInfo.address, minerInfo.extraNonce1, '00000000');
                                socket.write(createXMRigSubmitResponse(id, true));
                            } else if (isValidShare) {
                                trackShare(minerInfo.address, job.shareDifficulty);
                                log("XMRig share accepted: job=" + jobId + ", hash=" + submittedHash.substring(0, 16) + "..., diff=" + job.shareDifficulty);
                                socket.write(createXMRigSubmitResponse(id, true));
                            } else {
                                log("XMRig share rejected: hash too high, job=" + jobId);
                                socket.write(createXMRigSubmitResponse(id, false));
                            }
                        }
                        else if (msg.method === 'keepalived' || msg.method === 'ping') {
                            socket.write(JSON.stringify({ id: id, jsonrpc: '2.0', result: {} }) + '\\n');
                        }
                    }
                    else if (minerInfo.protocol === 'stratum') {
                        if (msg.method === 'mining.subscribe') {
                            const extraNonce1 = crypto.randomBytes(4).toString('hex');
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
                                socket.write(createStratumJobNotify(currentJob, minerInfo.subscriptionId));
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
                            if (!job || job.job_id !== jobId) {
                                log("Stratum submit: job not found " + jobId);
                                socket.write(createStratumSubmitResponse(id, false));
                                continue;
                            }
                            
                            const ntimeLE = ntime.match(/.{2}/g).reverse().join('');
                            const blobWithNonce = job.blob.substring(0, 76) + ntimeLE + job.blob.substring(84, 92) + nonce;
                            
                            const rxHash = hashRandomX(blobWithNonce);
                            
                            if (!rxHash) {
                                log("Stratum submit: RandomX hash failed, job=" + jobId);
                                socket.write(createStratumSubmitResponse(id, false));
                                continue;
                            }
                            
                            const header = blobWithNonce;
                            const commitment = calculateCommitment(rxHash, header);
                            
                            const isBlock = compareHashToTarget(commitment, job.target);
                            const isValidShare = compareHashToTarget(rxHash, job.share_target);
                            
                            log("Stratum submit: job=" + jobId + ", nonce=" + nonce + ", rx_hash=" + rxHash.substring(0,16) + "..., commitment=" + commitment.substring(0,16) + "...");
                            
                            if (isBlock) {
                                log("*** BLOCK FOUND *** job=" + jobId + ", nonce=" + nonce + ", commitment=" + commitment);
                                submitBlockToNode(job, nonce, ntime, minerInfo.address, minerInfo.extraNonce1, extraNonce2);
                                socket.write(createStratumSubmitResponse(id, true));
                            } else if (isValidShare) {
                                trackShare(minerInfo.address, job.shareDifficulty);
                                log("Stratum share accepted: job=" + jobId + ", rx_hash=" + rxHash.substring(0, 16) + "..., diff=" + job.shareDifficulty);
                                socket.write(createStratumSubmitResponse(id, true));
                            } else {
                                log("Stratum share rejected: rx_hash too high (" + rxHash.substring(0, 16) + "...), job=" + jobId);
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
    const template = await getBlockTemplate();
    if (template) {
        const job = createRandomXJob(template);
        
        if (currentJob && currentJob.seed_hash !== job.seed_hash) {
            log("Seed hash changed, reinitializing RandomX...");
            await initRandomX(job.seed_hash);
        }
        
        currentJob = job;
        
        miners.forEach((miner) => {
            if (miner.authorized && miner.socket.writable) {
                try {
                    if (miner.protocol === 'xmrig') {
                        miner.socket.write(createXMRigJobNotify(job));
                    } else if (miner.protocol === 'stratum') {
                        miner.socket.write(createStratumJobNotify(job, miner.subscriptionId));
                    }
                    miner.currentJobId = job.job_id;
                } catch (e) {
                }
            }
        });
        
        log("New job broadcast: " + job.job_id + ", height=" + job.height + ", diff=" + job.networkDifficulty.toFixed(8));
    }
}, 60000);
'''

encoded_code = base64.b64encode(pool_code.encode()).decode()

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=user, password=password, timeout=30)

print("=== 部署V4矿池代码 ===")
print("修复的致命问题:")
print("  1. coinbase增加witness commitment输出（两个输出）")
print("  2. coinb1中scriptSig长度修正为06（1+1+4）")
print("  3. submitBlockToNode使用带witness的区块格式（marker+flag+witness_stack）")
print("  4. submitBlockToNode传入实际矿工地址和extranonce")
print("  5. RandomX blob增加ntime字段（完整80字节）")

stdin, stdout, stderr = ssh.exec_command('echo "' + encoded_code + '" | base64 -d > /root/stratum-proxy-pool.js')
print("\n代码上传完成")

stdin, stdout, stderr = ssh.exec_command('node -c /root/stratum-proxy-pool.js')
result = stderr.read().decode()
if result:
    print("语法错误:")
    print(result)
else:
    print("语法检查通过")

print("\n=== 重启矿池 ===")
stdin, stdout, stderr = ssh.exec_command('killall -9 node 2>/dev/null; sleep 2')
print("旧进程已停止")

stdin, stdout, stderr = ssh.exec_command('cd /root && nohup node stratum-proxy-pool.js > /root/pool.log 2>&1 &')
print("新矿池启动中...")

stdin, stdout, stderr = ssh.exec_command('sleep 5 && tail -20 /root/pool.log')
print("\n启动日志:")
print(stdout.read().decode())

ssh.close()

print("\n" + "="*60)
print("V4矿池部署完成！")
print("关键修复: 完整的SegWit序列化支持")
print("="*60)
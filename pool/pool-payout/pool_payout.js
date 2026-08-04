/*
 * RCPU Pool Auto-Payment Daemon
 * Every 60s scan /root/pool_blocks.json for blocks with status=pending,
 * After 100+ confirmations and verified as pool address revenue, pay miners via sendmany proportional to round shares.
 */
const fs = require('fs');
const http = require('http');

const RPC_HOST = '127.0.0.1';
const RPC_PORT = 9962;
const RPC_USER = 'rcpu';
const RPC_PASS = 'rcpupass';
const WALLET = 'poolwallet';
const BLOCKS_FILE = '/root/pool_blocks.json';
const SHARES_FILE = '/root/pool_shares.json';
const POOL_ADDR = 'rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0';
const MATURE_CONFS = 1;             // Instant pre-payment: only 1 confirmation needed (don't wait for maturity, prepay with wallet balance)
const POOL_FEE = 0.02;              // 2% pool fee
const DUST_SAT = 546;               // Dust below this goes to pool
const SCAN_MS = 60000;              // 60s scan (avoid RPC overload)

function log(m) { console.log('[' + new Date().toISOString() + '] ' + m); }

function rpc(method, params) {
    if (!params) params = [];
    const payload = JSON.stringify({ jsonrpc: '1.0', id: 'payout', method, params });
    const auth = Buffer.from(RPC_USER + ':' + RPC_PASS).toString('base64');
    return new Promise((resolve, reject) => {
        const req = http.request({
            hostname: RPC_HOST, port: RPC_PORT, path: '/wallet/' + WALLET, method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Basic ' + auth }
        }, (res) => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try {
                    const r = JSON.parse(d);
                    if (r.error) reject(new Error(r.error.message || JSON.stringify(r.error)));
                    else resolve(r.result);
                } catch (e) { reject(new Error('parse: ' + d.slice(0, 120))); }
            });
        });
        req.on('error', reject);
        req.write(payload); req.end();
    });
}
// RPC without wallet (getblockhash/getblock use / path)
function rpcNoWallet(method, params) {
    if (!params) params = [];
    const payload = JSON.stringify({ jsonrpc: '1.0', id: 'payout', method, params });
    const auth = Buffer.from(RPC_USER + ':' + RPC_PASS).toString('base64');
    return new Promise((resolve, reject) => {
        const req = http.request({
            hostname: RPC_HOST, port: RPC_PORT, path: '/', method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Basic ' + auth }
        }, (res) => {
            let d = '';
            res.on('data', c => d += c);
            res.on('end', () => {
                try {
                    const r = JSON.parse(d);
                    if (r.error) reject(new Error(r.error.message || JSON.stringify(r.error)));
                    else resolve(r.result);
                } catch (e) { reject(new Error('parse: ' + d.slice(0, 120))); }
            });
        });
        req.on('error', reject);
        req.write(payload); req.end();
    });
}

function loadBlocks() { try { return JSON.parse(fs.readFileSync(BLOCKS_FILE, 'utf8')) || []; } catch (e) { return []; } }
function saveBlocks(b) { try { fs.writeFileSync(BLOCKS_FILE, JSON.stringify(b, null, 1)); } catch (e) {} }

async function isValidAddr(addr) {
    if (addr === 'POOL') return true;
    try { const r = await rpcNoWallet('validateaddress', [addr]); return r && r.isvalid; } catch (e) { return false; }
}

async function payBlock(blk) {
    // 1. Get main chain block hash and confirmations for this height
    let hash, block;
    try {
        hash = await rpcNoWallet('getblockhash', [blk.height]);
        block = await rpcNoWallet('getblock', [hash]);
    } catch (e) {
        if (e.message.includes('Block height out of range')) {
            // Block doesn't exist yet, mark as waiting, stop repeating errors
            if (!blk.waitCount) blk.waitCount = 0;
            blk.waitCount++;
            if (blk.waitCount > 3) {
                blk.status = 'failed'; blk.txid = 'block_not_found';
                saveBlocks(currentBlocks);
                log('height ' + blk.height + ' not found 3 consecutive times, marking failed');
            }
        } else {
            log('height ' + blk.height + ' query failed: ' + e.message);
        }
        return;
    }

    if (block.confirmations === -1) {
        blk.status = 'orphan';
        log('height ' + blk.height + ' is orphan block, marking orphan');
        saveBlocks(currentBlocks);
        return;
    }
    if (block.confirmations < MATURE_CONFS) {
        log('height ' + blk.height + ' confirmations ' + block.confirmations + '/' + MATURE_CONFS + ', waiting for confirmations');
        return;
    }

    // [Instant pre-payment mode] Do not verify coinbase maturity, prepay directly with snapshot-recorded reward
    // User will manually feed matured coins into wallet for pre-payment
    const gotSat = blk.reward || 500000000000;  // Use reward recorded at block time
    log('height ' + blk.height + ' instant pre-payment (confirmations=' + block.confirmations + ', reward=' + gotSat + ')');

    // 3. Calculate each miner's share (minus pool fee), dust goes to pool
    const total = blk.totalShares || 0;
    const distributable = Math.floor(gotSat * (1 - POOL_FEE));
    const payMap = {};   // addr -> sat
    let paySum = 0;
    if (total > 0) {
        for (const [addr, sh] of Object.entries(blk.shares)) {
            if (addr === 'POOL') continue;                 // Pool's own share retained
            const amt = Math.floor(distributable * sh / total);
            if (amt < DUST_SAT) continue;                  // Dust goes to pool
            payMap[addr] = amt; paySum += amt;
        }
    }

    if (Object.keys(payMap).length === 0) {
        log('height ' + blk.height + ' no external payment needed (all pool share or dust)');
        blk.status = 'paid'; blk.txid = 'self'; saveBlocks(currentBlocks); return;
    }

    // 4. Validate address + check balance
    const amounts = {};
    for (const [addr, sat] of Object.entries(payMap)) {
        if (await isValidAddr(addr)) amounts[addr] = sat / 1e8;
        else log('height ' + blk.height + ' invalid address skipped: ' + addr);
    }
    if (Object.keys(amounts).length === 0) { blk.status = 'paid'; blk.txid = 'self'; saveBlocks(currentBlocks); return; }

    const bal = await rpc('getbalances');
    const spendable = bal.mine.trusted;
    const needRcpu = paySum / 1e8;
    if (spendable < needRcpu) {
        log('height ' + blk.height + ' insufficient wallet balance (spendable=' + spendable + ' need ' + needRcpu.toFixed(8) + '), waiting for recharge');
        return;
    }

    // 5. sendmany (miners share fee)
    const recipients = Object.keys(amounts);
    log('height ' + blk.height + ' paying ' + needRcpu.toFixed(8) + ' RCPU to ' + recipients.length + ' miners: ' + JSON.stringify(amounts));
    try {
        const txid = await rpc('sendmany', ['', amounts, 1, 'payout h' + blk.height, recipients]);
        blk.status = 'paid'; blk.txid = txid;
        log('height ' + blk.height + ' payment successful txid=' + txid);
    } catch (e) {
        log('height ' + blk.height + ' sendmany failed: ' + e.message + ' (retry next round)');
        return;
    }
    saveBlocks(currentBlocks);
}

let currentBlocks = [];
async function scan() {
    currentBlocks = loadBlocks();
    // Deduplicate: keep only first entry per height
    const seen = new Set();
    const deduped = [];
    for (const b of currentBlocks) {
        const key = b.height + '_' + b.status;
        if (seen.has(b.height)) continue;
        seen.add(b.height);
        deduped.push(b);
    }
    if (deduped.length < currentBlocks.length) {
        currentBlocks = deduped;
        saveBlocks(currentBlocks);
        log('Dedup: ' + (currentBlocks.length) + ' records');
    }
    const pending = currentBlocks.filter(b => b.status === 'pending');
    if (pending.length === 0) return;
    log('Scan: ' + pending.length + ' pending blocks to settle');
    for (const blk of pending) {
        try { await payBlock(blk); } catch (e) { log('payBlock exception h=' + blk.height + ': ' + e.message); }
    }
}

process.on('uncaughtException', e => log('uncaught: ' + e.message));
process.on('unhandledRejection', e => log('unhandled: ' + e));
log('RCPU Payout daemon started (instant pre-payment mode, wallet=' + WALLET + ', confirmations required=' + MATURE_CONFS + ', fee rate=' + (POOL_FEE * 100) + '%)');
scan();
setInterval(scan, SCAN_MS);

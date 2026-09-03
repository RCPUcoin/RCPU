# RCPU Mining Pool

Complete production mining pool for RCPU (RandomX CPU coin) — extracted from live
server (207.57.129.188). Includes the Stratum pool server, miner source with the
critical byte-order fix, payout scripts, miner binaries, systemd units and all
helper scripts needed to deploy your own pool.

## Repository Layout

```
pool/
├── stratum-pool/                 NOMP-based Stratum pool (Node.js)
│   ├── rcpu-nomp-pool.js         Latest stable v23 (byte-order fix + 2% fee + instant pre-payout)
│   ├── versions/                 Historical pool versions (v7..v23) for reference
│   ├── package.json              Node.js dependencies
│   └── package-lock.json
├── pool-payout/
│   └── pool_payout.js            PPLNS share-tracker + instant pre-payout engine
├── miner-src/
│   ├── cpuminer-opt-3.0.1-src.tar.gz   Full cpuminer-opt source tree (RandomX RCPU)
│   ├── randomx-miner.c           ⚠️ CRITICAL FIX: byte-order of prevhash/version/nbits/ntime
│   └── cpu-miner.c               Share-diff fix
├── miner-bin/
│   ├── minerd-rcpu-linux-x64     Linux x86_64 miner (post byte-order fix)
│   └── minerd-rcpu-linux-x64.old-buggy  For comparison / historical curiosity only
├── config/
│   ├── rcpu.conf.example         rcpud RPC + P2P settings
│   ├── rcpud.service             systemd unit for rcpud
│   ├── rcpu-pool.service         systemd unit for the Stratum pool
│   ├── rcpu-miner.service        systemd unit for local solo-miner
│   └── rcpu.logrotate            Log rotation for rcpud/pool/miner logs
├── logs-api/                     (Optional) share/miner stats API for a website
└── scripts/
    ├── start_pool.sh             Start pool + payout engine
    ├── restart_pool.sh           Restart pool (e.g. after update)
    ├── build_linux_miner.sh      Build cpuminer-opt for Linux
    ├── build_miner.sh            Build miner on the pool host
    ├── build_windows_cross.sh    Cross-compile Windows miner from Linux (MINGW)
    └── keepalive.sh              Keep pool running in foreground under tmux
```

## Quick-Start (deploy your own pool)

### 1. Prerequisites

```bash
# On Debian/Ubuntu 22.04+
sudo apt update
sudo apt install -y git build-essential cmake libboost-all-dev libssl-dev     libevent-dev libminiupnpc-dev libzmq3-dev libdb++-dev pkg-config nodejs npm     python3 python3-pip tmux logrotate
sudo npm install -g n
sudo n 18          # Node.js 18.x required for the pool
```

### 2. Build & start rcpud (RCPU full node)

```bash
git clone https://github.com/RCPUcoin/RCPU
cd RCPU
./autogen.sh && ./configure --without-gui --disable-tests --disable-bench
make -j$(nproc)
sudo make install

mkdir -p ~/.rcpu
cp pool/config/rcpu.conf.example ~/.rcpu/rcpu.conf
# edit rpcuser/rpcpassword in rcpu.conf
sudo cp pool/config/rcpud.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rcpud
# wait for sync ...
```

### 3. Start the Stratum pool

```bash
cd pool/stratum-pool
npm install
# edit rcpu-nomp-pool.js — search for `rpcuser` / `rpcpassword` and match rcpu.conf
# also check `poolAddress` for block rewards, `fee` = 0.02 (2%)

sudo cp ../../pool/config/rcpu-pool.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now rcpu-pool
# Pool listens on 0.0.0.0:3334
```

### 4. Point a miner at it

```bash
# Linux (static binary provided)
./minerd-rcpu-linux-x64 -a randomx -o stratum+tcp://YOUR_POOL_IP:3334     -u RCPU_WALLET_ADDRESS.WORKER -p x -t 4
```

## ⚠️ Critical fixes shipped here

If you ever regenerate the miner from upstream cpuminer-opt, *you must re-apply*
the fixes in `miner-src/randomx-miner.c` otherwise the miner will appear to
submit accepted shares but the pool will NEVER find a block on-chain.

### Miner (randomx-miner.c)

1. **Wrong byte-order for `version` / `prevhash` / `nbits` / `ntime`**
   — the old code used LE/display-BE incorrectly so the RandomX hash was computed
   on a "mirrored" block header. Commit count stayed at 0 even with yay shares.
   Now: `be32enc` for uint32 fields + internal-LE reversed prevhash word order.
2. **Share-diff scaling / 65536** in `cpu-miner.c` (cpuminer-opt stratum_gen_work).
3. **jansson ABI mismatch** — cpuminer-opt ships `-Icompat/jansson` but distros
   ship jansson 2.x. Fix: drop `-Icompat/jansson` so host headers match libjansson.so.

### Pool (rcpu-nomp-pool.js v23)

1. **Correct Bitcoin merkle branches** — `computeMerkleBranches` must pair-wise hash,
   not concat (the old code produced blocks rejected by rcpud with
   `bad-txnmrklroot`).
2. **Rate limiting on the Stratum port** — 20 msgs/conn/sec + 1 share per 500 ms,
   otherwise a flood of broken-submissions from old/buggy miners will wedge the
   event loop.
3. **2% pool fee** — `fee = 0.02` — tweak freely.
4. **Instant pre-payout on block found** — uses *mature* wallet balance so miners
   are paid the same block via PPLNS share weighting, no 100-confirm wait.
5. **rcpud systemd hardened:** OOMScoreAdjust=-500, swapfile enabled, RPC on
   127.0.0.1 only, logrotate active.

## Production checklist from the live server

```
- rcpud runs first, port 9965 P2P / 9962 RPC on 127.0.0.1 only
- pool second, port 3334 Stratum
- optional: local miner last (2 threads, cgroup memory limit ~3GB, RandomX needs 2GB JIT mem)
- 4GB swap ON
- logrotate for *.log in /root
```

## License

MIT — original NOMP parts are MIT, RCPU patches are MIT. Miners follow cpuminer
licenses (GPLv2 where applicable).

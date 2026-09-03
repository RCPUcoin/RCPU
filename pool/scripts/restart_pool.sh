#!/bin/bash
# Kill old processes
pkill -9 -f rcpu-nomp-pool 2>/dev/null
pkill -9 -f minerd-rcpu 2>/dev/null
sleep 3

# Clear logs
> /root/pool.log
> /root/miner.log

# Start pool
cd /root
nohup node rcpu-nomp-pool.js > /root/pool.log 2>&1 &
sleep 5

# Check port
ss -tlnp | grep 3334 && echo "POOL_OK" || echo "POOL_FAIL"

# Start miner
setsid /root/minerd-rcpu -a randomx -o stratum+tcp://127.0.0.1:3334 -u rcpu_miner.w1 -p x --coinbase-addr=rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0 -t 1 > /root/miner.log 2>&1 &
sleep 3
echo "MINER_OK"

# Show logs
echo "=== POOL LOG ==="
tail -8 /root/pool.log
echo "=== MINER LOG ==="
tail -3 /root/miner.log

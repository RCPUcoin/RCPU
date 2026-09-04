# RCPU Node Deployment Guide

This guide provides instructions for deploying RCPU nodes on Linux servers.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Quick Deployment (Binary)](#quick-deployment-binary)
3. [Docker Deployment](#docker-deployment)
4. [Configuration](#configuration)
5. [Network Setup](#network-setup)
6. [Security Best Practices](#security-best-practices)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| OS | Ubuntu 20.04+ / Debian 11+ | Ubuntu 22.04+ / Debian 12+ |
| CPU | 1 core | 2+ cores |
| RAM | 1 GB | 2+ GB |
| Disk | 5 GB SSD | 10+ GB SSD |
| Network | 5 Mbps | 50+ Mbps |

> RCPU launched in February 2024. The blockchain is lightweight (under 1 GB as
> of late 2026) and a full node runs comfortably on the smallest VPS.

### Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y libevent-dev libzmq5 libdb5.3++t64 libminiupnpc17 ca-certificates
```

## Quick Deployment (Binary)

### 1. Download Binaries

```bash
# Download latest release from GitHub
# Asset names change between releases - check the Releases page for the
# exact current filename (pattern: rcpu-core-<version>-linux-x86_64.tar.gz).
# The 'latest/download/' URL below only works when a matching asset is
# attached to the newest release; otherwise open the release page directly.
wget https://github.com/RCPUcoin/RCPU/releases/latest/download/rcpu-core-<VERSION>-linux-x86_64.tar.gz

# Verify checksums and signature
wget https://github.com/RCPUcoin/RCPU/releases/latest/download/SHA256SUMS.txt
wget https://github.com/RCPUcoin/RCPU/releases/latest/download/SHA256SUMS.txt.asc
gpg --import RCPU-DEV-GPG-KEY.asc
gpg --verify SHA256SUMS.txt.asc SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt

# Extract and install (replace with the version you downloaded)
tar xzf rcpu-core-<VERSION>-linux-x86_64.tar.gz
sudo cp rcpu-core-<VERSION>-linux-x86_64/bin/* /usr/local/bin/
sudo chmod +x /usr/local/bin/rcpud /usr/local/bin/rcpu-cli
```

> **Releases page always wins**. Download URLs are stable only when a given
> release carries a matching asset. Point users at
> <https://github.com/RCPUcoin/RCPU/releases> — pick the current tag and its
> attached binaries rather than guessing a filename.

### 2. Create Configuration

```bash
# Create data directory
mkdir -p ~/.rcpu

# Copy and customize config
cp docs/nodes/rcpu.conf.template ~/.rcpu/rcpu.conf
# Edit ~/.rcpu/rcpu.conf
```

### 3. Start the Node

```bash
# Test run
rcpud -chain=rcpu -datadir=~/.rcpu -daemon

# Or with systemd (recommended)
sudo cp docs/nodes/rcpud.service.template /etc/systemd/system/rcpud.service
# Edit the service file with your RPC credentials
sudo systemctl daemon-reload
sudo systemctl enable rcpud
sudo systemctl start rcpud
```

### 4. Verify

```bash
# Check node status
rcpu-cli -chain=rcpu -datadir=~/.rcpu \
  -rpcuser=<USER> -rpcpassword=<PASS> getblockchaininfo

# Expected output:
# {
#   "blocks": 1234,
#   "headers": 1234,
#   "verificationprogress": 0.9998,
#   ...
# }
```

## Docker Deployment

See [docker-deployment.md](docker-deployment.md) for detailed Docker setup instructions.

### Quick Docker Command

```bash
# Build image
docker build -t rcpu-node:latest docs/nodes/

# Run container
docker run -d \
  --name rcpud \
  --restart=always \
  -p 9965:9965 \
  -v /path/to/rcpu-data:/root/.rcpu \
  rcpu-node:latest
```

## Configuration

### Essential Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `chain` | Blockchain name | rcpu |
| `rpcbind` | RPC bind address | **127.0.0.1** |
| `rpcport` | RPC port | 9962 |
| `port` | P2P port | 9965 |
| `rpcuser` | RPC username | - |
| `rpcpassword` | RPC password | - |
| `addnode` | Peer node addresses | - |
| `txindex` | Transaction index | 1 |

### ⚠️ Security Warning

**NEVER** set `rpcbind=0.0.0.0` in production. This exposes your RPC interface to the internet, making your node vulnerable to attacks. Always use `rpcbind=127.0.0.1` and `rpcallowip=127.0.0.1`.

## Network Setup

### Connecting to the RCPU Network

Add peer nodes to your configuration:

```bash
# Temporary (will be lost on restart)
rcpu-cli -chain=rcpu -datadir=~/.rcpu \
  -rpcuser=<USER> -rpcpassword=<PASS> \
  addnode "PEER_IP:9965" "add"

# Permanent (add to rcpu.conf)
# Add line: addnode=PEER_IP:9965
```

### Current Network Peers

Contact the RCPU team for current peer node addresses.

### Firewall Configuration

```bash
# UFW (Ubuntu/Debian)
sudo ufw allow 9965/tcp   # P2P (required)
# DO NOT open 9962 (RPC) to the internet!

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-port=9965/tcp
sudo firewall-cmd --reload
```

## Security Best Practices

### 1. RPC Security

```
✅ DO:  rpcbind=127.0.0.1
✅ DO:  rpcallowip=127.0.0.1
✅ DO:  Use strong RPC credentials
❌ DON'T: rpcbind=0.0.0.0
❌ DON'T: Use simple passwords like "rcpupass"
```

### 2. System Security

- Use SSH key authentication (disable password login)
- Keep system packages updated
- Configure firewall (ufw/firewalld)
- Regularly monitor node status

### 3. Node Security

- Run rcpud under a dedicated user (not root)
- Set up log rotation to prevent disk exhaustion
- Monitor node health with the provided scripts
- Keep the node's blockchain data backed up

### 4. Log Rotation

```bash
# Create log rotation config
sudo tee /etc/logrotate.d/rcpu << 'EOF'
/root/.rcpu/rcpu/debug.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    size 100M
}
EOF
```

## Monitoring

### Node Status Check

```bash
# Quick status
rcpu-cli -chain=rcpu -datadir=~/.rcpu \
  -rpcuser=<USER> -rpcpassword=<PASS> getblockchaininfo

# Peer connections
rcpu-cli -chain=rcpu -datadir=~/.rcpu \
  -rpcuser=<USER> -rpcpassword=<PASS> getconnectioncount

# Peer details
rcpu-cli -chain=rcpu -datadir=~/.rcpu \
  -rpcuser=<USER> -rpcpassword=<PASS> getpeerinfo
```

### Using Monitoring Script

The repository includes a Python monitoring script:

```bash
# Install dependencies
pip install paramiko

# Monitor all nodes (edit hosts in script)
python scripts/monitor_nodes.py
```

## Troubleshooting

### Node Not Syncing

1. Check network connectivity:
   ```bash
   ping google.com
   ```

2. Verify peer connections:
   ```bash
   rcpu-cli ... getconnectioncount
   ```

3. Check logs:
   ```bash
   tail -f ~/.rcpu/rcpu/debug.log
   ```

### RPC Not Responding

1. Verify node is running:
   ```bash
   ps aux | grep rcpud
   ```

2. Check RPC binding:
   ```bash
   ss -tlnp | grep 9962
   # Should show: 127.0.0.1:9962
   ```

3. Test RPC locally:
   ```bash
   curl -X POST http://127.0.0.1:9962 \
     -u "USER:PASS" \
     -d '{"jsonrpc":"1.0","method":"getblockcount"}'
   ```

### Out of Memory

1. Create swap:
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

2. Restart node

### Disk Space Warning

1. Check disk usage:
   ```bash
   df -h
   ```

2. Clean old logs:
   ```bash
   truncate -s 0 ~/.rcpu/rcpu/debug.log
   ```

## Network Connectivity

RCPU nodes discover each other automatically through the **DNS seed
`seed.rcpu.ren`** (mainnet) plus seed addresses compiled into the client
(`vSeeds` in `src/kernel/chainparams.cpp`). For a fresh node this is normally
enough — you do not need to hard-code peers.

For nodes that cannot use DNS (locked-down firewalls, isolated networks),
pin peers by hostname in `rcpu.conf`:

```ini
# rcpu.conf - connect to specific peers (hostname or IP)
addnode=seed.rcpu.ren:9965
addnode=<YOUR_PEER_HOST>:9965
```

> For deployment-specific peer addresses, contact the RCPU team privately.
> Infrastructure node addresses are intentionally **not** published in this
> public repository to keep the network collectively operated and
> discourage targeted scanning.

## Support

- GitHub: https://github.com/RCPUcoin/RCPU
- Website: https://rcpuapp.top
- Pool: https://pool.rcpuapp.top
- Explorer: https://explorer.rcpuapp.top
- Wallet: https://wallet.rcpuapp.top
- Telegram: https://t.me/btc_rcpu

> **Deprecated domains** (still reachable, no longer official): `rcpu.cloud`
> and `rcpupool.asia`. New deployments should use the `rcpuapp.top` set above.

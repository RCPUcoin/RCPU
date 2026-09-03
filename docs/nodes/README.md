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
| OS | Ubuntu 18.04 / Debian 10 | Ubuntu 22.04+ / Debian 12+ |
| CPU | 2 cores | 4+ cores |
| RAM | 2 GB | 4+ GB |
| Disk | 50 GB | 100+ GB SSD |
| Network | 10 Mbps | 100+ Mbps |

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
wget https://github.com/RCPUcoin/RCPU/releases/latest/download/rcpud-linux-x64.gz
wget https://github.com/RCPUcoin/RCPU/releases/latest/download/rcpu-cli-linux-x64.gz

# Verify checksums
wget https://github.com/RCPUcoin/RCPU/releases/latest/download/SHA256SUMS
sha256sum -c SHA256SUMS

# Decompress
gunzip rcpud-linux-x64.gz
gunzip rcpu-cli-linux-x64.gz

# Install
sudo mv rcpud-linux-x64 /usr/local/bin/rcpud
sudo mv rcpu-cli-linux-x64 /usr/local/bin/rcpu-cli
sudo chmod +x /usr/local/bin/rcpud /usr/local/bin/rcpu-cli
```

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

## Network Topology

The RCPU network uses a full-mesh topology with 7 interconnected nodes:

```
Node Types:
  - Mining Pool: 207.57.129.188
  - Wallet Service: 38.147.171.29
  - Blockchain Explorer: 43.159.51.23
  - Main Website: 38.55.199.177
  - Pool Website: 119.28.152.245
  - US Alibaba Cloud: 47.85.38.146
  - Guangzhou Alibaba Cloud: 8.166.130.149
```

For new nodes, configure `addnode` with 3-5 of these peer addresses for optimal connectivity.

## Support

- GitHub: https://github.com/RCPUcoin/RCPU
- Website: https://rcpu.cloud
- Pool: https://rcpupool.asia

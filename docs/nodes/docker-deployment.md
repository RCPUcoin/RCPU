# RCPU Node Docker Deployment Guide

## Prerequisites
- Docker installed
- At least 2GB RAM recommended
- 50GB+ free disk space for blockchain data

## Quick Start

### 1. Pull or Build the Image

```bash
# Option 1: Use pre-built image (when available)
# docker pull rcpcore/rcpu-node:latest

# Option 2: Build from Dockerfile
docker build -t rcpu-node:latest .
```

### 2. Create Configuration

```bash
# Create data directory
mkdir -p /opt/rcpu-data

# Copy template and modify
cp rcpu.conf.template /opt/rcpu-data/rcpu.conf
# Edit /opt/rcpu-data/rcpu.conf with your settings
```

### 3. Run the Container

```bash
docker run -d \
  --name rcpud \
  --restart=always \
  -p 9965:9965 \
  -v /opt/rcpu-data:/root/.rcpu \
  rcpu-node:latest
```

### 4. Verify

```bash
# Check container status
docker ps --filter name=rcpud

# Check node logs
docker logs -f rcpud

# Check sync status
docker exec rcpud rcpu-cli \
  -chain=rcpu \
  -datadir=/root/.rcpu \
  -rpcuser=<YOUR_USERNAME> \
  -rpcpassword=<YOUR_PASSWORD> \
  getblockchaininfo
```

## Network Configuration

To connect to the RCPU network, you need to configure peers:

```bash
docker exec rcpud rcpu-cli \
  -chain=rcpu \
  -datadir=/root/.rcpu \
  -rpcuser=<YOUR_USERNAME> \
  -rpcpassword=<YOUR_PASSWORD> \
  addnode "<PEER_IP>:9965" "add"
```

## Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 9965 | TCP | P2P (must be public) |
| 9962 | TCP | RPC (localhost only) |

## Security Notes

- RPC port (9962) is bound to 127.0.0.1 by default
- Never expose RPC to the internet
- Use strong RPC credentials
- Keep container image updated

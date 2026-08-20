# RCPU Pre-built Binaries

Pre-built binaries are now hosted on [GitHub Releases](https://github.com/RCPUcoin/RCPU/releases).

## Available Downloads

Visit the [latest release page](https://github.com/RCPUcoin/RCPU/releases/latest) to download:

| Package | Platform | Description |
|---------|----------|-------------|
| `rcpu-<version>-linux-x64.tar.gz` | Linux x86_64 | Full package: rcpud, rcpu-cli, rcpu-tx, rcpu-util, rcpu-wallet |
| `rcpu-<version>-win64-wallet.zip` | Windows x86_64 | Windows wallet (GUI + daemon) |
| `One-click-mining-win.zip` | Windows x86_64 | One-click mining package |
| `cpuminer-rcpu-src-<version>.tar.gz` | Source | cpuminer-opt RCPU miner source |
| `RCPU_bluewallet_<date>.apk` | Android | Mobile miner (Bluewallet) |

## Quick Start -- Full Node

```bash
# Download the latest Linux release
wget https://github.com/RCPUcoin/RCPU/releases/latest/download/rcpu-3.0.1-linux-x64.tar.gz
tar -xzf rcpu-3.0.1-linux-x64.tar.gz
cd rcpu-3.0.1

# Create a data directory and config
mkdir -p ~/.rcpu
echo "server=1" > ~/.rcpu/rcpu.conf
echo "rpcuser=youruser" >> ~/.rcpu/rcpu.conf
echo "rpcpassword=yourpassword" >> ~/.rcpu/rcpu.conf

# Start the node (daemon mode)
./rcpud -daemon

# Check sync status
./rcpu-cli getblockchaininfo
```

## Quick Start -- Linux Miner

```bash
# Download cpuminer from releases
# Start mining
./minerd -a randomx \
    -o stratum+tcp://103.74.192.168:3334 \
    -u YOUR_WALLET_ADDRESS.worker1 -p x -t 4
```

## Verify

All release assets include SHA256 checksums in the release notes.

```bash
sha256sum -c SHA256SUMS
```

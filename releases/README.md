# RCPU Pre-built Binaries

All binaries are compiled from source on the production pool server
(103.74.192.168, x86_64). Files are gzip-compressed to fit GitHub's size limits.

## Downloads

| File | Platform | Description | Compressed Size |
|------|----------|-------------|-----------------|
| `minerd-rcpu-linux-x64.gz` | Linux x86_64 | cpuminer-opt RCPU miner (byte-order fix) | ~50 KB |
| `minerd-rcpu-windows-x64.exe.gz` | Windows x86_64 | MINGW cross-compiled, statically linked | ~1.1 MB |
| `rcpud-linux-x64.gz` | Linux x86_64 | RCPU full node daemon | ~88 MB |
| `rcpu-cli-linux-x64.gz` | Linux x86_64 | RCPU RPC client | ~7 MB |
| `rcpu-tx-linux-x64.gz` | Linux x86_64 | RCPU transaction utility | ~15 MB |
| `rcpu-wallet-linux-x64.gz` | Linux x86_64 | RCPU wallet | ~46 MB |
| `xmrig-rcpu-linux-x64.gz` | Linux x86_64 | XMRig RCPU build | ~1.8 MB |

## Verify

```bash
sha256sum -c SHA256SUMS
```

## Quick Start — Linux Miner

```bash
# Download and decompress
wget https://github.com/RCPUcoin/RCPU/raw/main/releases/minerd-rcpu-linux-x64.gz
gunzip minerd-rcpu-linux-x64.gz
chmod +x minerd-rcpu-linux-x64

# Start mining
./minerd-rcpu-linux-x64 -a randomx     -o stratum+tcp://103.74.192.168:3334     -u YOUR_WALLET_ADDRESS.worker1 -p x -t 4
```

## Quick Start — Windows Miner

```bash
# Download and decompress (use 7-Zip or PowerShell)
wget https://github.com/RCPUcoin/RCPU/raw/main/releases/minerd-rcpu-windows-x64.exe.gz

# PowerShell:
Expand-Archive minerd-rcpu-windows-x64.exe.gz

# Or with 7-Zip: right-click -> 7-Zip -> Extract Here

# Then run:
minerd-rcpu-windows-x64.exe -a randomx ^
    -o stratum+tcp://103.74.192.168:3334 ^
    -u YOUR_WALLET_ADDRESS.worker1 -p x -t 4
```

## Build Date
2026-08-13 (latest rebuild with DNS seed and port updates, commit e6ddcf6)

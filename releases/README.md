# RCPU Releases

Official binary releases are published on GitHub Releases:

  **https://github.com/RCPUcoin/RCPU/releases**

This directory contains **release notes and checksum manifests only** - no
pre-compiled binaries are stored in the git repository.

## Download

Go to the [Releases page](https://github.com/RCPUcoin/RCPU/releases) and grab
the files for your platform. Each release includes:

| File | Platform | Description |
|------|----------|-------------|
| `rcpu-core-*-linux-x86_64.tar.gz` | Linux x86_64 | Full node (rcpud, rcpu-cli, rcpu-tx, rcpu-wallet) |
| `rcpu-wallet-*-windows.zip` | Windows x64 | GUI wallet (rcpu-qt) |
| `cpuminer-rcpu-*-linux-x86_64.tar.gz` | Linux x86_64 | CPU miner (RandomX) |
| `cpuminer-rcpu-*-windows.zip` | Windows x64 | CPU miner (RandomX) |
| `One-click-mining-win.zip` | Windows x64 | One-click mining bundle |
| `SHA256SUMS.txt` | - | SHA-256 checksums for all files |
| `SHA256SUMS.txt.asc` | - | GPG detached signature of checksums |
| `RCPU-DEV-GPG-KEY.asc` | - | Signing public key |

## Verification

Always verify downloads before running them:

```bash
# 1. Import the signing key (first time)
gpg --import RCPU-DEV-GPG-KEY.asc

# 2. Verify the checksum file signature
gpg --verify SHA256SUMS.txt.asc SHA256SUMS.txt

# 3. Verify file checksums
sha256sum -c SHA256SUMS.txt
```

The signing key fingerprint is published in the root README and on the
project website for cross-reference.

## Build from source

If you prefer to compile your own binaries, see:

- [Unix build notes](../doc/build-unix.md)
- [Windows build notes](../doc/build-windows.md)
- [macOS build notes](../doc/build-osx.md)

## Mining

Quick start with the official pool:

```bash
# Linux
./cpuminer -a randomx -o stratum+tcp://pool.rcpuapp.top:3333 -u YOUR_ADDRESS -p x
```

```batch
:: Windows (one-click mining)
start-mining.bat
```

See [pool.rcpuapp.top](https://pool.rcpuapp.top) for pool details.

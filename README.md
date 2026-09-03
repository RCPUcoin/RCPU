# RCPU Core

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](COPYING)
[![Release](https://img.shields.io/github/v/release/RCPUcoin/RCPU)](https://github.com/RCPUcoin/RCPU/releases)
[![Explorer](https://img.shields.io/badge/Explorer-explorer.rcpuapp.top-blue)](https://explorer.rcpuapp.top/)
[![Mining Pool](https://img.shields.io/badge/Pool-pool.rcpuapp.top-green)](https://pool.rcpuapp.top/)
[![Wallet](https://img.shields.io/badge/Wallet-wallet.rcpuapp.top-orange)](https://wallet.rcpuapp.top/)
[![Telegram](https://img.shields.io/badge/Telegram-join-blue)](https://t.me/rcpucoin)

RCPU is a CPU-mineable cryptocurrency with **Confidential Transactions (CT)**.
It is forked from Bitcoin Core 27.0, replacing SHA-256 PoW with RandomX for
ASIC resistance, and adding on-chain privacy via Pedersen commitments.

**Clone shallow to save time and bandwidth** — this repo contains full Bitcoin
Core history plus RCPU additions:

```bash
git clone --depth=1 https://github.com/RCPUcoin/RCPU.git
```

---

## Key Features

### Confidential Transactions (CT)

Amounts in RCPU transactions are hidden on-chain using **Pedersen commitments**.
Only the sender and receiver know the transferred amount; miner fees remain
public. CT activates at **block height 8,000**.

- Send confidential transactions with `sendct` RPC
- Based on secp256k1-zkp rangeproof module (from Elements Project)
- Compatible with standard address formats (bech32 `rcpu1...`)

### RandomX Proof-of-Work

RCPU uses **RandomX**, a CPU-optimized mining algorithm that is resistant
to ASIC and GPU mining. Anyone with a modern CPU can mine RCPU.

- ASIC-resistant, CPU-friendly mining
- Fair launch: no pre-mine, no ICO
- 5-minute block time

### ASERT Difficulty Adjustment

Responsive difficulty algorithm based on ASERT (Absolutely Smooth Exponential Rescheduling Targets). Difficulty adjusts every block with a **12-hour half-life**
Response to Timestamps), adapting quickly to hashrate changes while
maintaining stable block times.

---

## Economic Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Ticker** | RCPU | |
| **Genesis block** | 22/Feb/2024 | Independent genesis, not Bitcoin |
| **Block time** | 5 minutes (300 seconds) | |
| **Block reward (start)** | 5,000 RCPU | From height 1 onward |
| **Halving interval** | 210,000 blocks | ~2 years at 5 min/block |
| **Halvings** | 10 times | Subsidy halves each interval |
| **Tail emission** | 1 RCPU per block | After 10 halvings, permanent |
| **MAX_MONEY (consensus)** | 2,100,000,000 RCPU | Upper bound for valid amounts |
| **CT activation** | Height 8,000 | Confidential Transactions fork |
| **ASERT activation** | Height 1,000 | Difficulty algorithm upgrade |
| **Port (mainnet)** | 9965 | P2P network port |
| **RPC port** | 9966 | Default (configurable) |
| **Address prefix** | `rcpu1` | Bech32 |

> **Note:** The genesis block has a reward of 50 RCPU (a Bitcoin Core
> legacy). The actual network subsidy begins at height 1 with 5,000 RCPU
> per block, as defined by `GetBlockSubsidy()`.

---

## Network

### Seed Nodes

- `seed.rcpu.ren` — DNS seed
- Multiple fixed seed nodes operated by the community

### Explorer

- **Mainnet**: [explorer.rcpuapp.top](https://explorer.rcpuapp.top/)

### Mining Pool

- **Official pool**: [pool.rcpuapp.top](https://pool.rcpuapp.top/)

---

## Downloads

Pre-built binaries are available on the
[GitHub Releases page](https://github.com/RCPUcoin/RCPU/releases).

| Component | Windows | Linux |
|-----------|---------|-------|
| Core Wallet (GUI) | ✅ | ✅ |
| rcpud (daemon) | ✅ | ✅ |
| rcpu-cli | ✅ | ✅ |
| CPU Miner | ✅ | ✅ |
| One-Click Mining | ✅ | — |
| Mobile Miner | — | — |

### Verify Downloads

Each release includes `SHA256SUMS` with file checksums:

```bash
sha256sum -c SHA256SUMS
```

---

## Building from Source

See the build documentation:

- [doc/build-unix.md](doc/build-unix.md) — Linux
- [doc/build-windows.md](doc/build-windows.md) — Windows (cross-compile)
- [doc/build-osx.md](doc/build-osx.md) — macOS

### Quick Start (Linux)

```bash
git clone https://github.com/RCPUcoin/RCPU.git
cd RCPU
./autogen.sh
./configure --without-gui --disable-tests --disable-bench
make -j$(nproc)
```

---

## License

RCPU Core is released under the terms of the MIT license. See [COPYING](COPYING)
for more information or see https://opensource.org/licenses/MIT.

RCPU Core is based on Bitcoin Core. Copyright for the upstream code belongs to
the Bitcoin Core developers and other contributors.

---

## Community

- [Telegram](https://t.me/rcpucoin)
- [X / Twitter](https://x.com/rcpucoin)
- [Official Website](https://rcpuapp.top/)

---

## Development

Want to contribute? Great!

- Read the [contributing guidelines](CONTRIBUTING.md)
- Check the [open issues](https://github.com/RCPUcoin/RCPU/issues)
- Submit pull requests against the `main` branch

### Security

If you find a security vulnerability, please report it privately to
**rcpudevs@proton.me**. See [SECURITY.md](SECURITY.md) for details.


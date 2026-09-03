# RCPU Core

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](COPYING)
[![Release](https://img.shields.io/github/v/release/RCPUcoin/RCPU)](https://github.com/RCPUcoin/RCPU/releases)
[![Explorer](https://img.shields.io/badge/Explorer-explorer.rcpuapp.top-blue)](https://explorer.rcpuapp.top/)
[![Mining Pool](https://img.shields.io/badge/Pool-pool.rcpuapp.top-green)](https://pool.rcpuapp.top/)
[![Wallet](https://img.shields.io/badge/Wallet-wallet.rcpuapp.top-orange)](https://wallet.rcpuapp.top/)
[![Telegram](https://img.shields.io/badge/Telegram-join-blue)](https://t.me/RCPUcoin)

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

### Genesis & Launch Timeline

| Event | Date | Details |
|-------|------|---------|
| Genesis block | 22 Feb 2024 | Height 0, 50 RCPU (unspendable origin output) |
| Mining started | Feb 2024 | Height 1 onward, 5,000 RCPU/block |
| CT activation | Height 8,000 | Confidential Transactions fork |
| Source public | Aug 2026 | Repository published on GitHub |

> **Genesis output note**: The genesis coinbase output script reuses the
> Bitcoin genesis public key (04678afd...). This output is unspendable
> by design and the genesis block reward is not part of circulating
> supply. RCPU has an independent genesis hash (2f7b90fa...), not a
> replay of Bitcoin's genesis block.

### ASERT Difficulty Adjustment

Responsive difficulty algorithm based on ASERT (Absolutely Smooth
Exponential Rescheduling Targets). Difficulty adjusts every block with a
**2-day (48-hour) half-life**, adapting to hashrate changes while
maintaining stable block times. ASERT activates at **block height 1,000**
with an anchor block at height 999.

---

## Economic Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| **Ticker** | RCPU | |
| **Genesis block** | 22/Feb/2024 | Independent genesis, not Bitcoin |
| **Block time** | 5 minutes (300 seconds) | |
| **Block reward (start)** | 5,000 RCPU | From height 1 onward |
| **Halving interval** | 210,000 blocks | ~2 years at 5 min/block |
| **Halvings** | ~10 times | Then permanent tail emission of 1 RCPU/block |
| **Tail emission** | 1 RCPU per block | After 10 halvings, permanent |
| **MAX_MONEY** | 2,100,000,000 RCPU | Per-output sanity check (consensus critical), NOT a total supply cap |
| **CT activation** | Height 8,000 | Confidential Transactions fork |
| **ASERT activation** | Height 1,000 | Difficulty algorithm upgrade |
| **Port (mainnet)** | 9965 | P2P network port |
| **RPC port** | 9962 | Default (configurable) |
| **Address prefix** | `rcpu` | Bech32 HRP (`rcpu1...`) |

> **Single source of truth**: `doc/consensus-params.md` lists every
> consensus-critical value above and cross-references the source
> location (`src/kernel/chainparams.cpp`, `src/validation.cpp`). If a
> number here ever disagrees with that table, the table (and the code)
> wins.

> **Supply model note**: RCPU is not a strictly capped-supply coin.
> - Genesis block (height 0): 50 RCPU reward (not spendable - historical origin)
> - Height 1 onwards: 5,000 RCPU base subsidy per block
> - Subsidy halves every 210,000 blocks (~2 years)
> - After ~10 halvings: permanent **tail emission** of 1 RCPU per block
> - `MAX_MONEY` (2.1B) is a per-transaction-output sanity check for
>   consensus safety - it is **not** a hard cap on total supply.

---

## Network

### Seed Nodes

- `seed.rcpu.ren` — official DNS seed (operated by RCPU team)
- Additional seed addresses ship compiled into the client (`vSeeds` in
  `src/kernel/chainparams.cpp`) and are refreshed on first start, so you
  normally do **not** need to configure peers manually.

> To pin a specific peer, add `addnode=<host>:9965` to `rcpu.conf`.
> The RCPU team operates `seed.rcpu.ren`; community DNS seeds are welcome —
> submit a PR adding your hostname to `vSeeds`
> in `src/kernel/chainparams.cpp`.

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

### Verify Downloads

Each release includes `SHA256SUMS` with file checksums. Releases are
signed with the RCPU GPG key.

**Signing key fingerprint**: `934D 5BC9 5DD4 B3AC FEF5 21B9 5476 3350 1FE4 B8EE`
(RCPU Dev Team <rcpudevs@proton.me>)

The public key is committed to the repo at `RCPU-DEV-GPG-KEY.asc` and also
published on the [Releases](https://github.com/RCPUcoin/RCPU/releases) page.

```bash
# Import the RCPU signing key
gpg --import RCPU-DEV-GPG-KEY.asc

# Verify checksums
sha256sum -c SHA256SUMS

# Verify signature
gpg --verify SHA256SUMS.asc
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

- [Telegram](https://t.me/RCPUcoin)
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


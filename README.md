# RCPU

RCPU is an independent public blockchain (cryptocurrency) forked from Bitcoin Core 27.0,
using the [RandomX](https://github.com/tevador/RandomX) proof-of-work algorithm. It aims
to achieve fairer, more decentralized block production and token distribution through
ASIC-resistant, CPU-friendly mining.

- Official repository: https://github.com/RCPUcoin/RCPU
- Block explorer / community: see the "Links" section below

---

## What is RCPU?

RCPU is an independent PoW public blockchain. It inherits Bitcoin Core's battle-tested
consensus core, P2P network, transaction and wallet implementations, while replacing the
proof-of-work algorithm with RandomX and introducing an independent genesis block, chain
parameters, and network magic — forming a new chain fully isolated from Bitcoin.

RCPU nodes download and fully validate blocks and transactions, and can optionally build
a graphical wallet interface.

See the [doc directory](/doc) for more technical details.

---

## Key Differences from Bitcoin Core

| Dimension | Bitcoin Core | RCPU |
|-----------|--------------|------|
| Consensus algorithm | SHA-256 (ASIC-dominated) | RandomX (ASIC-resistant, CPU-friendly) |
| Block interval | ~10 minutes | 5 minutes |
| Halving cycle | 210000 blocks | 210000 blocks (~2 years) |
| Network magic | `0xf9beb4d9` | `RCPU` (`0x52504355`) |
| Mainnet port | 8333 | 9965 |
| bech32 prefix | `bc` | `rcpu` (mainnet) |
| Chain type | MAIN/TESTNET/REGTEST/SIGNET | RCPUMAIN/RCPUTESTNET/RCPUREGTEST |

---

## Get the Source

The repository history contains pre-built binaries, so a full clone can be large.
For a quick checkout of the latest code, use a shallow clone (downloads only the
latest snapshot, without historical binaries):

```bash
git clone --depth 1 https://github.com/RCPUcoin/RCPU.git
```

To fetch the full history later: `git fetch --unshallow`.

---

## Quick Start

### Build

Dependencies and build steps are essentially the same as Bitcoin Core. Refer to:

- [doc/build-unix.md](doc/build-unix.md) — Linux / macOS
- [doc/build-windows.md](doc/build-windows.md) — Windows
- [doc/build-android.md](doc/build-android.md) — Android (optional)

Common flow (Linux):

```bash
./autogen.sh
./configure
make -j$(nproc)
```

Build artifacts:

| Command | Description |
|---------|-------------|
| `rcpud` | RCPU node daemon |
| `rcpu-cli` | RPC command-line client |
| `rcpu-tx` | Transaction utility |
| `rcpu-wallet` | Wallet tool |
| `rcpu-qt` | Graphical wallet (optional) |

### Run a Node

```bash
# Start the node (mainnet)
./src/rcpud -daemon

# Check chain status
./src/rcpu-cli getblockchaininfo
```

---

## Links

- Source: https://github.com/RCPUcoin/RCPU
- Block explorer: https://rcpupool.site/
- Community (Telegram): https://t.me/btc_rcpu
- Community (X/Twitter): https://x.com/rcpumm
- Issues: https://github.com/RCPUcoin/RCPU/issues
- License: MIT (see [COPYING](COPYING))

---

## Development Workflow

The main branch is built (see `doc/build-*.md`) and tested regularly, but is not
guaranteed to be fully stable. Please contribute by submitting issues and pull requests
on GitHub.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution process and
[doc/developer-notes.md](doc/developer-notes.md) for development tips.

## Testing

Developers are encouraged to write unit tests for new code. To run:

```bash
make check
```

There are also Python-based regression and integration tests in [test/](test/):

```bash
test/functional/test_runner.py
```

CI automatically builds and runs unit and sanitizer tests on Windows / Linux / macOS
for every pull request.

## License

RCPU is released under the MIT license. See [COPYING](COPYING) or
https://opensource.org/licenses/MIT.

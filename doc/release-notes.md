RCPU version 2.0.0 is now available from:

  <https://github.com/RCPUcoin/RCPU/releases>

RCPU is an independent public blockchain forked from Bitcoin Core 27.0, using
the RandomX proof-of-work algorithm.

This release introduces RCPU as an independent chain with:

- RandomX proof-of-work (ASIC-resistant, CPU-friendly mining)
- An independent genesis block, chain parameters, and network magic
- 5-minute block interval
- Mainnet default port 9965
- `rcpu` bech32 address prefix on mainnet

Please report bugs using the issue tracker at GitHub:

  <https://github.com/RCPUcoin/RCPU/issues>

How to Upgrade
==============

If you are running an older version, shut it down. Wait until it has completely
shut down (which might take a few minutes in some cases), then run the
installer (on Windows) or just copy over the new `rcpud`/`rcpu-qt` binaries
(on Linux/macOS).

Compatibility
==============

RCPU is supported and tested on operating systems using the Linux Kernel 3.17+,
macOS 11.0+, and Windows 7 and newer. RCPU should also work on most other Unix-like
systems but is not frequently tested on them.

Notable Changes
===============

Binaries
--------

RCPU binaries are named:

- `rcpud` — node daemon
- `rcpu-cli` — RPC command-line client
- `rcpu-tx` — transaction utility
- `rcpu-util` — utility tool
- `rcpu-wallet` — wallet tool
- `rcpu-qt` — graphical wallet (optional)

RandomX Proof-of-Work
---------------------

RCPU replaces Bitcoin Core's SHA-256 proof-of-work with RandomX, a
CPU-friendly, ASIC-resistant algorithm. See the
[RandomX project](https://github.com/tevador/RandomX) for details.

Building from Source
====================

Build dependencies and steps are essentially the same as Bitcoin Core. See:

- `doc/build-unix.md` — Linux / macOS
- `doc/build-windows.md` — Windows
- `doc/build-android.md` — Android (optional)

Credits
=======

RCPU is based on [Bitcoin Core](https://github.com/bitcoin/bitcoin), and
gratefully acknowledges the Bitcoin Core developers. See `COPYING` for license
details.

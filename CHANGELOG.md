# Changelog

All notable changes to the RCPU project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- PR and Issue templates for standardized contribution workflow
- Branch protection rules (PR review required, linear history)

### Changed
- CI workflow adapted for RCPU branding
- .gitignore expanded for RCPU build artifacts

## [3.0.1] - 2026-08-13

### Added
- Pre-built Linux binaries (rcpud, rcpu-cli, rcpu-tx, rcpu-util, rcpu-wallet)
- Pre-built Windows wallet (rcpu-3.0.1-win64-wallet.zip)
- One-click mining package for Windows
- cpuminer source code (3.0.9)
- Mobile miner for Android (Bluewallet)

### Fixed
- Fixed pow_tests ChainParams sanity check for RCPU
- Fixed RandomX seed hash test
- Fixed util_ParseMoney MAX_MONEY boundary for RCPU

### Changed
- Rebuilt Linux binaries with test fixes
- Added rcpu-util binary to release package

## [3.0.0] - 2026-08

### Added
- Initial RCPU mainnet release
- RandomX proof-of-work algorithm (ASIC-resistant, CPU-friendly)
- 5-minute block interval
- RCPU bech32 address prefix (rcpu1...)
- RCPU network magic (0x52504355)
- Mainnet port 9965
- RCPUMAIN / RCPUTESTNET / RCPUREGTEST chain types
- Desktop wallet (Windows/Linux)
- CPU miner (cpuminer-opt)
- XMRig miner support
- Mobile miner (Android)

### Changed
- Forked from Bitcoin Core 27.0
- Rebranded all binaries: rcpud, rcpu-cli, rcpu-tx, rcpu-util, rcpu-wallet, rcpu-qt
- Data directory and configuration files use cpu naming
- Independent genesis block and chain parameters

[Unreleased]: https://github.com/RCPUcoin/RCPU/compare/v3.0.1...HEAD
[3.0.1]: https://github.com/RCPUcoin/RCPU/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/RCPUcoin/RCPU/releases/tag/v3.0.0-linux-miner
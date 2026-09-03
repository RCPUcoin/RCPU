# Changelog

All notable changes to RCPU Core will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-09-03

### Added

- **Confidential Transactions (CT)** - Full CT support with Pedersen commitments
  - CT activates at block height 8,000
  - `sendct` RPC command for confidential transactions
  - `createrawcttransaction` RPC for raw CT transactions
  - Wallet support for CT outputs (blinding, unblinding)
  - secp256k1-zkp rangeproof module integration
  - CT-specific consensus validation rules
  - `confidential.h` / `confidential.cpp` primitives library

- **ASERT Difficulty Adjustment**
  - ASERT activates at block height 1,000
  - Responsive difficulty algorithm based on timestamp anchoring
  - 2-day half-life for smooth adjustments

### Changed

- RCPU client version bumped to 3.1.0 (from 2.0.0)
- Copyright year updated to 2026
- Project URLs updated to github.com/RCPUcoin/RCPU
- `amount.h` include guard renamed to `RCPU_CONSENSUS_AMOUNT_H`
- README comprehensively rewritten with CT features and economic parameters
- `doc/README.md` rewritten for RCPU (was Bitcoin template)
- Build documentation clone URLs updated to RCPU repository

### Removed

- Removed `SECURITY-SCASH.md` (legacy from SCASH fork era)
- Removed legacy CI workflow configurations
- Removed pre-built binaries from `releases/` directory (use GitHub Releases)
- Removed miner source tarball from repo (use GitHub Releases)
- Moved operational scripts from root to `contrib/admin/`

### Security

- Security contact updated to rcpudevs@proton.me
- Added `SECURITY.md` with vulnerability disclosure policy

## [3.0.1] - 2026-08-20

### Added

- Brand rename from SCASH to RCPU
- RandomX Proof-of-Work algorithm
- Independent genesis block and chain parameters
- RCPU bech32 address prefix (`rcpu1...`)
- Chain network IDs: RCPUMAIN / RCPUTESTNET / RCPUREGTEST
- 5-minute block time
- Updated test vectors for RCPU (bech32, magic bytes, RandomX)

### Changed

- Forked from Bitcoin Core 27.0
- Replaced SHA-256 PoW with RandomX (ASIC-resistant, CPU-friendly)
- Port numbers changed (9965 mainnet, 19965 testnet)
- Qt wallet renamed from Bitcoin-Qt to RCPU-Qt
- macOS Info.plist updated with RCPU branding
- MSVC project files renamed to RCPU naming

### Fixed

- SegWit test vectors updated to use RCPU bech32 HRP
- ASERT unit tests fixed for self-consistency
- Various test vector corrections for new chain parameters

## [2.0.0] - 2024-02-22

- Genesis block created
- Initial launch of RCPU (then known as SCASH)
- SHA-256 PoW (later replaced with RandomX)

---

## About Version Numbers

RCPU Core uses a hybrid version scheme:

- **RCPU client version**: `3.1.0` (project-specific version)
- **Upstream base**: `Bitcoin Core 27.0.0`
- **Full version string**: `3.1.0-narnia-core-27.0.0`

The `narnia` release codename refers to the current development series.


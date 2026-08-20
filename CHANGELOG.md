# Changelog

All notable changes to the RCPU project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- RandomX proof-of-work algorithm (ASIC-resistant, CPU-friendly mining)
- Independent genesis block, chain parameters, and network magic
- RCPUMAIN / RCPUTESTNET / RCPUREGTEST chain types
- `rcpu` bech32 prefix on mainnet

### Changed

- Block interval reduced from ~10 minutes to 5 minutes
- Mainnet default port changed to 9965
- Data directory and configuration files use `rcpu` naming

### Security

- Rebranded binaries: `rcpud`, `rcpu-cli`, `rcpu-tx`, `rcpu-util`,
  `rcpu-wallet`, `rcpu-qt`

## [2.0.0] - 2024

- Initial RCPU release, forked from Bitcoin Core 27.0

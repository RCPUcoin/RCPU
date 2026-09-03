# RCPU Consensus Parameters

This is the **single source of truth** for consensus-critical RCPU values.
Other docs (README, node deployment guide, release notes) reference this table;
if a number elsewhere disagrees with what is listed here, **the code and this
table win**.

All mainnet values below are verified against the current source:

| Parameter | Mainnet value | Source reference |
|-----------|---------------|------------------|
| Chain name (CLI) | `-chain=rcpu` / `-rcpu` | `src/chainparamsbase.cpp` (`ChainType::RCPUMAIN`) |
| Data directory | `~/.rcpu` | client default |
| Config file | `rcpu.conf` | `src/common/args.cpp` (`BITCOIN_CONF_FILENAME`) |
| P2P port | **9965** (testnet 19965) | `src/kernel/chainparams.cpp` (`nDefaultPort`) |
| RPC port | **9962** (testnet 19962) | `src/chainparamsbase.cpp` (`CreateBaseChainParams`) |
| Block time | 5 minutes (300 s) | `src/kernel/chainparams.cpp` (`nPowTargetSpacing`) |
| Block reward (start) | 5,000 RCPU | `src/validation.cpp` (`GetBlockSubsidy`) |
| Halving interval | 210,000 blocks | `src/kernel/chainparams.cpp` (`nSubsidyHalvingInterval`) |
| Block subsidy formula | `5000 >> (height / 210000)` | `src/validation.cpp` `GetBlockSubsidy` |
| Long-term tail target | 1 RCPU/block (projected, after ~10 halvings) | README economics; not yet a consensus floor |
| MAX_MONEY (per-output sanity) | 2,100,000,000 RCPU | `src/consensus/amount.h` |
| CT activation height | **8,000** (testnet: always) | `src/kernel/chainparams.cpp` (`nCTActivationHeight`) |
| ASERT activation height | **1,000** (testnet 301) | `src/kernel/chainparams.cpp` (`nASERTActivationHeight`) |
| ASERT anchor block | 999 (testnet 280) | `src/kernel/chainparams.cpp` (`asertAnchorParams`) |
| ASERT half-life | **2 days (172,800 s)** | `src/kernel/chainparams.cpp` (`nASERTHalfLife`) |
| PoW algorithm | RandomX | `src/kernel/chainparams.cpp` (`fPowRandomX`) |
| RandomX epoch | 7 days | `src/kernel/chainparams.cpp` (`nRandomXEpochDuration`) |
| Message start (magic) | `R C P U` (0x52 0x43 0x50 0x55) | `src/kernel/chainparams.cpp` (`pchMessageStart`) |
| Bech32 HRP | `rcpu` (`rcpu1...`) | `src/kernel/chainparams.cpp` (`bech32_hrp`) |
| Base58 prefix (legacy) | 0 / 5 / 128 | `src/kernel/chainparams.cpp` (`base58Prefixes`) |

## Chain rollback context (v3.1.1)

A PoW-verification bypass was removed in v3.1.1 and the mainnet chain was rolled
**back to block height 8,743** to drop blocks mined under the flawed
`CheckProofOfWorkRandomX`. Any node built from the pre-fix source will be on a
divergent chain; always run the latest release and expect a one-time reindex on
upgrade.

## Notes on "consensus-critical" vs "economic"

- `MAX_MONEY` (2.1B) is a **per-output sanity check**, not a total-supply cap.
- The 1 RCPU/block tail emission is the long-term economic target stated in the
  README; the consensus subsidy formula is the halving curve in `GetBlockSubsidy`.
- Ports, data-dir and config-file are network/CLI defaults, not consensus rules,
  but are listed here so every doc agrees on one set of numbers.
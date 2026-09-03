# RCPU Releases

Pre-built binaries for RCPU are available on the
[**GitHub Releases page**](https://github.com/RCPUcoin/RCPU/releases).

> **Note:** Binary files are not stored in this git repository.
> They are distributed exclusively via GitHub Releases to keep the
> repository lean and fast to clone.

## Available downloads

| Component | Description |
|-----------|-------------|
| **Core Wallet** | Full node with GUI wallet (Windows & Linux) |
| **CLI Tools** | `rcpud`, `rcpu-cli`, `rcpu-tx` (command line) |
| **CPU Miner** | `cpuminer-rcpu` (Windows & Linux) |
| **One-Click Mining** | Easy mining setup for Windows |
| **Mobile Miner** | Android mining app |

## Verifying downloads

SHA256 checksums are provided with each release.
To verify:

```bash
sha256sum -c SHA256SUMS
```

## Building from source

See the build documentation in the [`doc/`](../doc/) directory:
- `doc/build-unix.md` - Linux build instructions
- `doc/build-windows.md` - Windows (cross-compile) instructions
- `doc/build-osx.md` - macOS build instructions


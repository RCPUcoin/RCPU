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

All release files are signed with the RCPU Dev Team GPG key.

### 1. Import the signing key

```bash
# Download the public key from the release page
wget https://github.com/RCPUcoin/RCPU/releases/download/v3.1.0/RCPU-DEV-GPG-KEY.asc

# Import it
gpg --import RCPU-DEV-GPG-KEY.asc
```

Key fingerprint:
```
934D 5BC9 5DD4 B3AC FEF5  21B9 5476 3350 1FE4 B8EE
```

### 2. Verify checksums signature

```bash
gpg --verify SHA256SUMS.txt.asc SHA256SUMS.txt
```

You should see:
```
Good signature from "RCPU Dev Team <rcpudevs@proton.me>"
```

### 3. Verify file checksums

```bash
sha256sum -c SHA256SUMS.txt
```

## Building from source

See the build documentation in the [`doc/`](../doc/) directory:
- `doc/build-unix.md` - Linux build instructions
- `doc/build-windows.md` - Windows (cross-compile) instructions
- `doc/build-osx.md` - macOS build instructions

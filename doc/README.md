RCPU Core
=============

RCPU is an experimental digital currency that enables instant payments to
anyone, anywhere in the world. RCPU uses peer-to-peer technology to operate
with no central authority: managing transactions and issuing money are carried
out collectively by the network. RCPU Core is the name of open source
software which enables the use of this currency.

For more information, as well as an immediately usable binary version of
RCPU Core, see the [RCPU website](https://rcpuapp.top/) and the
[GitHub Releases page](https://github.com/RCPUcoin/RCPU/releases).

## License

RCPU Core is released under the terms of the MIT license. See [COPYING](COPYING) for more
information or see https://opensource.org/licenses/MIT.

## Development Process

The `master` branch is regularly built (see `doc/build-*.md` for instructions) and tested, but it is not guaranteed to be
completely stable. [Tags](https://github.com/RCPUcoin/RCPU/tags) are created
regularly from release branches to indicate new official, stable release versions of RCPU Core.

The contribution workflow is described in [CONTRIBUTING.md](CONTRIBUTING.md)
and useful hints for developers can be found in [doc/developer-notes.md](doc/developer-notes.md).

## Testing

Testing and code review is the bottleneck for development; we get more pull
requests than we can review and test on short notice. Please be patient and help out by testing
other people's pull requests, and remember this is a security-critical project where any mistake might cost people
lots of money.

### Automated Testing

Developers are strongly encouraged to write [unit tests](src/test/README.md) for new code, and to
submit new unit tests for old code. Unit tests can be compiled and run
(assuming they weren't disabled in configure) with: `make check`. Further details on running
and extending unit tests can be found in [/src/test/README.md](/src/test/README.md).

There are also [regression and integration tests](/test), written
in Python.
These tests are run regularly by CI.

### Manual Quality Assurance (QA) Testing

Changes should be tested by somebody other than the developer who wrote the
code. This is especially important for large or high-risk changes. It is useful
to add a test plan to the pull request description if testing the changes is
not straightforward.

## Translations

Changes to translations as well as new translations can be submitted via pull request.

Translations are periodically pulled from the translation platform and merged
into the git repository. **Important**: We do not accept translation changes as
GitHub pull requests because the next pull from the translation platform would
automatically overwrite them again.

## Notable Features

- **RandomX PoW**: CPU-friendly mining algorithm, ASIC-resistant
- **Confidential Transactions (CT)**: Amounts are hidden on-chain using
  Pedersen commitments (activated at height 8000)
- **ASERT Difficulty Adjustment**: Responsive difficulty algorithm
- **5-minute block time**: Faster confirmations than Bitcoin
- **Independent genesis**: RCPU has its own genesis block and chain parameters

## Upstream

RCPU Core is forked from [Bitcoin Core](https://github.com/bitcoin/bitcoin) 27.0.
We maintain the upstream copyright and license, and contribute back where possible.


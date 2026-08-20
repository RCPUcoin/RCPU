# RCPU

RCPU 是一个基于 Bitcoin Core 27.0 分叉的独立公有链（cryptocurrency），采用
[RandomX](https://github.com/tevador/RandomX) 工作量证明算法，旨在通过抗 ASIC
的 CPU 友好型挖矿实现更公平、更去中心化的出块与代币分发。

- 官方仓库：https://github.com/RCPUcoin/RCPU
- 区块浏览器 / 社区：见下方「链接」小节

---

## RCPU 是什么？

RCPU 是一条独立的 PoW 公有链。它继承了 Bitcoin Core 久经考验的共识内核、
P2P 网络、交易与钱包实现，同时将工作量证明算法替换为 RandomX，并引入了
独立的创世区块、链参数与网络魔法值，形成一条与 Bitcoin 完全隔离的新链。

RCPU 节点会下载并完整验证区块与交易，同时可选地构建图形化钱包界面。

更多技术细节见 [doc 目录](/doc)。

---

## 与 Bitcoin Core 的主要区别

| 维度 | Bitcoin Core | RCPU |
|------|--------------|------|
| 共识算法 | SHA-256（ASIC 主导） | RandomX（抗 ASIC，CPU 友好） |
| 出块间隔 | ~10 分钟 | 5 分钟 |
| 减半周期 | 210000 块 | 210000 块（约 2 年） |
| 网络魔数 | `0xf9beb4d9` | `RCPU`（`0x52504355`） |
| 主网端口 | 8333 | 9965 |
| bech32 前缀 | `bc` | `rcpu`（主网） |
| 链类型 | MAIN/TESTNET/REGTEST/SIGNET | RCPUMAIN/RCPUTESTNET/RCPUREGTEST |

---

## 快速开始

### 编译

依赖与编译步骤与 Bitcoin Core 基本一致。请参照：

- [doc/build-unix.md](doc/build-unix.md) — Linux / macOS
- [doc/build-windows.md](doc/build-windows.md) — Windows
- [doc/build-android.md](doc/build-android.md) — Android（可选）

通用流程（Linux）：

\`\`\`bash
./autogen.sh
./configure
make -j$(nproc)
\`\`\`

编译产物为：

| 命令 | 说明 |
|------|------|
| `rcpud` | RCPU 节点守护进程 |
| `rcpu-cli` | RPC 命令行客户端 |
| `rcpu-tx` | 交易工具 |
| `rcpu-wallet` | 钱包工具 |
| `rcpu-qt` | 图形化钱包（可选） |

### 运行节点

\`\`\`bash
# 启动节点（主网）
./src/rcpud -daemon

# 查看链状态
./src/rcpu-cli getblockchaininfo
\`\`\`

---

## 链接

- 源码：https://github.com/RCPUcoin/RCPU
- 问题反馈：https://github.com/RCPUcoin/RCPU/issues
- 许可证：MIT（见 [COPYING](COPYING)）

---

## 开发流程

主分支会定期构建（见 `doc/build-*.md`）并测试，但不保证完全稳定。
请通过 GitHub 提交 issue 与 pull request 参与贡献。

贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，开发提示见
[doc/developer-notes.md](doc/developer-notes.md)。

## 测试

鼓励开发者为新代码编写单元测试，运行方式：

\`\`\`bash
make check
\`\`\`

另有基于 Python 的回归与集成测试，位于 [test/](test/)：

\`\`\`bash
test/functional/test_runner.py
\`\`\`

CI 会对每个 pull request 在 Windows / Linux / macOS 上自动构建并运行单元与
sanitize 测试。

## 许可证

RCPU 基于 MIT 许可证发布。详见 [COPYING](COPYING) 或
https://opensource.org/licenses/MIT。

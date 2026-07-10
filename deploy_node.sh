#!/bin/bash
# RCPU节点部署脚本
set -e

echo "=== RCPU节点部署 ==="
echo "服务器: $1"

# 安装依赖
echo "[1/5] 安装依赖..."
apt-get update -qq
apt-get install -y -qq build-essential libtool autotools-dev automake pkg-config bsdmainutils curl git cmake bison libevent-dev libboost-system-dev libboost-filesystem-dev libboost-test-dev libboost-thread-dev libdb-dev libdb++-dev 2>/dev/null || true

# 创建rcpu用户
id -u rcpu &>/dev/null || useradd -m -s /bin/bash rcpu 2>/dev/null || true

# 创建数据目录
mkdir -p /root/.rcpu
cat > /root/.rcpu/rcpu.conf << 'CONFEOF'
# RCPU节点配置
daemon=1
listen=1
server=1
txindex=1
rpcuser=rcpurpc
rpcpassword=rcpurpc2026
rpcallowip=0.0.0.0/0
rpcbind=0.0.0.0
bind=0.0.0.0
port=9363
rpcport=9362
addnode=103.74.192.168:9363
CONFEOF

echo "[2/5] 等待从主节点复制二进制文件..."

EOF && chmod +x /root/rcpuchain/deploy_node.sh

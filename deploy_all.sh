#!/bin/bash
# RCPU 多服务器部署脚本
SERVERS=(
    "43.156.103.27:22"
    "38.147.171.29:47005"
    "38.55.199.177:22"
    "47.85.38.146:22"
    "119.28.152.245:22"
    "8.166.130.149:22"
)
PASS="13559714383cQ@"
USER="root"

for server in "${SERVERS[@]}"; do
    IFS=':' read -r HOST PORT <<< "$server"
    echo "=== 部署到 $HOST:$PORT ==="

    # 复制二进制文件
    sshpass -p "$PASS" scp -o StrictHostKeyChecking=no -P "$PORT" \
        /root/rcpuchain/src/rcpud \
        /root/rcpuchain/src/rcpu-cli \
        /root/rcpuchain/src/rcpu-tx \
        /root/rcpuchain/src/rcpu-wallet \
        "$USER@$HOST:/usr/local/bin/" 2>/dev/null || echo "SCP failed for $HOST"

    # 复制配置文件和服务文件
    sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -p "$PORT" "$USER@$HOST" \
        "mkdir -p /root/.rcpu" 2>/dev/null

    sshpass -p "$PASS" scp -o StrictHostKeyChecking=no -P "$PORT" \
        /root/rcpuchain/rcpu.service \
        "$USER@$HOST:/etc/systemd/system/" 2>/dev/null || echo "Service SCP failed for $HOST"
done

echo "所有服务器部署完成"

EOF && chmod +x /root/rcpuchain/deploy_all.sh

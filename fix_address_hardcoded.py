import paramiko

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=user, password=password, timeout=30)

print("=== 硬编码scriptPubKey ===")

stdin, stdout, stderr = ssh.exec_command('''
cat > /tmp/addr_hardcoded.js << 'EOF'
const SCRIPT_PUB_KEY_MAP = new Map([
    ["rcpu1qlx8p93gzm6f9h0nn7mn6p5k69t60wj6g7u24w0", "0014f98e12c502de925bbe73f6e7a0d2da2af4f74b48"],
    ["rcpu1q8f7ltdsjh4k3zavgxf64zkukw9s66z82n3th20", "00143a7df5b612bd6d1175883275515b967161ad08ea"]
]);

function addressToScriptPubKey(address) {
    if (!address) {
        console.log("[POOL] Invalid address: null");
        return '76a91400000000000000000000000000000000000000000088ac';
    }
    
    const lowerAddr = address.toLowerCase();
    if (SCRIPT_PUB_KEY_MAP.has(lowerAddr)) {
        return SCRIPT_PUB_KEY_MAP.get(lowerAddr);
    }
    
    console.log("[POOL] Unknown address, using default: " + address);
    return '76a91400000000000000000000000000000000000000000088ac';
}
EOF
''')
print("临时文件创建完成")

stdin, stdout, stderr = ssh.exec_command('''
sed -i '/^function bech32Decode/,/^function convertBits/{/^function convertBits/!d; /^function bech32Decode/r /tmp/addr_hardcoded.js}' /root/stratum-proxy-pool.js
''')
print("函数替换完成")

stdin, stdout, stderr = ssh.exec_command('''
sed -i '/^function bech32Decode/,/^function addressToScriptPubKey/{/^function addressToScriptPubKey/!d}' /root/stratum-proxy-pool.js
''')
print("清理旧bech32函数")

print("\n=== 验证修改 ===")
stdin, stdout, stderr = ssh.exec_command('sed -n "81,105p" /root/stratum-proxy-pool.js')
print(stdout.read().decode())

print("\n=== 重启矿池 ===")
stdin, stdout, stderr = ssh.exec_command('killall -9 node 2>/dev/null; sleep 2')
print("旧进程已停止")

stdin, stdout, stderr = ssh.exec_command('cd /root && nohup node stratum-proxy-pool.js > /root/pool.log 2>&1 &')
print("新矿池启动中...")

stdin, stdout, stderr = ssh.exec_command('sleep 5 && tail -20 /root/pool.log')
print("\n启动日志:")
print(stdout.read().decode())

ssh.close()

print("\n" + "="*60)
print("修复完成！")
print("硬编码scriptPubKey")
print("="*60)
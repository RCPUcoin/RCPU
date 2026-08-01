import paramiko

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=user, password=password, timeout=30)

print("=== 查看getBlockTemplate函数 ===")
stdin, stdout, stderr = ssh.exec_command('grep -n "getBlockTemplate" /root/stratum-proxy-pool.js')
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('sed -n "290,310p" /root/stratum-proxy-pool.js')
print("\n函数内容:")
print(stdout.read().decode())

print("\n=== 修复getBlockTemplate函数 ===")
stdin, stdout, stderr = ssh.exec_command('''
cat > /tmp/fix_gbt.js << 'EOF'
async function getBlockTemplate() {
    try {
        const response = await makeRpcRequest("getblocktemplate", [{ rules: ["segwit"] }]);
        if (response) {
            const miningInfo = await makeRpcRequest("getmininginfo", []);
            if (miningInfo && miningInfo.difficulty) {
                response.difficulty = miningInfo.difficulty;
            }
        }
        return response;
    } catch (e) {
        log("getblocktemplate error: " + e.message);
        return null;
    }
}
EOF
''')
print("临时文件创建完成")

stdin, stdout, stderr = ssh.exec_command('''
sed -i '/^async function getBlockTemplate() {/,/^}/d' /root/stratum-proxy-pool.js
''')
print("旧函数已删除")

stdin, stdout, stderr = ssh.exec_command('''
grep -n "function makeRpcRequest" /root/stratum-proxy-pool.js | head -1
''')
line_num = stdout.read().decode().split(':')[0]
print("插入位置: " + line_num)

stdin, stdout, stderr = ssh.exec_command(f'''
sed -i '{line_num}r /tmp/fix_gbt.js' /root/stratum-proxy-pool.js
''')
print("新函数已插入")

stdin, stdout, stderr = ssh.exec_command('sed -n "290,310p" /root/stratum-proxy-pool.js')
print("\n验证修改:")
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
print("="*60)
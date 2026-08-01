import paramiko

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

print("=== 检查share难度修改效果 ===")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=30)
    
    print("\n1. 查看最新矿池日志...")
    stdin, stdout, stderr = ssh.exec_command('tail -30 /root/pool.log')
    print(stdout.read().decode())
    
    print("\n2. 查看当前share难度设置...")
    stdin, stdout, stderr = ssh.exec_command('grep -n "shareDifficulty\\|MIN_SHARE_DIFFICULTY" /root/stratum-proxy-pool.js')
    print(stdout.read().decode())
    
    print("\n3. 修改为合理的share难度（网络难度的1/10）...")
    stdin, stdout, stderr = ssh.exec_command('''
sed -i 's/const MIN_SHARE_DIFFICULTY = [0-9.]\+;/const MIN_SHARE_DIFFICULTY = 0.000024;/' /root/stratum-proxy-pool.js
''')
    stdout.channel.recv_exit_status()
    
    print("\n4. 修改第410行为取较大值...")
    stdin, stdout, stderr = ssh.exec_command('''
sed -i 's/const shareDifficulty = Math.min(MIN_SHARE_DIFFICULTY, networkDifficulty);/const shareDifficulty = Math.max(MIN_SHARE_DIFFICULTY, networkDifficulty);/' /root/stratum-proxy-pool.js
''')
    stdout.channel.recv_exit_status()
    
    print("\n5. 验证修改...")
    stdin, stdout, stderr = ssh.exec_command('grep -n "MIN_SHARE_DIFFICULTY\\|shareDifficulty = Math" /root/stratum-proxy-pool.js')
    print(stdout.read().decode())
    
    print("\n6. 重启矿池...")
    stdin, stdout, stderr = ssh.exec_command('killall -9 node 2>/dev/null; sleep 2')
    stdout.channel.recv_exit_status()
    
    stdin, stdout, stderr = ssh.exec_command('cd /root && node stratum-proxy-pool.js > /root/pool.log 2>&1 &')
    stdout.channel.recv_exit_status()
    
    stdin, stdout, stderr = ssh.exec_command('sleep 5 && tail -20 /root/pool.log')
    print(stdout.read().decode())
    
    ssh.close()
    
    print("\n完成!")
    
except Exception as e:
    print("失败: " + str(e))

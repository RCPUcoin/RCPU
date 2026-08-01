import paramiko

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=user, password=password, timeout=30)

print("=== 搜索出块相关日志 ===")
stdin, stdout, stderr = ssh.exec_command('grep -E "BLOCK|submitblock|merkle|coinbase" /root/pool.log')
print(stdout.read().decode())

print("\n=== 检查节点最近区块 ===")
stdin, stdout, stderr = ssh.exec_command('curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d \'{"method":"getblockhash","params":[61],"id":1}\'')
print("Block 61:", stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d \'{"method":"getblockhash","params":[60],"id":1}\'')
print("Block 60:", stdout.read().decode())

print("\n=== 检查coinbase交易结构 ===")
stdin, stdout, stderr = ssh.exec_command('curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d \'{"method":"getblocktemplate","params":[{"rules":["segwit"]}],"id":1}\'')
result = stdout.read().decode()
print("GBT coinb1:", result[:500])

ssh.close()
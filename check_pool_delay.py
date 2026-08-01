import paramiko
import time

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

print("等待30秒后检查...")
time.sleep(30)

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=user, password=password, timeout=30)

print("\n=== 最新矿池日志 ===")
stdin, stdout, stderr = ssh.exec_command('tail -50 /root/pool.log')
print(stdout.read().decode())

print("\n=== 节点状态 ===")
stdin, stdout, stderr = ssh.exec_command('curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d \'{"method":"getmininginfo","params":[],"id":1}\'')
print(stdout.read().decode())

print("\n=== 区块高度 ===")
stdin, stdout, stderr = ssh.exec_command('curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d \'{"method":"getblockcount","params":[],"id":1}\'')
print(stdout.read().decode())

ssh.close()
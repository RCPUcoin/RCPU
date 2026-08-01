import paramiko
import json

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, port=port, username=user, password=password, timeout=30)

print('=== 矿池最新日志 ===')
stdin, stdout, stderr = ssh.exec_command('tail -30 /root/pool.log')
print(stdout.read().decode())

print('=== 使用Python调用节点RPC ===')
stdin, stdout, stderr = ssh.exec_command('python3 -c "import urllib.request, json, base64; req=urllib.request.Request(\'http://127.0.0.1:6988/\', data=json.dumps({\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getblockcount\"}).encode(), headers={\"Authorization\":\"Basic \" + base64.b64encode(b\'rcpuuser:rcpupassword\').decode()}); print(urllib.request.urlopen(req).read().decode())"')
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('python3 -c "import urllib.request, json, base64; req=urllib.request.Request(\'http://127.0.0.1:6988/\', data=json.dumps({\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getmininginfo\"}).encode(), headers={\"Authorization\":\"Basic \" + base64.b64encode(b\'rcpuuser:rcpupassword\').decode()}); print(urllib.request.urlopen(req).read().decode())"')
print(stdout.read().decode())

ssh.close()

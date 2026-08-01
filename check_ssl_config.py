import paramiko

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

print("=== 检查SSL配置 ===")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=30)
    
    print("\n当前nginx配置:")
    stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/rcpupool')
    print(stdout.read().decode())
    
    print("\n测试HTTPS API:")
    stdin, stdout, stderr = ssh.exec_command('curl -sk https://rcpupool.asia/api/stats')
    print("HTTPS响应:", stdout.read().decode())
    if stderr.read().decode():
        print("错误:", stderr.read().decode())
    
    ssh.close()
    
except Exception as e:
    print("失败: " + str(e))

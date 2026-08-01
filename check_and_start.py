import paramiko

hostname = '103.74.192.168'
port = 45148
username = 'root'
password = '13559714383cQ@'

def execute_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def main():
    print("=" * 70)
    print("检查文件语法并启动代理")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 检查JavaScript语法 ---")
        output, error = execute_command(ssh, "node -c /root/stratum-proxy-fixed.js")
        if error:
            print(f"语法错误: {error}")
        else:
            print("语法检查通过")
        
        print("\n--- 2. 查看第278行附近代码 ---")
        output, _ = execute_command(ssh, "sed -n '270,290p' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 3. 手动启动代理并查看错误 ---")
        output, error = execute_command(ssh, "cd /root && node stratum-proxy-fixed.js 2>&1 & sleep 2 && ps aux | grep stratum-proxy-fixed | grep -v grep")
        print("输出:", output)
        if error:
            print("错误:", error)
        
        print("\n--- 4. 查看最新日志 ---")
        output, _ = execute_command(ssh, "tail -20 /var/log/stratum-proxy.log")
        print(output)
        
        print("\n--- 5. 检查端口 ---")
        output, _ = execute_command(ssh, "netstat -tlnp | grep :8080 || ss -tlnp | grep :8080")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("检查完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
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
    print("重新启动Stratum代理")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 检查是否有残留进程 ---")
        output, _ = execute_command(ssh, "ps aux | grep stratum-proxy | grep -v grep")
        print(output if output else "无残留进程")
        
        print("\n--- 2. 强制终止所有相关进程 ---")
        output, _ = execute_command(ssh, "pkill -9 -f stratum-proxy 2>/dev/null; sleep 1")
        print("已清理")
        
        print("\n--- 3. 检查端口8080占用 ---")
        output, _ = execute_command(ssh, "netstat -tlnp | grep :8080 || ss -tlnp | grep :8080")
        print(output if output else "端口8080未被占用")
        
        print("\n--- 4. 启动Stratum代理 ---")
        output, _ = execute_command(ssh, "cd /root && nohup node stratum-proxy-fixed.js > /var/log/stratum-proxy.log 2>&1 &")
        print("启动命令已执行")
        
        print("\n--- 5. 等待3秒后检查进程 ---")
        output, _ = execute_command(ssh, "sleep 3 && ps aux | grep stratum-proxy-fixed | grep -v grep")
        print(output if output else "进程未启动")
        
        print("\n--- 6. 检查端口监听 ---")
        output, _ = execute_command(ssh, "sleep 1 && netstat -tlnp | grep :8080 || ss -tlnp | grep :8080")
        print(output if output else "端口未监听")
        
        print("\n--- 7. 查看最新日志 ---")
        output, _ = execute_command(ssh, "tail -30 /var/log/stratum-proxy.log")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("操作完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
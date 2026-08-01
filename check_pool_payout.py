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
    print("检查矿池份额分配功能")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看代理代码中的份额跟踪逻辑 ---")
        output, _ = execute_command(ssh, "grep -n 'share\\|payout\\|balance\\|reward\\|分配' /root/stratum-proxy-fixed.js | head -50")
        print(output)
        
        print("\n--- 2. 查看代理代码中的矿工管理逻辑 ---")
        output, _ = execute_command(ssh, "grep -n 'miner\\|worker\\|client\\|auth' /root/stratum-proxy-fixed.js | head -30")
        print(output)
        
        print("\n--- 3. 查看当前连接的矿工 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getmininginfo\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 4. 查看代理是否有数据库或文件存储份额 ---")
        output, _ = execute_command(ssh, "ls -la /root/*.db /root/*.json /root/*.log 2>/dev/null | head -20")
        print(output)
        
        print("\n--- 5. 查看代理代码结构 ---")
        output, _ = execute_command(ssh, "head -100 /root/stratum-proxy-fixed.js")
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
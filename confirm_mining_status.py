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
    print("确认挖矿状态")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 当前区块高度 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockcount\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 2. 最新区块信息 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockchaininfo\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 3. 最新代理日志 ---")
        output, _ = execute_command(ssh, "tail -30 /var/log/stratum-proxy.log")
        print(output)
        
        print("\n--- 4. 检查是否有区块提交记录 ---")
        output, _ = execute_command(ssh, "grep -i 'BLOCK ACCEPTED\\|BLOCK FOUND\\|rejected' /var/log/stratum-proxy.log | tail -20")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("确认完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
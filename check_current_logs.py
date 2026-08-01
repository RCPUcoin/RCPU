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
    print("查看当前代理日志和节点日志")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看stratum-proxy-fixed.js日志 ---")
        output, _ = execute_command(ssh, "tail -100 /root/stratum.log")
        print(output)
        
        print("\n--- 2. 查看节点日志中的提交失败记录 ---")
        output, _ = execute_command(ssh, "grep -i 'reject\\|error\\|invalid\\|bad' /root/.rcpu/debug.log | tail -50")
        print(output)
        
        print("\n--- 3. 查看当前运行的代理进程 ---")
        output, _ = execute_command(ssh, "ps aux | grep -i stratum")
        print(output)
        
        print("\n--- 4. 测试直接提交区块 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblocktemplate\",\"params\":[{\"rules\":[\"segwit\"]}],\"id\":1}' | python3 -m json.tool")
        print(output)
        
        ssh.close()
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
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
    print("深度诊断：矿工算力1.81 khash/s但不出块")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看最新代理日志（是否有区块提交） ---")
        output, _ = execute_command(ssh, "grep -E 'BLOCK FOUND|submitblock|rejected|error' /var/log/stratum-proxy.log | tail -30")
        print(output)
        
        print("\n--- 2. 查看完整代理日志（最近100行） ---")
        output, _ = execute_command(ssh, "tail -100 /var/log/stratum-proxy.log")
        print(output)
        
        print("\n--- 3. 当前区块高度和状态 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockcount\",\"params\":[],\"id\":1}'")
        print("区块高度:", output)
        
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getmininginfo\",\"params\":[],\"id\":1}'")
        print("挖矿信息:", output)
        
        print("\n--- 4. 查看节点debug日志（是否有错误） ---")
        output, _ = execute_command(ssh, "tail -50 /root/.rcpu/debug.log")
        print(output)
        
        print("\n--- 5. 查看代理提交区块的代码逻辑 ---")
        output, _ = execute_command(ssh, "sed -n '200,270p' /root/stratum-proxy-fixed.js")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("诊断完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
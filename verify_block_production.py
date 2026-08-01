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
    print("验证区块出块情况")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 当前区块高度 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockcount\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 2. 查看最新区块信息 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockhash\",\"params\":[53],\"id\":1}'")
        import json
        blockhash = json.loads(output)['result']
        print(f"区块53 hash: {blockhash}")
        
        output, _ = execute_command(ssh, f"curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{{\"method\":\"getblock\",\"params\":[\"{blockhash}\"],\"id\":1}}'")
        print(output)
        
        print("\n--- 3. 查看最近10个区块 ---")
        for i in range(44, 54):
            output, _ = execute_command(ssh, f"curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{{\"method\":\"getblockhash\",\"params\":[{i}]}}'")
            try:
                h = json.loads(output)['result']
                print(f"区块 {i}: {h}")
            except:
                pass
        
        print("\n--- 4. 查看代理日志中的区块提交记录 ---")
        output, _ = execute_command(ssh, "grep -i 'BLOCK ACCEPTED\\|BLOCK FOUND\\|submitblock' /var/log/stratum-proxy.log")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("验证完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
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
    print("分析coinbase交易和merkle root问题")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 获取区块模板 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblocktemplate\",\"params\":[{\"rules\":[\"segwit\"]}],\"id\":1}'")
        print(output[:2000])
        
        print("\n--- 2. 查看现有区块的交易 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockhash\",\"params\":[40],\"id\":1}'")
        print(output)
        
        ssh.close()
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")

if __name__ == "__main__":
    main()
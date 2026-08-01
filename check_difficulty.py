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
    print("查看当前挖矿难度设置")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 挖矿信息 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getmininginfo\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 2. 区块模板 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblocktemplate\",\"params\":[{\"rules\":[\"segwit\"]}],\"id\":1}'")
        print(output)
        
        print("\n--- 3. 当前区块详情 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockchaininfo\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 4. 查看代理配置中的难度设置 ---")
        output, _ = execute_command(ssh, "grep -n 'MIN_SHARE_DIFFICULTY\\|shareDifficulty\\|target' /root/stratum-proxy-fixed.js | head -20")
        print(output)
        
        print("\n--- 5. 查看节点配置文件 ---")
        output, _ = execute_command(ssh, "cat /root/.rcpu/rcpu.conf")
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
import paramiko

src_host = '103.74.192.168'
src_port = 45148
src_user = 'root'
src_pass = '13559714383cQ@'

def execute_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def main():
    print("=" * 70)
    print("步骤1: 检查源服务器钱包位置和结构")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(src_host, src_port, src_user, src_pass, timeout=30)
        
        print("\n--- 1. 查找钱包文件 ---")
        output, _ = execute_command(ssh, "find /root -name '*.dat' -o -name 'wallet*' 2>/dev/null | head -20")
        print(output)
        
        print("\n--- 2. 查找RCPU数据目录 ---")
        output, _ = execute_command(ssh, "find /root -name '.rcpu' -type d 2>/dev/null")
        print(output)
        
        output, _ = execute_command(ssh, "ls -la /root/.rcpu/ 2>/dev/null")
        print(output)
        
        print("\n--- 3. 查找配置文件 ---")
        output, _ = execute_command(ssh, "find /root -name 'rcpu.conf' -o -name 'bitcoin.conf' 2>/dev/null")
        print(output)
        
        print("\n--- 4. 查看钱包信息 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getwalletinfo\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 5. 查看区块数据 ---")
        output, _ = execute_command(ssh, "ls -la /root/.rcpu/blocks/ 2>/dev/null | head -10")
        print(output)
        
        print("\n--- 6. 查看节点进程 ---")
        output, _ = execute_command(ssh, "ps aux | grep -i rcpu | grep -v grep")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("步骤1完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
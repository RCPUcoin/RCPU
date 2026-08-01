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
    print("查看当前代理的实际运行日志")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看当前代理日志 (/var/log/stratum-proxy.log) ---")
        output, _ = execute_command(ssh, "tail -100 /var/log/stratum-proxy.log")
        print(output)
        
        print("\n--- 2. 查看节点debug.log最新记录 ---")
        output, _ = execute_command(ssh, "tail -100 /root/.rcpu/debug.log")
        print(output)
        
        print("\n--- 3. 查看当前代理的关键代码段 ---")
        output, _ = execute_command(ssh, "sed -n '196,330p' /root/stratum-proxy-fixed.js")
        print(output)
        
        ssh.close()
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
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
    print("对比原始stratum-proxy.js和当前stratum-proxy-fixed.js")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看原始stratum-proxy.js的关键代码 ---")
        output, _ = execute_command(ssh, "cat /root/stratum-proxy.js")
        print(output)
        
        print("\n" + "=" * 70)
        print("对比完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
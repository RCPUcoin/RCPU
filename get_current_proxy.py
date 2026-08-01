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
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("获取当前stratum-proxy-fixed.js完整代码...")
        output, _ = execute_command(ssh, "cat /root/stratum-proxy-fixed.js")
        with open('c:\\Users\\92763\\Desktop\\RCPU主链\\RCPU\\current_proxy.js', 'w', encoding='utf-8') as f:
            f.write(output)
        print("已保存到 current_proxy.js")
        
        print("\n--- 对比两个文件的差异 ---")
        output, _ = execute_command(ssh, "diff /root/stratum-proxy.js /root/stratum-proxy-fixed.js")
        print(output)
        
        ssh.close()
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
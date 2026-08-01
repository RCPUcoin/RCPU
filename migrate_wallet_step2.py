import paramiko

dst_host = '38.147.171.29'
dst_port = 47005
dst_user = 'root'
dst_pass = '13559714383cQ@'

def execute_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def main():
    print("=" * 70)
    print("步骤2: 检查目标服务器环境")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(dst_host, dst_port, dst_user, dst_pass, timeout=30)
        
        print("\n--- 1. 系统信息 ---")
        output, _ = execute_command(ssh, "uname -a && cat /etc/os-release")
        print(output)
        
        print("\n--- 2. CPU和内存 ---")
        output, _ = execute_command(ssh, "cat /proc/cpuinfo | grep 'model name' | head -1 && free -h")
        print(output)
        
        print("\n--- 3. 磁盘空间 ---")
        output, _ = execute_command(ssh, "df -h")
        print(output)
        
        print("\n--- 4. 已有软件 ---")
        output, _ = execute_command(ssh, "which node npm git wget curl")
        print(output)
        
        print("\n--- 5. 检查是否已有RCPU安装 ---")
        output, _ = execute_command(ssh, "ls -la /root/ | grep -i rcpu")
        print(output)
        
        output, _ = execute_command(ssh, "ls -la /root/.rcpu/ 2>/dev/null || echo 'No .rcpu directory'")
        print(output)
        
        print("\n--- 6. 检查端口占用 ---")
        output, _ = execute_command(ssh, "netstat -tlnp 2>/dev/null | grep -E '6988|8080' || ss -tlnp | grep -E '6988|8080'")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("步骤2完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
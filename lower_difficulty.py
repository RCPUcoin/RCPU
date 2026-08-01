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
    print("降低share难度，让矿工正常工作")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 停止代理进程 ---")
        output, _ = execute_command(ssh, "pkill -9 -f stratum-proxy-fixed.js")
        print("进程已停止")
        
        print("\n--- 2. 将share难度从100降低到1 ---")
        output, _ = execute_command(ssh, "sed -i 's/const MIN_SHARE_DIFFICULTY = 100;/const MIN_SHARE_DIFFICULTY = 1;/' /root/stratum-proxy-fixed.js")
        print("已将最低share难度从100调整为1")
        
        print("\n--- 3. 验证修改 ---")
        output, _ = execute_command(ssh, "grep -n 'MIN_SHARE_DIFFICULTY' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 4. 验证语法 ---")
        output, _ = execute_command(ssh, "node -c /root/stratum-proxy-fixed.js")
        if output == "":
            print("语法检查通过")
        else:
            print(f"语法错误: {output}")
        
        print("\n--- 5. 启动代理进程 ---")
        output, _ = execute_command(ssh, "cd /root && nohup node stratum-proxy-fixed.js > /var/log/stratum-proxy.log 2>&1 &")
        print("代理进程已启动")
        
        print("\n--- 6. 验证进程运行 ---")
        output, _ = execute_command(ssh, "sleep 2 && ps aux | grep -i stratum | grep -v grep")
        print(output)
        
        print("\n--- 7. 查看启动日志 ---")
        output, _ = execute_command(ssh, "sleep 3 && tail -15 /var/log/stratum-proxy.log")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("难度调整完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
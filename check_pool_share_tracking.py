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
    print("检查矿池份额分配功能详情")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看代理完整代码结构 ---")
        output, _ = execute_command(ssh, "wc -l /root/stratum-proxy-fixed.js && grep -n 'function\\|const\\|let\\|var' /root/stratum-proxy-fixed.js | head -40")
        print(output)
        
        print("\n--- 2. 搜索份额统计相关代码 ---")
        output, _ = execute_command(ssh, "grep -n 'shareCount\\|totalShares\\|shares\\|accepted\\|rejected' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 3. 搜索矿工状态管理 ---")
        output, _ = execute_command(ssh, "grep -n 'miners\\|workers\\|clients\\|pool' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 4. 搜索奖励分配相关代码 ---")
        output, _ = execute_command(ssh, "grep -n 'reward\\|payout\\|balance\\|distribute\\|分配' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 5. 查看区块提交后的处理逻辑 ---")
        output, _ = execute_command(ssh, "sed -n '580,650p' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 6. 查看代理是否有API接口 ---")
        output, _ = execute_command(ssh, "grep -n 'http\\|api\\|server\\|listen' /root/stratum-proxy-fixed.js | head -20")
        print(output)
        
        print("\n--- 7. 查看是否有相关的矿池管理工具 ---")
        output, _ = execute_command(ssh, "ls -la /root/ | grep -i 'pool\\|proxy\\|mining'")
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
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
    print("修复Stratum代理 - bad-txnmrklroot问题")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 备份原文件 ---")
        output, _ = execute_command(ssh, "cp /root/stratum-proxy-fixed.js /root/stratum-proxy-fixed.js.bak5")
        print("备份完成")
        
        print("\n--- 2. 修复merkle root字节序问题 ---")
        
        fix_command = '''
sed -i 's/const merkleRootLE = merkleRoot;/const merkleRootLE = reverseHex(merkleRoot);/' /root/stratum-proxy-fixed.js
'''
        output, _ = execute_command(ssh, fix_command)
        print("修复完成")
        
        print("\n--- 3. 验证修复 ---")
        output, _ = execute_command(ssh, "grep -n 'merkleRootLE' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 4. 重启Stratum代理 ---")
        output, _ = execute_command(ssh, "pkill -f stratum-proxy-fixed.js; sleep 2; nohup node /root/stratum-proxy-fixed.js > /var/log/stratum-proxy.log 2>&1 &")
        print("代理已重启")
        
        print("\n--- 5. 验证代理进程 ---")
        output, _ = execute_command(ssh, "sleep 3; ps aux | grep stratum-proxy-fixed | grep -v grep")
        print(output)
        
        print("\n--- 6. 查看重启后日志 ---")
        output, _ = execute_command(ssh, "tail -20 /var/log/stratum-proxy.log")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("修复完成！等待矿工提交区块验证...")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
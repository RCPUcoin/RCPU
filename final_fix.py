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
    print("最终修复 - 完全移除segwit数据")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 杀死旧进程 ---")
        output, _ = execute_command(ssh, "pkill -9 -f stratum-proxy-fixed.js; sleep 2")
        print("旧进程已杀死")
        
        print("\n--- 2. 查看当前文件内容 ---")
        output, _ = execute_command(ssh, "cat /root/stratum-proxy-fixed.js")
        content = output
        
        print("\n--- 3. 替换所有segwit相关代码 ---")
        content = content.replace("'01000000' +\n                '0001' +\n                '01'", "'01000000' +\n                '01'")
        content = content.replace("'01000000' +\n                '0001' +\n            '01'", "'01000000' +\n            '01'")
        content = content.replace("'02' +\n                valueLE +", "'01' +\n                valueLE +")
        content = content.replace("'0000000000000000' +\n                '26' +\n                witnessCommitment +\n                '01' +\n                '20' +\n                '0000000000000000000000000000000000000000000000000000000000000000' +\n                '00000000';", "'00000000';")
        
        print("\n--- 4. 写入修复后的文件 ---")
        stdin, stdout, stderr = ssh.exec_command("cat > /root/stratum-proxy-fixed.js")
        stdin.write(content)
        stdin.flush()
        stdin.channel.shutdown_write()
        print("文件写入完成")
        
        print("\n--- 5. 验证修复 ---")
        output, _ = execute_command(ssh, "grep -n '0001' /root/stratum-proxy-fixed.js")
        if output:
            print(f"仍然存在segwit标记: {output}")
        else:
            print("segwit标记已移除")
        
        output, _ = execute_command(ssh, "grep -n 'witnessCommitment' /root/stratum-proxy-fixed.js")
        if output:
            print(f"仍然存在witnessCommitment: {output}")
        else:
            print("witnessCommitment已移除")
        
        output, _ = execute_command(ssh, "grep -n \"'02'\" /root/stratum-proxy-fixed.js")
        if output:
            print(f"仍然存在双输出: {output}")
        else:
            print("双输出已移除")
        
        print("\n--- 6. 启动代理 ---")
        output, _ = execute_command(ssh, "cd /root && nohup node stratum-proxy-fixed.js > /var/log/stratum-proxy.log 2>&1 &")
        print("代理已启动")
        
        print("\n--- 7. 等待3秒后检查进程 ---")
        output, _ = execute_command(ssh, "sleep 3 && ps aux | grep stratum-proxy-fixed | grep -v grep")
        print(output if output else "进程未启动")
        
        print("\n--- 8. 查看最新日志 ---")
        output, _ = execute_command(ssh, "tail -15 /var/log/stratum-proxy.log")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("修复完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
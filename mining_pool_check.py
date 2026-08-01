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
    print("=" * 60)
    print("RCPU矿池全面检测")
    print("=" * 60)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        print("[OK] SSH连接成功")
        print()
        
        print("=" * 60)
        print("1. 系统信息")
        print("=" * 60)
        output, _ = execute_command(ssh, "uname -a")
        print(output)
        
        print("=" * 60)
        print("2. 内存状态")
        print("=" * 60)
        output, _ = execute_command(ssh, "free -h")
        print(output)
        
        print("=" * 60)
        print("3. CPU状态")
        print("=" * 60)
        output, _ = execute_command(ssh, "top -bn1 | head -20")
        print(output)
        
        print("=" * 60)
        print("4. 磁盘状态")
        print("=" * 60)
        output, _ = execute_command(ssh, "df -h")
        print(output)
        
        print("=" * 60)
        print("5. 运行中的服务")
        print("=" * 60)
        output, _ = execute_command(ssh, "systemctl list-units --type=service --state=running 2>/dev/null || ps aux --sort=-%mem | head -20")
        print(output)
        
        print("=" * 60)
        print("6. 挖矿相关进程")
        print("=" * 60)
        output, _ = execute_command(ssh, "ps aux | grep -iE 'miner|pool|node|cpu|rcpu' | grep -v grep")
        print(output)
        
        print("=" * 60)
        print("7. 网络状态")
        print("=" * 60)
        output, _ = execute_command(ssh, "netstat -tlnp 2>/dev/null || ss -tlnp")
        print(output)
        
        print("=" * 60)
        print("8. 监听端口详情")
        print("=" * 60)
        output, _ = execute_command(ssh, "netstat -tlnp 2>/dev/null | grep -E ':(80|443|3333|8899|9999|8888|8080|3000|5000)' || ss -tlnp | grep -E ':(80|443|3333|8899|9999|8888|8080|3000|5000)'")
        print(output)
        
        print("=" * 60)
        print("9. 矿池配置文件查找")
        print("=" * 60)
        output, _ = execute_command(ssh, "find / -name '*config*.json' -o -name '*pool*.conf' -o -name '*miner*.conf' -o -name '*node*.json' 2>/dev/null | head -20")
        print(output)
        
        print("=" * 60)
        print("10. 挖矿日志文件查找")
        print("=" * 60)
        output, _ = execute_command(ssh, "find /var/log -type f -name '*.log' 2>/dev/null | head -20")
        print(output)
        
        print("=" * 60)
        print("11. RCPU相关目录")
        print("=" * 60)
        output, _ = execute_command(ssh, "ls -la /root/ 2>/dev/null; ls -la /home/ 2>/dev/null")
        print(output)
        
        print("=" * 60)
        print("12. 挖矿进程详细信息")
        print("=" * 60)
        output, _ = execute_command(ssh, "ps auxf | grep -iE 'miner|pool|node|rcpu' | grep -v grep")
        print(output)
        
        print("=" * 60)
        print("13. 最近系统日志")
        print("=" * 60)
        output, _ = execute_command(ssh, "tail -50 /var/log/syslog 2>/dev/null || tail -50 /var/log/messages 2>/dev/null || tail -50 /var/log/auth.log 2>/dev/null")
        print(output)
        
        print("=" * 60)
        print("14. 检查挖矿软件版本")
        print("=" * 60)
        output, _ = execute_command(ssh, "which rcpu-node 2>/dev/null || which rcpu-miner 2>/dev/null || find / -name 'rcpu-node' -o -name 'rcpu-miner' 2>/dev/null | head -5")
        print(output)
        
        print("=" * 60)
        print("15. 检测结果汇总")
        print("=" * 60)
        
        _, error = execute_command(ssh, "ps aux | grep -iE 'miner|pool|node|rcpu' | grep -v grep")
        if error == "":
            output, _ = execute_command(ssh, "ps aux | grep -iE 'miner|pool|node|rcpu' | grep -v grep | wc -l")
            miner_count = int(output.strip()) if output.strip() else 0
            if miner_count > 0:
                print(f"[OK] 发现 {miner_count} 个挖矿相关进程")
            else:
                print("[WARNING] 未发现挖矿相关进程")
        else:
            print("[ERROR] 无法检测挖矿进程")
        
        output, _ = execute_command(ssh, "free -m | grep Mem | awk '{print $3/$2*100}'")
        if output.strip():
            mem_usage = float(output.strip())
            print(f"内存使用率: {mem_usage:.1f}%")
        
        output, _ = execute_command(ssh, "df -h / | grep / | awk '{print $5}'")
        if output.strip():
            disk_usage = output.strip()
            print(f"磁盘使用率: {disk_usage}")
        
        ssh.close()
        print()
        print("=" * 60)
        print("检测完成")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] 连接失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
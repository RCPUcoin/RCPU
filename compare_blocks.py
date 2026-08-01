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
    print("对比成功出块(38/39/40)和当前状态")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 获取区块38/39/40的详情 ---")
        for block_num in [38, 39, 40]:
            output, _ = execute_command(ssh, f"curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{{\"method\":\"getblockhash\",\"params\":[{block_num}],\"id\":1}}'")
            import json
            try:
                blockhash = json.loads(output)['result']
                print(f"\n区块 {block_num} hash: {blockhash}")
                output2, _ = execute_command(ssh, f"curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{{\"method\":\"getblock\",\"params\":[\"{blockhash}\"],\"id\":1}}'")
                block_info = json.loads(output2)['result']
                print(f"时间戳: {block_info.get('time')}")
                print(f"难度: {block_info.get('difficulty')}")
                print(f"交易数: {len(block_info.get('tx', []))}")
                print(f"Merkle Root: {block_info.get('merkleroot')}")
                print(f"版本: {block_info.get('version')}")
            except:
                print(f"无法获取区块 {block_num} 详情")
        
        print("\n--- 2. 查看历史日志中成功出块的记录 ---")
        output, _ = execute_command(ssh, "grep -i 'BLOCK ACCEPTED\\|*** BLOCK FOUND ***' /var/log/stratum-proxy.log /root/stratum.log /var/log/proxy_8080.log 2>/dev/null || echo '未找到成功出块记录'")
        print(output)
        
        print("\n--- 3. 查看历史日志中区块38/39/40的相关记录 ---")
        output, _ = execute_command(ssh, "grep -E 'height=38|height=39|height=40' /var/log/stratum-proxy.log /root/stratum.log /var/log/proxy_8080.log 2>/dev/null | head -30")
        print(output)
        
        print("\n--- 4. 查看当前区块模板 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblocktemplate\",\"params\":[{\"rules\":[\"segwit\"]}],\"id\":1}'")
        print(output)
        
        print("\n--- 5. 查看当前节点状态 ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getmininginfo\",\"params\":[],\"id\":1}'")
        print(output)
        
        print("\n--- 6. 查看当前stratum-proxy-fixed.js关键代码 ---")
        output, _ = execute_command(ssh, "sed -n '270,310p' /root/stratum-proxy-fixed.js")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("对比完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
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
    print("RCPU矿池深度检测 - 节点状态与出块验证")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        print("[OK] SSH连接成功")
        print()
        
        print("=" * 70)
        print("1. RCPU节点状态检测 (RPC调用)")
        print("=" * 70)
        
        rpc_cmds = [
            ("getblockchaininfo", "获取区块链信息"),
            ("getnetworkinfo", "获取网络信息"),
            ("getmininginfo", "获取挖矿信息"),
            ("getpeerinfo", "获取节点连接信息"),
            ("getblockcount", "获取区块高度"),
            ("getdifficulty", "获取当前难度"),
        ]
        
        for cmd, desc in rpc_cmds:
            print(f"\n--- {desc} ---")
            rpc_cmd = f"curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{{\"method\":\"{cmd}\",\"params\":[],\"id\":1}}'"
            output, error = execute_command(ssh, rpc_cmd)
            if error:
                print(f"[ERROR] {error}")
            else:
                print(output[:2000])
        
        print("\n" + "=" * 70)
        print("2. 最近区块信息")
        print("=" * 70)
        
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblockcount\",\"params\":[],\"id\":1}'")
        import json
        try:
            block_count = json.loads(output)['result']
            print(f"当前区块高度: {block_count}")
            
            for i in range(0, 5):
                block_num = block_count - i
                print(f"\n--- 区块 #{block_num} ---")
                getblock_cmd = f"curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{{\"method\":\"getblock\",\"params\":[{block_num}],\"id\":1}}'"
                block_output, _ = execute_command(ssh, getblock_cmd)
                print(block_output[:1500])
        except Exception as e:
            print(f"获取区块信息失败: {e}")
        
        print("\n" + "=" * 70)
        print("3. Stratum代理日志检测")
        print("=" * 70)
        
        output, _ = execute_command(ssh, "tail -100 /var/log/stratum-proxy.log")
        print(output)
        
        print("\n" + "=" * 70)
        print("4. Gateway日志检测")
        print("=" * 70)
        
        output, _ = execute_command(ssh, "tail -100 /root/gateway.log")
        print(output)
        
        print("\n" + "=" * 70)
        print("5. 矿池配置文件")
        print("=" * 70)
        
        output, _ = execute_command(ssh, "cat /root/stratum-proxy-fixed.js 2>/dev/null | head -100")
        print(output)
        
        print("\n" + "=" * 70)
        print("6. 当前连接的矿工")
        print("=" * 70)
        
        output, _ = execute_command(ssh, "netstat -tnp 2>/dev/null | grep :8080 | grep ESTABLISHED || ss -tnp | grep :8080 | grep ESTAB")
        if output.strip():
            print(output)
        else:
            print("未发现活跃的矿工连接")
        
        print("\n" + "=" * 70)
        print("7. 测试矿工连接")
        print("=" * 70)
        
        test_cmd = """curl -s -X POST http://127.0.0.1:8080 --data-binary '{"id":1,"method":"mining.subscribe","params":[]}' 2>/dev/null | head -c 500"""
        output, error = execute_command(ssh, test_cmd)
        if output.strip():
            print(f"订阅响应: {output}")
        else:
            print(f"订阅测试失败: {error}")
        
        print("\n" + "=" * 70)
        print("8. 钱包与出块奖励")
        print("=" * 70)
        
        rpc_cmds2 = [
            ("listaccounts", "列出账户"),
            ("getbalance", "获取余额"),
            ("getwalletinfo", "获取钱包信息"),
        ]
        
        for cmd, desc in rpc_cmds2:
            print(f"\n--- {desc} ---")
            rpc_cmd = f"curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{{\"method\":\"{cmd}\",\"params\":[],\"id\":1}}'"
            output, error = execute_command(ssh, rpc_cmd)
            if error:
                print(f"[ERROR] {error}")
            else:
                print(output[:1000])
        
        print("\n" + "=" * 70)
        print("9. 检测结果汇总")
        print("=" * 70)
        
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getmininginfo\",\"params\":[],\"id\":1}'")
        try:
            mining_info = json.loads(output)['result']
            print(f"出块状态: {'正常' if mining_info.get('blocks', 0) > 0 else '异常'}")
            print(f"当前区块: {mining_info.get('blocks', 0)}")
            print(f"网络哈希率: {mining_info.get('networkhashps', 0)}")
            print(f"难度: {mining_info.get('difficulty', 0)}")
            print(f"连接节点数: {mining_info.get('connections', 0)}")
        except Exception as e:
            print(f"[ERROR] 无法获取挖矿信息: {e}")
        
        ssh.close()
        print()
        print("=" * 70)
        print("深度检测完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] 连接失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
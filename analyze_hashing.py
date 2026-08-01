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
    print("分析区块验证逻辑")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看代理中区块验证的关键代码 ---")
        output, _ = execute_command(ssh, "sed -n '600,660p' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 2. 查看原始版本的验证代码 ---")
        output, _ = execute_command(ssh, "sed -n '600,660p' /root/stratum-proxy.js")
        print(output)
        
        print("\n--- 3. 查看区块38的详细信息（成功出块的示例） ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblock\",\"params\":[\"eb6dbefb83642027e1387065666c85275169c918913568f214f22fe85b055479\"],\"id\":1}'")
        print(output)
        
        print("\n--- 4. 查看当前区块模板中的target和bits ---")
        output, _ = execute_command(ssh, "curl -s -u rcpuuser:rcpupassword http://127.0.0.1:6988/ -d '{\"method\":\"getblocktemplate\",\"params\":[{\"rules\":[\"segwit\"]}],\"id\":1}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('target:', d['result']['target']); print('bits:', d['result']['bits']); print('height:', d['result']['height'])\"")
        print(output)
        
        print("\n--- 5. 手动计算难度 ---")
        output, _ = execute_command(ssh, "python3 << 'EOF'\ntarget = \"00000fffff000000000000000000000000000000000000000000000000000000\"\nbits = \"1e0fffff\"\n\n# 计算难度\ntarget_int = int(target, 16)\nmax_target = int(\"ffff\" + \"00\" * 28, 16)\ndifficulty = max_target / target_int\nprint(f\"目标难度: {difficulty:.2f}\")\n\n# 解析bits\nexponent = int(bits[:2], 16)\nmantissa = int(bits[2:], 16)\nprint(f\"指数: {exponent}, 尾数: {mantissa}\")\n\n# 从bits计算target\nbits_target = mantissa * (2 ** (8 * (exponent - 3)))\nbits_target_hex = format(bits_target, '064x')\nprint(f\"从bits计算的target: {bits_target_hex}\")\nEOF")
        print(output)
        
        ssh.close()
        
        print("\n" + "=" * 70)
        print("分析完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
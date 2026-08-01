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
    print("修复Segwit禁用问题 - 移除coinbase交易中的witness数据")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看当前代码中的coinbase构建部分 ---")
        output, _ = execute_command(ssh, "sed -n '294,313p' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 2. 修复coinbase交易 - 移除witness数据 ---")
        fix_code = '''
function constructCoinbaseTransaction(template, minerAddress, extraNonce1, extraNonce2) {
    const height = template.height;
    const coinbaseValue = template.coinbasevalue || 500000000000;
    
    let heightBytes = [];
    if (height < 0xfd) {
        heightBytes = [height];
    } else if (height <= 0xffff) {
        heightBytes = [0xfd, height & 0xff, (height >> 8) & 0xff];
    } else if (height <= 0xffffffff) {
        heightBytes = [0xfe, height & 0xff, (height >> 8) & 0xff, (height >> 16) & 0xff, (height >> 24) & 0xff];
    }
    
    const scriptSig = Buffer.from(heightBytes);
    const scriptSigLen = scriptSig.length;
    const scriptSigLenHex = scriptSigLen.toString(16).padStart(2, '0');
    
    const scriptPubKey = addressToScriptPubKey(minerAddress);
    
    const valueHex = (coinbaseValue).toString(16).padStart(16, '0');
    const valueLE = valueHex.match(/.{2}/g).reverse().join('');
    
    const txHex = 
        '01000000' +
        '01' +
        '0000000000000000000000000000000000000000000000000000000000000000' +
        'ffffffff' +
        scriptSigLenHex +
        scriptSig.toString('hex') +
        'ffffffff' +
        '01' +
        valueLE +
        (scriptPubKey.length / 2).toString(16).padStart(2, '0') +
        scriptPubKey +
        '00000000';
    
    return txHex;
}
'''
        
        output, _ = execute_command(ssh, "cat > /tmp/fix_coinbase.js << 'EOF'\n" + fix_code + "\nEOF")
        print("修复代码已准备")
        
        print("\n--- 3. 替换constructCoinbaseTransaction函数 ---")
        output, _ = execute_command(ssh, '''
awk -v RS='^$' -v ORS='' '
/function constructCoinbaseTransaction\(template, minerAddress, extraNonce1, extraNonce2\)/ {
    print "function constructCoinbaseTransaction(template, minerAddress, extraNonce1, extraNonce2) {\n    const height = template.height;\n    const coinbaseValue = template.coinbasevalue || 500000000000;\n    \n    let heightBytes = [];\n    if (height < 0xfd) {\n        heightBytes = [height];\n    } else if (height <= 0xffff) {\n        heightBytes = [0xfd, height & 0xff, (height >> 8) & 0xff];\n    } else if (height <= 0xffffffff) {\n        heightBytes = [0xfe, height & 0xff, (height >> 8) & 0xff, (height >> 16) & 0xff, (height >> 24) & 0xff];\n    }\n    \n    const scriptSig = Buffer.from(heightBytes);\n    const scriptSigLen = scriptSig.length;\n    const scriptSigLenHex = scriptSigLen.toString(16).padStart(2, '\\''0'\\'');\n    \n    const scriptPubKey = addressToScriptPubKey(minerAddress);\n    \n    const valueHex = (coinbaseValue).toString(16).padStart(16, '\\''0'\\'');\n    const valueLE = valueHex.match(/.{2}/g).reverse().join('\\''\\'');\n    \n    const txHex = \n        '\\''01000000'\\'' +\n        '\\''01'\\'' +\n        '\\''0000000000000000000000000000000000000000000000000000000000000000'\\'' +\n        '\\''ffffffff'\\'' +\n        scriptSigLenHex +\n        scriptSig.toString('\\''hex'\\'') +\n        '\\''ffffffff'\\'' +\n        '\\''01'\\'' +\n        valueLE +\n        (scriptPubKey.length / 2).toString(16).padStart(2, '\\''0'\\'') +\n        scriptPubKey +\n        '\\''00000000'\\'';\n    \n    return txHex;\n}\n'
    next
}
1
' /root/stratum-proxy-fixed.js > /tmp/fixed_proxy.js && mv /tmp/fixed_proxy.js /root/stratum-proxy-fixed.js
''')
        print("替换完成")
        
        print("\n--- 4. 同样修复submitBlockToNode中的coinbase构建 ---")
        output, _ = execute_command(ssh, '''
awk -v RS='^$' -v ORS='' '
/coinbaseTx = / {
    if (match($0, /coinbaseTx = \\n[\\s\\S]*?00000000\\n\\s*\\}/)) {
        print "coinbaseTx = \\\n            \\'01000000\\' +\\n            \\'01\\' +\\n            \\'00000000000000000000000000000000000000000000000000000000000000000\\' +\\n            \\'ffffffff\\' +\\n            scriptSigLenHex +\\n            scriptSig.toString(\\'hex\\') +\\n            \\'ffffffff\\' +\\n            \\'01\\' +\\n            valueLE +\\n            (scriptPubKey.length / 2).toString(16).padStart(2, \\'0\\') +\\n            scriptPubKey +\\n            \\'00000000\\';"
        next
    }
}
1
' /root/stratum-proxy-fixed.js > /tmp/fixed_proxy2.js && mv /tmp/fixed_proxy2.js /root/stratum-proxy-fixed.js
''')
        print("修复完成")
        
        print("\n--- 5. 验证修复后的代码 ---")
        output, _ = execute_command(ssh, "sed -n '294,313p' /root/stratum-proxy-fixed.js")
        print(output)
        
        print("\n--- 6. 重启代理 ---")
        output, _ = execute_command(ssh, "pkill -9 -f stratum-proxy-fixed.js; sleep 2; cd /root && nohup node stratum-proxy-fixed.js > /var/log/stratum-proxy.log 2>&1 &")
        print("代理已重启")
        
        print("\n--- 7. 等待3秒后检查进程 ---")
        output, _ = execute_command(ssh, "sleep 3 && ps aux | grep stratum-proxy-fixed | grep -v grep")
        print(output if output else "进程未启动")
        
        print("\n--- 8. 查看最新日志 ---")
        output, _ = execute_command(ssh, "tail -10 /var/log/stratum-proxy.log")
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
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
    print("直接修复stratum-proxy-fixed.js")
    print("=" * 70)
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, password, timeout=30)
        
        print("\n--- 1. 查看当前完整文件 ---")
        output, _ = execute_command(ssh, "cat /root/stratum-proxy-fixed.js")
        file_content = output
        
        print("\n--- 2. 修复constructCoinbaseTransaction函数 ---")
        
        old_func = '''function constructCoinbaseTransaction(template, minerAddress, extraNonce1, extraNonce2) {
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
    
    const witnessCommitment = '6a24aa21a9ede2f61c3f71d1defd3fa999dfa36953755c690689799962b48bebd836974e8cf9';
    
    const txHex = 
        '01000000' +
        '0001' +
        '01' +
        '0000000000000000000000000000000000000000000000000000000000000000' +
        'ffffffff' +
        scriptSigLenHex +
        scriptSig.toString('hex') +
        'ffffffff' +
        '02' +
        valueLE +
        (scriptPubKey.length / 2).toString(16).padStart(2, '0') +
        scriptPubKey +
        '0000000000000000' +
        '26' +
        witnessCommitment +
        '01' +
        '20' +
        '0000000000000000000000000000000000000000000000000000000000000000' +
        '00000000';
    
    return txHex;
}'''

        new_func = '''function constructCoinbaseTransaction(template, minerAddress, extraNonce1, extraNonce2) {
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
}'''

        file_content = file_content.replace(old_func, new_func)
        print("constructCoinbaseTransaction已修复")
        
        print("\n--- 3. 修复submitBlockToNode中的coinbase构建 ---")
        old_coinbase = '''            coinbaseTx = 
                '01000000' +
                '0001' +
                '01' +
                '0000000000000000000000000000000000000000000000000000000000000000' +
                'ffffffff' +
                scriptSigLenHex +
                scriptSig.toString('hex') +
                'ffffffff' +
                '02' +
                valueLE +
                (scriptPubKey.length / 2).toString(16).padStart(2, '0') +
                scriptPubKey +
                '0000000000000000' +
                '26' +
                witnessCommitment +
                '01' +
                '20' +
                '0000000000000000000000000000000000000000000000000000000000000000' +
                '00000000';'''

        new_coinbase = '''            coinbaseTx = 
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
                '00000000';'''

        file_content = file_content.replace(old_coinbase, new_coinbase)
        print("submitBlockToNode中的coinbase已修复")
        
        print("\n--- 4. 写入修复后的文件 ---")
        stdin, stdout, stderr = ssh.exec_command("cat > /root/stratum-proxy-fixed.js")
        stdin.write(file_content)
        stdin.flush()
        stdin.channel.shutdown_write()
        print("文件写入完成")
        
        print("\n--- 5. 验证修复 ---")
        output, _ = execute_command(ssh, "grep -n 'witnessCommitment' /root/stratum-proxy-fixed.js")
        if output:
            print(f"警告：仍然存在witnessCommitment引用: {output}")
        else:
            print("witnessCommitment已移除")
        
        output, _ = execute_command(ssh, "grep -n \"'0001'\" /root/stratum-proxy-fixed.js")
        if output:
            print(f"警告：仍然存在segwit版本号: {output}")
        else:
            print("segwit版本号已移除")
        
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
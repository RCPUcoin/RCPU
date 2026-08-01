import paramiko
import os
import tempfile

src_host = '103.74.192.168'
src_port = 45148
src_user = 'root'
src_pass = '13559714383cQ@'

dst_host = '38.147.171.29'
dst_port = 47005
dst_user = 'root'
dst_pass = '13559714383cQ@'

def execute_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode('utf-8', errors='ignore')
    error = stderr.read().decode('utf-8', errors='ignore')
    return output, error

def main():
    print("=" * 70)
    print("步骤3: 传输钱包数据到目标服务器")
    print("=" * 70)
    
    try:
        print("\n--- 1. 连接源服务器打包钱包数据 ---")
        src_ssh = paramiko.SSHClient()
        src_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        src_ssh.connect(src_host, src_port, src_user, src_pass, timeout=30)
        
        output, _ = execute_command(src_ssh, "cd /root/.rcpu && tar -czf wallet_backup.tar.gz rcpu/wallets/ bitcoin.conf rcpu.conf")
        print("打包完成")
        
        output, _ = execute_command(src_ssh, "ls -la /root/.rcpu/wallet_backup.tar.gz")
        print(output)
        
        print("\n--- 2. 传输钱包文件到本地 ---")
        local_path = os.path.join(tempfile.gettempdir(), 'wallet_backup.tar.gz')
        print(f"本地临时路径: {local_path}")
        
        sftp = src_ssh.open_sftp()
        sftp.get('/root/.rcpu/wallet_backup.tar.gz', local_path)
        sftp.close()
        print(f"已下载到本地: {local_path}")
        print(f"文件大小: {os.path.getsize(local_path)} bytes")
        
        src_ssh.close()
        
        print("\n--- 3. 上传到目标服务器 ---")
        dst_ssh = paramiko.SSHClient()
        dst_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        dst_ssh.connect(dst_host, dst_port, dst_user, dst_pass, timeout=30)
        
        sftp = dst_ssh.open_sftp()
        sftp.put(local_path, '/root/.rcpu/wallet_backup.tar.gz')
        sftp.close()
        print("已上传到目标服务器")
        
        output, _ = execute_command(dst_ssh, "ls -la /root/.rcpu/wallet_backup.tar.gz")
        print(output)
        
        print("\n--- 4. 解压钱包数据 ---")
        output, _ = execute_command(dst_ssh, "cd /root/.rcpu && tar -xzf wallet_backup.tar.gz")
        print("解压完成")
        
        output, _ = execute_command(dst_ssh, "ls -la /root/.rcpu/rcpu/wallets/")
        print(output)
        
        print("\n--- 5. 查看配置文件 ---")
        output, _ = execute_command(dst_ssh, "cat /root/.rcpu/bitcoin.conf")
        print(output)
        
        dst_ssh.close()
        
        os.remove(local_path)
        
        print("\n" + "=" * 70)
        print("步骤3完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
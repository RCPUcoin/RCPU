import paramiko
import time

HOST = '103.74.192.168'
PORT = 45148
USER = 'root'
PASSWORD = '13559714383cQ@'

LOCAL_FILE = r'c:\Users\92763\Desktop\RCPU主链\RCPU\stratum-proxy-pool.js'
REMOTE_FILE = '/root/stratum-proxy-pool.js'

def ssh_exec(client, cmd, timeout=30):
    print(f"Executing: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    stdout.channel.set_combine_stderr(True)
    output = stdout.read().decode('utf-8')
    print(f"Output: {output[:2000]}")
    return output

def main():
    print("Connecting to server...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    
    try:
        print("\n=== Step 1: Stop existing pool processes ===")
        ssh_exec(client, "pkill -f stratum-proxy-pool.js || true")
        time.sleep(2)
        
        print("\n=== Step 2: Upload fixed pool code ===")
        sftp = client.open_sftp()
        sftp.put(LOCAL_FILE, REMOTE_FILE)
        sftp.close()
        print("File uploaded successfully")
        
        print("\n=== Step 3: Verify file upload ===")
        ssh_exec(client, "ls -la /root/stratum-proxy-pool.js")
        ssh_exec(client, "head -30 /root/stratum-proxy-pool.js")
        
        print("\n=== Step 4: Start pool in background ===")
        ssh_exec(client, "cd /root && nohup node stratum-proxy-pool.js > pool.log 2>&1 &")
        time.sleep(3)
        
        print("\n=== Step 5: Check pool status ===")
        ssh_exec(client, "ps aux | grep node")
        ssh_exec(client, "ss -tlnp | grep 808")
        ssh_exec(client, "tail -20 /root/pool.log")
        
        print("\n=== Step 6: Check node status ===")
        ssh_exec(client, "curl -s http://127.0.0.1:6988 -u rcpuuser:rcpupassword -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"method\":\"getblockcount\",\"params\":[],\"id\":1}'")
        
    finally:
        client.close()
        print("\nConnection closed.")

if __name__ == "__main__":
    main()
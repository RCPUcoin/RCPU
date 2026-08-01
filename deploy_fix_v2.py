import paramiko
import time

HOST = '103.74.192.168'
PORT = 45148
USER = 'root'
PASSWORD = '13559714383cQ@'

LOCAL_FILE = r'c:\Users\92763\Desktop\RCPU主链\RCPU\stratum-proxy-pool.js'
REMOTE_FILE = '/root/stratum-proxy-pool.js'

def ssh_exec(client, cmd, timeout=15):
    print(f"  > {cmd}")
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        stdout.channel.set_combine_stderr(True)
        output = stdout.read().decode('utf-8').strip()
        if output:
            print(f"  {output}")
        return output
    except Exception as e:
        print(f"  ERROR: {e}")
        return str(e)

def main():
    print("Connecting to server...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    
    try:
        print("\n=== Stop pool ===")
        ssh_exec(client, "pkill -f stratum-proxy-pool.js")
        time.sleep(2)
        
        print("\n=== Upload fixed code ===")
        sftp = client.open_sftp()
        sftp.put(LOCAL_FILE, REMOTE_FILE)
        sftp.close()
        print("  File uploaded")
        
        print("\n=== Start pool ===")
        ssh_exec(client, "cd /root && nohup node stratum-proxy-pool.js > pool.log 2>&1 &")
        time.sleep(5)
        
        print("\n=== Check status ===")
        ssh_exec(client, "ps aux | grep -v grep | grep 'node stratum'")
        ssh_exec(client, "ss -tlnp | grep 808")
        
        print("\n=== Pool logs ===")
        ssh_exec(client, "tail -30 /root/pool.log")
        
    finally:
        client.close()
        print("\nDone")

if __name__ == "__main__":
    main()

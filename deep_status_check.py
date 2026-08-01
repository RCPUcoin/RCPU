import paramiko
import json

HOST = '103.74.192.168'
PORT = 45148
USER = 'root'
PASSWORD = '13559714383cQ@'

def ssh_exec(client, cmd, timeout=30):
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    stdout.channel.set_combine_stderr(True)
    return stdout.read().decode('utf-8', errors='ignore')

def main():
    print("Connecting to server...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)

    try:
        print("\n=== 检查 rcpu-cli 路径 ===")
        print(ssh_exec(client, "which rcpu-cli; ls -la /usr/local/bin/rcpu* 2>/dev/null; ls -la /root/rcpu* 2>/dev/null; find / -name 'rcpu-cli' -type f 2>/dev/null | head -5").strip())

        print("\n=== 节点进程 ===")
        print(ssh_exec(client, "ps aux | grep -v grep | grep -iE 'rcpu|bitcoind|coind'").strip())

        print("\n=== 直接 RPC 调用 getblockcount ===")
        rpc_cmd = "curl -s -u rcpuuser:rcpupassword -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getblockcount\",\"params\":[]}' http://127.0.0.1:6988"
        result = ssh_exec(client, rpc_cmd).strip()
        print(result[:500])

        print("\n=== getmininginfo ===")
        rpc_cmd2 = "curl -s -u rcpuuser:rcpupassword -X POST -H 'Content-Type: application/json' -d '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"getmininginfo\",\"params\":[]}' http://127.0.0.1:6988"
        result2 = ssh_exec(client, rpc_cmd2).strip()
        print(result2[:800])

        print("\n=== 最近100行矿池日志 ===")
        print(ssh_exec(client, "tail -100 /root/pool.log").strip())

        print("\n=== 所有 share 提交记录 ===")
        print(ssh_exec(client, "grep -E 'Stratum submit|share|BLOCK' /root/pool.log | tail -40").strip())

    finally:
        client.close()
        print("\nDone")

if __name__ == "__main__":
    main()

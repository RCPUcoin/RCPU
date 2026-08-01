import paramiko

HOST = '103.74.192.168'
PORT = 45148
USER = 'root'
PASSWORD = '13559714383cQ@'

def ssh_exec(client, cmd, timeout=15):
    try:
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        stdout.channel.set_combine_stderr(True)
        output = stdout.read().decode('utf-8')
        return output.strip()
    except Exception as e:
        return str(e)

def main():
    print("Connecting to server...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    
    try:
        print("=== 区块高度 ===")
        print(ssh_exec(client, "rcpu-cli getblockcount 2>/dev/null"))
        
        print("\n=== 矿池日志最后 80 行 ===")
        print(ssh_exec(client, "tail -80 /root/pool.log"))
        
        print("\n=== 检查 BLOCK 相关日志 ===")
        print(ssh_exec(client, "grep -i 'block' /root/pool.log | tail -20"))
        
        print("\n=== 检查 rejected/error 日志 ===")
        print(ssh_exec(client, "grep -iE 'reject|error' /root/pool.log | tail -20"))
        
        print("\n=== GBT 返回关键字段 ===")
        gbt_cmd = "rcpu-cli getblocktemplate '{\"rules\":[\"segwit\"]}' 2>/dev/null"
        gbt_raw = ssh_exec(client, gbt_cmd)
        if gbt_raw and gbt_raw.startswith('{'):
            import json
            try:
                d = json.loads(gbt_raw)
                print("height:", d.get('height'))
                print("curtime:", d.get('curtime'))
                print("previousblockhash:", str(d.get('previousblockhash',''))[:48])
                print("default_witness_commitment:", str(d.get('default_witness_commitment',''))[:48])
                print("bits:", d.get('bits'))
                print("target:", str(d.get('target',''))[:48])
                print("coinbasevalue:", d.get('coinbasevalue'))
                print("version:", d.get('version'))
                # Check for seed/randomx/epoch fields
                for k, v in d.items():
                    kl = k.lower()
                    if 'seed' in kl or 'random' in kl or 'epoch' in kl:
                        print(f"  {k}: {str(v)[:64]}")
                # Print all keys
                print("All keys:", list(d.keys()))
            except json.JSONDecodeError as e:
                print("JSON parse error:", e)
                print("Raw (first 500 chars):", gbt_raw[:500])
        else:
            print("GBT raw:", gbt_raw[:500] if gbt_raw else "(empty)")
        
    finally:
        client.close()
        print("\nDone")

if __name__ == "__main__":
    main()

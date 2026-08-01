import paramiko

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>RCPU矿池 - RCPU Pool</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 50%, #16213e 100%); color: #fff; min-height: 100vh; }
        
        .logo-container { text-align: center; padding: 30px 0; }
        .logo { width: 120px; height: 120px; margin: 0 auto; position: relative; }
        .logo-ring { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border-radius: 50%; border: 3px solid #ffd700; box-shadow: 0 0 20px rgba(255,215,0,0.4), inset 0 0 10px rgba(255,215,0,0.2); }
        .logo-inner { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 85px; height: 85px; border-radius: 50%; background: linear-gradient(135deg, #ffd700 0%, #ffb700 100%); display: flex; align-items: center; justify-content: center; }
        .logo-r { font-size: 50px; font-weight: 900; color: #000; font-family: Arial, sans-serif; letter-spacing: -2px; }
        .logo-dots { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 100%; height: 100%; }
        .logo-dot { position: absolute; width: 4px; height: 4px; background: #ffd700; border-radius: 50%; opacity: 0.6; }
        .logo-dot:nth-child(1) { top: 8px; left: 50%; transform: translateX(-50%); }
        .logo-dot:nth-child(2) { bottom: 8px; left: 50%; transform: translateX(-50%); }
        .logo-dot:nth-child(3) { left: 8px; top: 50%; transform: translateY(-50%); }
        .logo-dot:nth-child(4) { right: 8px; top: 50%; transform: translateY(-50%); }
        .logo-container h1 { margin-top: 15px; font-size: 36px; color: #ffd700; text-shadow: 0 0 20px rgba(255, 215, 0, 0.5); }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 20px 5%; max-width: 1200px; margin: 0 auto; }
        .stat-card { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; text-align: center; border: 1px solid rgba(255,215,0,0.2); }
        .stat-card .label { font-size: 14px; color: #aaa; margin-bottom: 10px; }
        .stat-card .value { font-size: 28px; font-weight: bold; color: #ffd700; }
        
        .section { max-width: 1200px; margin: 40px auto; padding: 0 5%; }
        .section-title { font-size: 24px; color: #ffd700; margin-bottom: 20px; border-left: 4px solid #ffd700; padding-left: 15px; }
        
        .connection-info { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 30px; border: 1px solid rgba(255,215,0,0.2); }
        .connection-info h3 { color: #ffd700; margin-bottom: 20px; }
        
        .port-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .port-table th, .port-table td { padding: 15px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
        .port-table th { color: #ffd700; background: rgba(255,215,0,0.1); }
        
        .code-block { background: #1a1a2e; border-radius: 10px; padding: 20px; font-family: 'Courier New', monospace; font-size: 14px; margin: 15px 0; overflow-x: auto; border: 1px solid rgba(255,215,0,0.2); }
        
        .footer { text-align: center; padding: 40px; color: #666; font-size: 14px; margin-top: 60px; }
        
        .btn { display: inline-block; padding: 10px 25px; background: linear-gradient(135deg, #ffd700, #ffb700); color: #000; text-decoration: none; border-radius: 25px; font-weight: bold; transition: all 0.3s; }
        .btn:hover { transform: scale(1.05); box-shadow: 0 0 20px rgba(255,215,0,0.5); }
        
        .miner-section { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        .miner-box { background: rgba(255,255,255,0.05); border-radius: 15px; padding: 25px; border: 1px solid rgba(255,215,0,0.2); }
        .miner-box h4 { color: #ffd700; margin-bottom: 15px; }
        
        @media (max-width: 768px) {
            .miner-section { grid-template-columns: 1fr; }
            .logo-container h1 { font-size: 24px; }
        }
    </style>
</head>
<body>
    <div class="logo-container">
        <div class="logo">
            <div class="logo-ring"></div>
            <div class="logo-inner">
                <span class="logo-r">R</span>
            </div>
            <div class="logo-dots">
                <div class="logo-dot"></div>
                <div class="logo-dot"></div>
                <div class="logo-dot"></div>
                <div class="logo-dot"></div>
            </div>
        </div>
        <h1>RCPU矿池</h1>
        <p style="color: #aaa; margin-top: 10px;">RCPU Mining Pool</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">区块高度</div>
            <div class="value" id="blockHeight">--</div>
        </div>
        <div class="stat-card">
            <div class="label">网络难度</div>
            <div class="value" id="difficulty">--</div>
        </div>
        <div class="stat-card">
            <div class="label">全网算力</div>
            <div class="value" id="hashrate">--</div>
        </div>
        <div class="stat-card">
            <div class="label">连接矿工</div>
            <div class="value" id="miners">--</div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">矿池连接</div>
        <div class="connection-info">
            <h3>矿池地址</h3>
            <div class="code-block">stratum+tcp://103.74.192.168:8080</div>
            
            <table class="port-table">
                <tr><th>端口</th><th>类型</th><th>说明</th></tr>
                <tr><td>8080</td><td>共享池</td><td>所有矿工共享，按算力分配奖励</td></tr>
                <tr><td>8081</td><td>独享池</td><td>示例: rcpu1qxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx</td></tr>
                <tr><td>8082</td><td>独享池</td><td>示例: rcpu1qyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy</td></tr>
            </table>
        </div>
    </div>

    <div class="section">
        <div class="section-title">挖矿配置</div>
        <div class="miner-section">
            <div class="miner-box">
                <h4>XMRig 配置</h4>
                <div class="code-block">{
  "autosave": true,
  "cpu": true,
  "opencl": false,
  "cuda": false,
  "pools": [
    {
      "url": "103.74.192.168:8080",
      "user": "你的RCPU钱包地址",
      "pass": "x",
      "algorithm": "randomx",
      "coin": null
    }
  ]
}</div>
            </div>
            <div class="miner-box">
                <h4>Windows 批处理</h4>
                <div class="code-block">@echo off
minerd -a randomx -o stratum+tcp://103.74.192.168:8080 -u 你的钱包地址 -p x -t 12</div>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">挖矿软件下载</div>
        <div class="connection-info">
            <p style="margin-bottom: 20px;">下载挖矿软件，支持Windows系统：</p>
            <div style="display: flex; gap: 20px; flex-wrap: wrap;">
                <a href="/cpuminer-rcpu-3.0.0.tar.gz" class="btn">下载挖矿软件</a>
            </div>
        </div>
    </div>

    <div class="section">
        <div class="section-title">奖励规则</div>
        <div class="connection-info">
            <ul style="margin-left: 20px; line-height: 2;">
                <li><strong>矿池费率:</strong> 0%</li>
                <li><strong>奖励模式:</strong> PPS (按算力比例分配)</li>
                <li><strong>最低支付:</strong> 100 RCPU</li>
                <li><strong>区块奖励:</strong> 5000 RCPU/块</li>
            </ul>
        </div>
    </div>

    <div class="footer">
        <p>RCPU Mining Pool - 2026</p>
        <p style="margin-top: 10px; color: #444;">Powered by RCPU Blockchain</p>
    </div>

    <script>
        function fetchStats() {
            fetch('/api/stats')
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.height !== undefined) {
                    document.getElementById('blockHeight').textContent = data.height;
                }
                if (data.difficulty !== undefined) {
                    document.getElementById('difficulty').textContent = data.difficulty;
                }
                if (data.hashrate !== undefined) {
                    document.getElementById('hashrate').textContent = data.hashrate;
                }
                if (data.miners !== undefined) {
                    document.getElementById('miners').textContent = data.miners;
                }
            })
            .catch(function(e) {
                console.error('Failed to fetch stats:', e);
            });
        }
        
        fetchStats();
        setInterval(fetchStats, 30000);
    </script>
</body>
</html>
'''

print("=== 上传修复后的页面 ===")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=30)
    
    print("\n上传新页面...")
    stdin, stdout, stderr = ssh.exec_command('cat > /var/www/rcpupool/index.html << "EOF"\n' + html_content + '\nEOF')
    stdout.channel.recv_exit_status()
    print("页面上传完成")
    
    print("\n测试页面加载...")
    stdin, stdout, stderr = ssh.exec_command('curl -s https://rcpupool.asia/ | head -20')
    print(stdout.read().decode())
    
    ssh.close()
    
    print("\n完成!")
    
except Exception as e:
    print("失败: " + str(e))

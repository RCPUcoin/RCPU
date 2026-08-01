import paramiko

host = '103.74.192.168'
port = 45148
user = 'root'
password = '13559714383cQ@'

api_server_code = '''const http = require('http');
const crypto = require('crypto');

const RPC_HOST = '127.0.0.1';
const RPC_PORT = 6988;
const API_PORT = 3001;

let chainStats = {
    height: 0,
    difficulty: 0,
    hashrate: '0 KH/s',
    miners: 0
};

function makeRpcRequest(method, params) {
    return new Promise((resolve, reject) => {
        const data = JSON.stringify({
            id: Date.now(),
            jsonrpc: '2.0',
            method: method,
            params: params
        });
        
        const auth = Buffer.from('rcpuuser:rcpupassword').toString('base64');
        
        const options = {
            hostname: RPC_HOST,
            port: RPC_PORT,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data),
                'Authorization': "Basic " + auth
            }
        };
        
        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => { body += chunk; });
            res.on('end', () => {
                try {
                    const parsed = JSON.parse(body);
                    if (parsed.error) {
                        reject(new Error(parsed.error.message || 'RPC error'));
                    } else {
                        resolve(parsed.result);
                    }
                } catch (e) {
                    reject(new Error('Invalid JSON'));
                }
            });
        });
        
        req.on('error', (e) => reject(e));
        req.write(data);
        req.end();
    });
}

async function updateStats() {
    try {
        const blockCount = await makeRpcRequest('getblockcount', []);
        chainStats.height = blockCount;
        
        const miningInfo = await makeRpcRequest('getmininginfo', []);
        if (miningInfo) {
            chainStats.difficulty = miningInfo.difficulty || 0;
            chainStats.hashrate = formatHashrate(miningInfo.networkhashps || 0);
        }
        
        const peerInfo = await makeRpcRequest('getpeerinfo', []);
        if (peerInfo && Array.isArray(peerInfo)) {
            chainStats.miners = peerInfo.length;
        }
        
        console.log('Updated stats:', chainStats);
    } catch (e) {
        console.log('Failed to update stats:', e.message);
    }
}

function formatHashrate(hashps) {
    if (hashps < 1000) return hashps.toFixed(2) + ' H/s';
    if (hashps < 1000000) return (hashps / 1000).toFixed(2) + ' KH/s';
    if (hashps < 1000000000) return (hashps / 1000000).toFixed(2) + ' MH/s';
    return (hashps / 1000000000).toFixed(2) + ' GH/s';
}

const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Content-Type', 'application/json');
    
    if (req.url === '/api/stats') {
        res.statusCode = 200;
        res.end(JSON.stringify(chainStats));
    } else {
        res.statusCode = 404;
        res.end(JSON.stringify({ error: 'Not found' }));
    }
});

server.listen(API_PORT, () => {
    console.log('API server listening on port', API_PORT);
    updateStats();
});

setInterval(updateStats, 30000);
'''

print("=== 部署API服务并连接链上真实数据 ===")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, port=port, username=user, password=password, timeout=30)
    
    print("\n1. 创建API服务...")
    stdin, stdout, stderr = ssh.exec_command('cat > /root/api-server.js << "EOF"\n' + api_server_code + '\nEOF')
    stdout.channel.recv_exit_status()
    print("API服务代码创建完成")
    
    print("\n2. 启动API服务...")
    stdin, stdout, stderr = ssh.exec_command('pkill -f "node api-server.js" 2>/dev/null; sleep 1')
    stdout.channel.recv_exit_status()
    
    stdin, stdout, stderr = ssh.exec_command('nohup node /root/api-server.js > /root/api.log 2>&1 &')
    stdout.channel.recv_exit_status()
    
    stdin, stdout, stderr = ssh.exec_command('sleep 3 && tail -5 /root/api.log')
    print(stdout.read().decode())
    
    print("\n3. 测试API...")
    stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:3001/api/stats')
    result = stdout.read().decode()
    print("API响应:", result)
    
    print("\n4. 配置nginx反向代理...")
    stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/rcpupool')
    current_config = stdout.read().decode()
    
    if '/api/' not in current_config:
        new_config = current_config.replace('location / {', '''location /api/ {
        proxy_pass http://127.0.0.1:3001/;
    }
    
    location / {''')
        stdin, stdout, stderr = ssh.exec_command('cat > /etc/nginx/sites-available/rcpupool << "EOF"\n' + new_config + '\nEOF')
        stdout.channel.recv_exit_status()
        
        stdin, stdout, stderr = ssh.exec_command('nginx -t')
        test_result = stdout.read().decode() + stderr.read().decode()
        if 'test failed' in test_result:
            print("nginx配置错误:", test_result)
        else:
            print("nginx配置测试通过")
            stdin, stdout, stderr = ssh.exec_command('systemctl reload nginx')
            stdout.channel.recv_exit_status()
            print("nginx已重新加载")
    else:
        print("nginx已配置API代理")
    
    print("\n5. 更新网站前端...")
    stdin, stdout, stderr = ssh.exec_command('cat /var/www/rcpupool/index.html | sed "s|https://rcpu.top/api/stats|/api/stats|g" > /tmp/index_new.html && mv /tmp/index_new.html /var/www/rcpupool/index.html')
    stdout.channel.recv_exit_status()
    print("前端已更新")
    
    print("\n6. 验证网站API调用...")
    stdin, stdout, stderr = ssh.exec_command('curl -s https://rcpupool.asia/api/stats')
    print("网站API响应:", stdout.read().decode())
    
    ssh.close()
    
    print("\n" + "="*60)
    print("API服务部署完成!")
    print("网站统计数据将实时更新")
    print("="*60)
    
except Exception as e:
    print("部署失败: " + str(e))

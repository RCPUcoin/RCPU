#!/usr/bin/env python3
"""
RCPU Pool Log Parser API - Final Version
First scan full log to build ID->address mapping, then scan recent log to get shares
"""
import json
import re
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque

LOG_FILE = '/root/pool.log'
PORT = 8090
MAX_SHARES = 100

shares = deque(maxlen=MAX_SHARES)
stats = {
    'valid': 0, 'invalid': 0, 'blocksFound': 0,
    'blocksSubmitted': 0, 'rpcErrors': 0, 'miners': 0,
    'lastUpdate': 0,
}
miners = {}
miner_id_to_addr = {}

def parse_log():
    global stats, miners, miner_id_to_addr
    
    if not os.path.exists(LOG_FILE):
        return
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            all_lines = f.readlines()
        
        total_lines = len(all_lines)
        
        # Step 1: Scan first 3000 lines (or all) to build ID->address mapping
        scan_lines = all_lines[:min(total_lines, 5000)]  # First 5000 lines build mapping
        
        for line in scan_lines:
            line = line.strip()
            if 'authorized:' in line:
                id_matches = re.findall(r'\[([a-f0-9]+)\]', line)
                miner_id = id_matches[0] if id_matches else 'unknown'
                
                m = re.search(r'authorized:\s*([a-zA-Z0-9]+)', line)
                if m:
                    addr = m.group(1)
                    miner_id_to_addr[miner_id] = addr
        
        # Step 2: Scan last 2000 lines to get shares and stats
        recent_lines = all_lines[-2000:]
        new_shares = []
        
        for line in recent_lines:
            line = line.strip()
            if not line:
                continue
            
            # Parse timestamp
            ts_match = re.match(r'\[(\d{4}-\d{2}-\d{2}T[^\]]+)\]', line)
            ts = ts_match.group(1) if ts_match else ''
            
            # Parse ID
            id_matches = re.findall(r'\[([a-f0-9]+)\]', line)
            miner_id = id_matches[0] if id_matches else 'unknown'
            
            # Parse stats
            if 'Stats:' in line:
                m = re.search(r'valid=(\d+)\s+invalid=(\d+)\s+blocksFound=(\d+)\s+blocksSubmitted=(\d+)\s+rpcErrors=(\d+)\s+miners=(\d+)', line)
                if m:
                    stats['valid'] = int(m.group(1))
                    stats['invalid'] = int(m.group(2))
                    stats['blocksFound'] = int(m.group(3))
                    stats['blocksSubmitted'] = int(m.group(4))
                    stats['rpcErrors'] = int(m.group(5))
                    stats['miners'] = int(m.group(6))
                    stats['lastUpdate'] = time.time()
            
            # Parse valid shares
            if 'share valid#' in line:
                m = re.search(r'share valid#(\d+)\s+cm:(\d+)\s+target:(\d+)\s+ratio_e9:(\d+)\s+(\w+)\s+meetNet=(\w+)\s+hashVer=(\w+)', line)
                if m:
                    share_num = int(m.group(1))
                    cm = int(m.group(2))
                    target = int(m.group(3))
                    ratio = int(m.group(4))
                    
                    difficulty = target / 1e9 if target > 0 else 0
                    addr = miner_id_to_addr.get(miner_id, 'unknown')
                    
                    new_shares.append({
                        'share': share_num,
                        'cm': cm,
                        'target': target,
                        'difficulty': f'{difficulty:.2e}',
                        'ratio': f'{ratio/1e9:.4f}',
                        'status': m.group(5),
                        'meetNet': m.group(6) == 'true',
                        'hashVer': m.group(7),
                        'minerId': miner_id,
                        'minerAddr': addr,
                        'time': ts,
                        'timestamp': time.time(),
                    })
            
            # Parse miner authorization (supplement mapping)
            if 'authorized:' in line:
                m = re.search(r'authorized:\s*([a-zA-Z0-9]+)', line)
                if m:
                    addr = m.group(1)
                    miner_id_to_addr[miner_id] = addr
                    
                    if addr not in miners:
                        miners[addr] = {
                            'address': addr[:10] + '***' + addr[-4:] if len(addr) > 14 else addr,
                            'fullAddress': addr,
                            'minerId': miner_id,
                            'shares': 0,
                            'firstSeen': time.time(),
                            'lastSeen': time.time(),
                        }
                    else:
                        miners[addr]['lastSeen'] = time.time()
        
        # Update shares list
        if new_shares:
            existing_share_nums = {s['share'] for s in shares}
            for s in new_shares:
                if s['share'] not in existing_share_nums:
                    shares.append(s)
                    existing_share_nums.add(s['share'])
            
            # Update miner share count
            for s in new_shares:
                addr = s.get('minerAddr', 'unknown')
                if addr in miners:
                    miners[addr]['shares'] += 1
                elif addr != 'unknown':
                    miners[addr] = {
                        'address': addr[:10] + '***' + addr[-4:] if len(addr) > 14 else addr,
                        'fullAddress': addr,
                        'minerId': s.get('minerId', ''),
                        'shares': 1,
                        'firstSeen': time.time(),
                        'lastSeen': time.time(),
                    }
                    
    except Exception as e:
        pass

class PoolAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
    
    def do_GET(self):
        parse_log()
        
        if self.path == '/api/stats':
            now = time.time()
            active_miners = [v for v in miners.values() if now - v['lastSeen'] < 300]
            
            data = {
                'validShares': stats['valid'],
                'invalidShares': stats['invalid'],
                'blocksFound': stats['blocksFound'],
                'blocksSubmitted': stats['blocksSubmitted'],
                'rpcErrors': stats['rpcErrors'],
                'totalMiners': stats['miners'],
                'activeMiners': len(active_miners),
                'lastUpdate': stats['lastUpdate'],
                'updateTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now)),
            }
            
            self._send_json(data)
        
        elif self.path == '/api/shares':
            share_list = list(shares)
            share_list.reverse()
            
            self._send_json(share_list[:50])
        
        elif self.path == '/api/miners':
            now = time.time()
            miner_list = []
            for addr, info in miners.items():
                miner_list.append({
                    'address': info['address'],
                    'fullAddress': info['fullAddress'],
                    'shares': info['shares'],
                    'active': now - info['lastSeen'] < 300,
                    'lastSeen': time.strftime('%H:%M:%S', time.localtime(info['lastSeen'])),
                })
            
            self._send_json(miner_list)
        
        elif self.path == '/api/all':
            now = time.time()
            active_miners = [v for v in miners.values() if now - v['lastSeen'] < 300]
            
            data = {
                'stats': {
                    'validShares': stats['valid'],
                    'invalidShares': stats['invalid'],
                    'blocksFound': stats['blocksFound'],
                    'totalMiners': stats['miners'],
                    'activeMiners': len(active_miners),
                },
                'shares': list(shares)[-20:],
                'miners': list(miners.values()),
            }
            
            self._send_json(data)
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def _send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

if __name__ == '__main__':
    print(f"RCPU Pool Log API running on port {PORT}")
    server = HTTPServer(('0.0.0.0', PORT), PoolAPIHandler)
    server.serve_forever()

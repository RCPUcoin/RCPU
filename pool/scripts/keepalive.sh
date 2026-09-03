# SSH Keepalive - Output timestamp every 10 seconds
while true; do
    echo -e "\r\033[K[$(date '+%H:%M:%S')] Connection alive..."
    sleep 10
done
EOF && chmod +x /root/keepalive.sh

@echo off
cd /d "%~dp0"

echo ============================================
echo      RCPU 挖矿启动脚本
echo ============================================
echo 连接节点: 103.74.192.168:6988
echo 算法: RandomX (rx/0)
echo ============================================

xmrig.exe --url http://103.74.192.168:6988 --user rcpuuser --pass rcpupassword --algo rx/0 --daemon --keepalive --threads=4

pause

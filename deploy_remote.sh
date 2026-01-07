#!/bin/bash
# 快速部署到远程服务器脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 服务器配置
SERVER_IP="101.34.152.109"
SSH_KEY="001.pem"
SERVER_PATH="/opt/incomestreamai"

echo -e "${BLUE}🚀 快速部署到远程服务器${NC}"
echo "=================================="

# 1. 同步文件
echo -e "${BLUE}📤 同步文件到服务器...${NC}"

# 同步app.py
scp -i "$SSH_KEY" app.py root@"$SERVER_IP":"$SERVER_PATH"/

# 同步models.py
scp -i "$SSH_KEY" models.py root@"$SERVER_IP":"$SERVER_PATH"/

# 同步templates
echo -e "${BLUE}📤 同步模板文件...${NC}"
rsync -avz -e "ssh -i $SSH_KEY" --exclude='._*' templates/ root@"$SERVER_IP":"$SERVER_PATH"/templates/

echo -e "${GREEN}✅ 文件同步完成${NC}"

# 2. 重启应用
echo -e "${BLUE}🔄 重启应用...${NC}"
ssh -i "$SSH_KEY" root@"$SERVER_IP" << 'ENDSSH'
cd /opt/incomestreamai

# 停止旧进程
pkill -f "python.*main.py" || true
sleep 2

# 启动新进程
nohup python3 main.py > app.log 2>&1 &
sleep 3

# 检查状态
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ 应用启动成功"
    echo "📊 进程信息:"
    ps aux | grep "python.*main.py" | grep -v grep
else
    echo "❌ 应用启动失败"
    tail -20 app.log
    exit 1
fi
ENDSSH

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 部署成功！${NC}"
    echo ""
    echo "🌐 访问地址: http://$SERVER_IP"
    echo "🔑 管理员账号: 18302196515"
    echo "📝 查看日志: ssh -i $SSH_KEY root@$SERVER_IP 'tail -f /opt/incomestreamai/app.log'"
else
    echo -e "${RED}❌ 部署失败${NC}"
    exit 1
fi

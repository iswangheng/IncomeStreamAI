#!/bin/bash
# 快速部署更新脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}📦 准备部署文件...${NC}"
echo -e "${BLUE}==================================${NC}"

# 创建临时打包文件
echo "正在打包更新文件..."

# 只打包修改的文件
tar -czf update_files.tar.gz \
    app.py \
    models.py \
    templates/history_apple.html \
    HISTORY_PAGE_UPGRADE.md \
    QUICK_VIEW_GUIDE.md \
    2>/dev/null

if [ ! -f "update_files.tar.gz" ]; then
    echo "❌ 打包失败"
    exit 1
fi

echo -e "${GREEN}✅ 打包完成${NC}"
echo ""
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}📤 上传到远程服务器...${NC}"
echo -e "${BLUE}==================================${NC}"

# 上传到服务器
scp -i 001.pem -o StrictHostKeyChecking=no \
    update_files.tar.gz \
    root@101.34.152.109:/tmp/

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 上传完成${NC}"
else
    echo "❌ 上传失败"
    exit 1
fi

echo ""
echo -e "${BLUE}==================================${NC}"
echo -e "${BLUE}🔧 在远程服务器上安装更新...${NC}"
echo -e "${BLUE}==================================${NC}"

# 在远程服务器上执行更新
ssh -i 001.pem -o StrictHostKeyChecking=no root@101.34.152.109 << 'EOF'
cd /opt/incomestreamai

echo "备份当前文件..."
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S)
cp models.py models.py.backup.$(date +%Y%m%d_%H%M%S)
cp templates/history_apple.html templates/history_apple.html.backup.$(date +%Y%m%d_%H%M%S)

echo "解压更新文件..."
tar -xzf /tmp/update_files.tar.gz -C /opt/incomestreamai/

echo "清理临时文件..."
rm -f /tmp/update_files.tar.gz

echo "重启应用..."
pkill -f "python.*main.py" || true
sleep 2
nohup python3 main.py > app.log 2>&1 &
sleep 3

echo "检查应用状态..."
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ 应用重启成功"
    echo ""
    echo "🌐 应用地址: http://101.34.152.109"
    echo "📝 查看日志: tail -f /opt/incomestreamai/app.log"
else
    echo "❌ 应用启动失败"
    echo "查看错误日志:"
    tail -30 /opt/incomestreamai/app.log
    exit 1
fi
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}==================================${NC}"
    echo -e "${GREEN}✅ 部署成功完成！${NC}"
    echo -e "${GREEN}==================================${NC}"
    echo ""
    echo "🌐 线上应用地址: http://101.34.152.109"
    echo "🔑 管理员账号: 18302196515"
    
    # 清理本地临时文件
    rm -f update_files.tar.gz
else
    echo ""
    echo "❌ 部署失败"
    exit 1
fi

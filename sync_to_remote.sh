#!/bin/bash
# 本地到远程服务器同步脚本

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 服务器配置
SERVER_IP="101.34.152.109"
SSH_KEY="001.pem"
SERVER_PATH="/opt/incomestreamai"

# 检查必要文件
check_prerequisites() {
    log_info "检查同步前置条件..."

    # 检查SSH密钥
    if [ ! -f "$SSH_KEY" ]; then
        log_error "SSH密钥文件 $SSH_KEY 不存在"
        exit 1
    fi

    # 检查Git仓库
    if [ ! -d ".git" ]; then
        log_error "当前目录不是Git仓库"
        exit 1
    fi

    log_success "前置条件检查完成"
}

# Git 提交和推送
sync_to_git() {
    log_info "同步代码到 Git..."

    # 检查是否有未提交的更改
    if [ -n "$(git status --porcelain)" ]; then
        log_info "发现未提交的更改，正在提交..."

        # 添加所有更改
        git add .

        # 提交（使用默认消息或让用户输入）
        read -p "请输入提交消息 (默认: 自动同步): " commit_msg
        commit_msg=${commit_msg:-"自动同步 $(date '+%Y-%m-%d %H:%M:%S')"}

        git commit -m "$commit_msg"

        # 推送到远程
        git push origin main

        log_success "代码已推送到 Git"
    else
        log_info "没有未提交的更改"
    fi
}

# 部署到远程服务器
deploy_to_server() {
    log_info "部署到远程服务器 $SERVER_IP..."

    # SSH连接并执行部署
    ssh -i "$SSH_KEY" root@"$SERVER_IP" << 'EOF'
cd /opt/incomestreamai

# 拉取最新代码
echo "📥 拉取最新代码..."
git pull origin main

# 安装新的依赖（如果有）
if [ -f "requirements.txt" ]; then
    echo "📦 安装Python依赖..."
    pip install -r requirements.txt
fi

# 重启应用
echo "🔄 重启应用..."
pkill -f "python.*main.py" || true
sleep 2

# 启动应用
nohup python3 main.py > app.log 2>&1 &
sleep 3

# 检查应用状态
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ 应用重启成功"
    echo "🌐 应用地址: http://$SERVER_IP"
else
    echo "❌ 应用启动失败，请检查日志"
    tail -20 app.log
fi

EOF

    if [ $? -eq 0 ]; then
        log_success "远程部署完成"
    else
        log_error "远程部署失败"
        exit 1
    fi
}

# 验证部署
verify_deployment() {
    log_info "验证部署状态..."

    # 检查服务器上的应用状态
    ssh -i "$SSH_KEY" root@"$SERVER_IP" << 'EOF'
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ 应用正在运行"
    echo "📊 进程信息:"
    ps aux | grep "python.*main.py" | grep -v grep
else
    echo "❌ 应用未运行"
    exit 1
fi
EOF

    if [ $? -eq 0 ]; then
        log_success "部署验证成功"
    else
        log_error "部署验证失败"
        exit 1
    fi
}

# 主函数
main() {
    echo "🚀 IncomeStreamAI 本地到远程同步脚本"
    echo "=================================="

    check_prerequisites

    # 询问用户要执行的操作
    echo "请选择同步方式："
    echo "1) 仅同步到 Git"
    echo "2) 同步到 Git 并部署到远程服务器"
    echo "3) 仅部署远程服务器（不提交Git）"

    read -p "请输入选择 (1-3): " choice

    case $choice in
        1)
            sync_to_git
            ;;
        2)
            sync_to_git
            deploy_to_server
            verify_deployment
            ;;
        3)
            deploy_to_server
            verify_deployment
            ;;
        *)
            log_error "无效选择"
            exit 1
            ;;
    esac

    log_success "同步操作完成！"
    echo ""
    echo "🌐 远程应用地址: http://$SERVER_IP"
    echo "🔑 管理员账号: 18302196515"
    echo "📝 查看远程日志: ssh -i $SSH_KEY root@$SERVER_IP 'tail -f /opt/incomestreamai/app.log'"
}

# 运行主函数
main "$@"
#!/bin/bash
# IncomeStreamAI 本地开发环境启动脚本
# Local Development Environment Startup Script

set -e

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

# 检查Python版本
check_python() {
    log_info "检查Python版本..."
    if ! command -v python3 &> /dev/null; then
        log_error "未找到Python3，请先安装Python 3.8+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python版本: $PYTHON_VERSION"

    if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
        log_error "需要Python 3.8或更高版本，当前版本: $PYTHON_VERSION"
        exit 1
    fi
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装项目依赖..."

    # 检查是否有虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi

    # 激活虚拟环境
    log_info "激活虚拟环境..."
    source venv/bin/activate

    # 升级pip
    log_info "升级pip..."
    pip install --upgrade pip

    # 安装依赖
    log_info "安装项目依赖..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        # 从pyproject.toml安装依赖
        pip install -e .
    fi

    # 安装开发依赖
    pip install python-dotenv pytest pytest-flask
}

# 检查环境配置
check_env_config() {
    log_info "检查环境配置..."

    if [ ! -f ".env" ]; then
        log_error ".env文件不存在，请先创建环境配置文件"
        exit 1
    fi

    # 检查关键环境变量
    if ! grep -q "OPENAI_API_KEY" .env || grep -q "sk-your-openai-api-key-here" .env; then
        log_warning "请在.env文件中设置正确的OpenAI API密钥"
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p uploads
    mkdir -p logs
    mkdir -p instance
}

# 启动应用
start_application() {
    log_info "启动IncomeStreamAI本地开发服务器..."

    # 设置环境变量
    export FLASK_ENV=development
    export FLASK_DEBUG=1

    # 启动应用
    python3 main.py
}

# 主函数
main() {
    echo "🚀 IncomeStreamAI 本地开发环境启动器"
    echo "=================================="

    check_python
    install_dependencies
    check_env_config
    create_directories

    log_success "环境检查完成，启动应用..."
    start_application
}

# 错误处理
trap 'log_error "启动过程中发生错误"; exit 1' ERR

# 运行主函数
main "$@"
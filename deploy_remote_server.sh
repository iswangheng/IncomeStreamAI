#!/bin/bash
# ====================================================================
# IncomeStreamAI 项目远程服务器部署脚本
# 适用于：OpenCloudOS 9 / CentOS 9 / RHEL 9 系统
# 作者：AI助手
# 创建日期：2025年11月23日
# ====================================================================

set -e  # 遇到错误立即退出

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

# 检查是否为root用户
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "检测到root用户，建议使用普通用户进行部署"
        read -p "是否继续？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 设置项目变量
PROJECT_NAME="incomestreamai"
DEPLOY_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="incomestreamai"
NGINX_CONF="/etc/nginx/conf.d/$PROJECT_NAME.conf"
POSTGRES_DB="incomestreamai_db"
POSTGRES_USER="incomestreamai_user"

# 更新系统
update_system() {
    log_info "正在更新系统软件包..."
    sudo dnf update -y
    log_success "系统更新完成"
}

# 安装EPEL仓库
install_epel() {
    log_info "正在安装EPEL仓库..."
    sudo dnf install -y epel-release
    log_success "EPEL仓库安装完成"
}

# 安装Python 3.11+
install_python() {
    log_info "正在检查Python版本..."

    # 首先尝试从系统仓库安装Python 3.11+
    if dnf list python3.11 &>/dev/null; then
        sudo dnf install -y python3.11 python3.11-pip python3.11-devel
        log_success "Python 3.11 安装完成"
    else
        log_warning "系统仓库未找到Python 3.11，正在从源码编译安装..."
        install_python_from_source
    fi
}

# 从源码编译安装Python 3.11
install_python_from_source() {
    log_info "正在安装Python编译依赖..."
    sudo dnf groupinstall -y "Development Tools"
    sudo dnf install -y openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel xz-devel

    PYTHON_VERSION="3.11.10"
    cd /tmp
    wget "https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tgz"
    tar -xzf "Python-${PYTHON_VERSION}.tgz"
    cd "Python-${PYTHON_VERSION}"

    log_info "正在编译Python ${PYTHON_VERSION}..."
    ./configure --enable-optimizations --with-ssl
    make -j$(nproc)
    sudo make altinstall

    log_success "Python ${PYTHON_VERSION} 编译安装完成"
    cd /tmp
    rm -rf "Python-${PYTHON_VERSION}"*
}

# 安装uv包管理器
install_uv() {
    log_info "正在安装uv包管理器..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
    log_success "uv安装完成"
}

# 安装和配置PostgreSQL
install_postgresql() {
    log_info "正在安装PostgreSQL..."

    # 安装PostgreSQL
    sudo dnf install -y postgresql postgresql-server postgresql-contrib

    # 初始化数据库
    sudo postgresql-setup --initdb
    sudo systemctl enable postgresql
    sudo systemctl start postgresql

    # 设置数据库用户和数据库
    sudo -u postgres psql -c "CREATE USER $POSTGRES_USER WITH PASSWORD 'your_strong_password_here';"
    sudo -u postgres psql -c "CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;"

    # 配置PostgreSQL允许本地连接
    sudo sed -i 's/ident/md5/' /var/lib/pgsql/data/pg_hba.conf
    sudo systemctl restart postgresql

    log_success "PostgreSQL安装配置完成"
    log_warning "请记住数据库信息："
    echo "  数据库: $POSTGRES_DB"
    echo "  用户: $POSTGRES_USER"
    echo "  密码: your_strong_password_here (请在.env文件中修改)"
}

# 安装Nginx
install_nginx() {
    log_info "正在安装Nginx..."
    sudo dnf install -y nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx

    # 配置防火墙
    sudo firewall-cmd --permanent --add-service=http
    sudo firewall-cmd --permanent --add-service=https
    sudo firewall-cmd --reload

    log_success "Nginx安装完成"
}

# 创建项目目录和用户
setup_project() {
    log_info "正在设置项目目录..."

    # 创建项目目录
    sudo mkdir -p $DEPLOY_DIR
    sudo chown $USER:$USER $DEPLOY_DIR

    log_success "项目目录创建完成: $DEPLOY_DIR"
}

# 部署应用代码
deploy_app() {
    log_info "正在部署应用代码..."

    # 检查是否是Git仓库
    if [ -d ".git" ]; then
        log_info "检测到Git仓库，正在克隆代码..."
        git clone . $DEPLOY_DIR
    else
        log_warning "当前目录不是Git仓库，请手动复制代码到 $DEPLOY_DIR"
        read -p "按Enter键继续..."
    fi

    cd $DEPLOY_DIR

    # 安装依赖
    if command -v uv &> /dev/null; then
        log_info "正在使用uv安装依赖..."
        uv sync
    else
        log_info "正在使用pip安装依赖..."
        python3.11 -m pip install -e .
    fi

    # 创建必要的目录
    mkdir -p uploads
    mkdir -p logs

    log_success "应用代码部署完成"
}

# 配置环境变量
setup_environment() {
    log_info "正在配置环境变量..."

    ENV_FILE="$DEPLOY_DIR/.env"

    if [ ! -f "$ENV_FILE" ]; then
        cp .env.example "$ENV_FILE"

        # 生成随机SESSION_SECRET
        SESSION_SECRET=$(python3.11 -c "import secrets; print(secrets.token_hex(32))")

        log_info "请配置以下环境变量在 $ENV_FILE 文件中："
        echo "DATABASE_URL=postgresql://$POSTGRES_USER:your_strong_password_here@localhost:5432/$POSTGRES_DB"
        echo "SESSION_SECRET=$SESSION_SECRET"
        echo "OPENAI_API_KEY=sk-your-openai-api-key-here"

        log_warning "请编辑 .env 文件并填入正确的配置值！"
    fi
}

# 创建systemd服务
create_systemd_service() {
    log_info "正在创建systemd服务..."

    SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"

    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=IncomeStreamAI Web Application
After=network.target postgresql.service

[Service]
Type=notify
User=$USER
Group=$USER
WorkingDirectory=$DEPLOY_DIR
Environment=PATH=$DEPLOY_DIR/.venv/bin
EnvironmentFile=$DEPLOY_DIR/.env
ExecStart=/usr/local/bin/uv run gunicorn --config gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME

    log_success "systemd服务创建完成"
}

# 配置Nginx反向代理
configure_nginx() {
    log_info "正在配置Nginx反向代理..."

    sudo tee $NGINX_CONF > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # 请修改为你的域名或IP

    # 静态文件
    location /static/ {
        alias $DEPLOY_DIR/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 上传文件
    location /uploads/ {
        alias $DEPLOY_DIR/uploads/;
        expires 7d;
    }

    # 应用代理
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
EOF

    # 测试Nginx配置
    sudo nginx -t

    if [ $? -eq 0 ]; then
        sudo systemctl reload nginx
        log_success "Nginx配置完成"
    else
        log_error "Nginx配置错误，请检查配置文件"
        exit 1
    fi
}

# 启动应用
start_application() {
    log_info "正在启动应用..."

    # 初始化数据库
    cd $DEPLOY_DIR
    if [ -f ".env" ]; then
        export $(cat .env | xargs)
        python3.11 -c "from app import app, db; app.app_context().push(); db.create_all(); print('数据库表创建完成')"
    fi

    # 启动服务
    sudo systemctl start $SERVICE_NAME
    sudo systemctl status $SERVICE_NAME --no-pager

    log_success "应用启动完成！"
}

# 显示部署信息
show_deployment_info() {
    log_success "🎉 IncomeStreamAI 部署完成！"
    echo ""
    echo "部署信息："
    echo "  项目目录: $DEPLOY_DIR"
    echo "  服务名称: $SERVICE_NAME"
    echo "  Nginx配置: $NGINX_CONF"
    echo "  数据库: $POSTGRES_DB"
    echo "  数据库用户: $POSTGRES_USER"
    echo ""
    echo "常用命令："
    echo "  查看应用状态: sudo systemctl status $SERVICE_NAME"
    echo "  重启应用: sudo systemctl restart $SERVICE_NAME"
    echo "  查看应用日志: sudo journalctl -u $SERVICE_NAME -f"
    echo "  查看Nginx状态: sudo systemctl status nginx"
    echo ""
    echo "下一步："
    echo "  1. 编辑 $DEPLOY_DIR/.env 文件，配置正确的API密钥和数据库密码"
    echo "  2. 编辑 $NGINX_CONF 文件，设置正确的域名或IP地址"
    echo "  3. 重启服务: sudo systemctl restart $SERVICE_NAME nginx"
    echo "  4. 配置SSL证书（推荐使用Let's Encrypt）"
    echo ""
    echo "访问地址: http://your-server-ip"
}

# 主函数
main() {
    log_info "开始部署 IncomeStreamAI 项目到 OpenCloudOS 9"

    check_root
    update_system
    install_epel
    install_python
    install_uv
    install_postgresql
    install_nginx
    setup_project
    deploy_app
    setup_environment
    create_systemd_service
    configure_nginx
    start_application
    show_deployment_info
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查上面的错误信息"; exit 1' ERR

# 运行主函数
main "$@"
# IncomeStreamAI 远程服务器部署指南

## 📋 部署概述

本指南适用于将 IncomeStreamAI 项目部署到 OpenCloudOS 9 / CentOS 9 / RHEL 9 服务器。

### 系统要求

- **操作系统：** OpenCloudOS 9, CentOS 9, RHEL 9 或兼容系统
- **内存：** 最少 2GB RAM（推荐 4GB+）
- **存储：** 最少 10GB 可用空间
- **网络：** 稳定的互联网连接
- **权限：** sudo 权限或 root 权限

### 架构图

```
Internet
    ↓
[防火墙/路由器]
    ↓
[Nginx (80/443)] → 反向代理
    ↓
[Gunicorn (5000)] → WSGI服务器
    ↓
[Flask App] → Python应用
    ↓
[PostgreSQL (5432)] → 数据库
```

## 🚀 快速部署

### 方法一：使用自动化部署脚本

1. **上传项目到服务器**
```bash
# 方式A：使用Git克隆
git clone <your-repo-url> /tmp/incomestreamai
cd /tmp/incomestreamai

# 方式B：使用scp上传
scp -r /path/to/project user@server:/tmp/incomestreamai
ssh user@server
cd /tmp/incomestreamai
```

2. **运行部署脚本**
```bash
chmod +x deploy_remote_server.sh
./deploy_remote_server.sh
```

### 方法二：手动部署

如果需要更精细的控制，可以按照以下步骤手动部署。

## 📝 手动部署步骤

### 1. 系统准备

```bash
# 更新系统
sudo dnf update -y

# 安装EPEL仓库
sudo dnf install -y epel-release

# 安装开发工具
sudo dnf groupinstall -y "Development Tools"
```

### 2. 安装Python 3.11+

#### 方式A：从系统仓库安装（推荐）
```bash
# 检查可用版本
dnf search python3

# 安装Python 3.11（如果可用）
sudo dnf install -y python3.11 python3.11-pip python3.11-devel
```

#### 方式B：从源码编译安装
```bash
# 安装编译依赖
sudo dnf install -y openssl-devel bzip2-devel libffi-devel zlib-devel readline-devel sqlite-devel xz-devel

# 下载并编译Python 3.11
cd /tmp
wget https://www.python.org/ftp/python/3.11.10/Python-3.11.10.tgz
tar -xzf Python-3.11.10.tgz
cd Python-3.11.10
./configure --enable-optimizations --with-ssl
make -j$(nproc)
sudo make altinstall
```

### 3. 安装uv包管理器

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### 4. 安装和配置PostgreSQL

```bash
# 安装PostgreSQL
sudo dnf install -y postgresql postgresql-server postgresql-contrib

# 初始化数据库
sudo postgresql-setup --initdb

# 启动并设置开机自启
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 创建数据库和用户
sudo -u postgres psql <<EOF
CREATE USER incomestreamai_user WITH PASSWORD 'your_strong_password';
CREATE DATABASE incomestreamai_db OWNER incomestreamai_user;
GRANT ALL PRIVILEGES ON DATABASE incomestreamai_db TO incomestreamai_user;
\q
EOF

# 配置认证
sudo sed -i 's/ident/md5/' /var/lib/pgsql/data/pg_hba.conf
sudo systemctl restart postgresql
```

### 5. 安装Nginx

```bash
# 安装Nginx
sudo dnf install -y nginx

# 配置防火墙
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# 启动并设置开机自启
sudo systemctl enable nginx
sudo systemctl start nginx
```

### 6. 部署应用

```bash
# 创建项目目录
sudo mkdir -p /opt/incomestreamai
sudo chown $USER:$USER /opt/incomestreamai

# 复制项目文件
cp -r /tmp/incomestreamai/* /opt/incomestreamai/
cd /opt/incomestreamai

# 安装依赖
uv sync

# 创建必要目录
mkdir -p uploads logs
```

### 7. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

在 `.env` 文件中配置：

```bash
# 数据库连接（修改密码为实际密码）
DATABASE_URL=postgresql://incomestreamai_user:your_strong_password@localhost:5432/incomestreamai_db

# 生成随机会话密钥
SESSION_SECRET=your-generated-secret-key

# OpenAI API密钥
OPENAI_API_KEY=sk-your-openai-api-key
```

生成会话密钥：
```bash
python3.11 -c "import secrets; print(secrets.token_hex(32))"
```

### 8. 创建systemd服务

```bash
sudo tee /etc/systemd/system/incomestreamai.service > /dev/null <<EOF
[Unit]
Description=IncomeStreamAI Web Application
After=network.target postgresql.service

[Service]
Type=notify
User=$USER
Group=$USER
WorkingDirectory=/opt/incomestreamai
Environment=PATH=/opt/incomestreamai/.venv/bin
EnvironmentFile=/opt/incomestreamai/.env
ExecStart=/usr/local/bin/uv run gunicorn --config gunicorn.conf.py main:app
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 重载systemd并启用服务
sudo systemctl daemon-reload
sudo systemctl enable incomestreamai
```

### 9. 配置Nginx反向代理

```bash
sudo tee /etc/nginx/conf.d/incomestreamai.conf > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # 修改为你的域名或IP

    # 静态文件
    location /static/ {
        alias /opt/incomestreamai/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 上传文件
    location /uploads/ {
        alias /opt/incomestreamai/uploads/;
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

# 重载Nginx
sudo systemctl reload nginx
```

### 10. 启动应用

```bash
# 初始化数据库
cd /opt/incomestreamai
export $(cat .env | xargs)
python3.11 -c "from app import app, db; app.app_context().push(); db.create_all()"

# 启动应用
sudo systemctl start incomestreamai

# 检查状态
sudo systemctl status incomestreamai
```

## 🔒 SSL证书配置

### 使用Let's Encrypt

```bash
# 安装certbot
sudo dnf install -y certbot python3-certbot-nginx

# 获取SSL证书
sudo certbot --nginx -d your-domain.com

# 设置自动续期
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -
```

### 手动配置SSL证书

如果有自签名证书或其他SSL证书，可以手动配置Nginx：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

    # 其他配置...
}

# HTTP重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://\$server_name\$request_uri;
}
```

## 🔧 运维管理

### 常用命令

```bash
# 应用服务管理
sudo systemctl start incomestreamai          # 启动
sudo systemctl stop incomestreamai           # 停止
sudo systemctl restart incomestreamai        # 重启
sudo systemctl status incomestreamai         # 状态
sudo systemctl enable incomestreamai         # 开机自启

# 查看日志
sudo journalctl -u incomestreamai -f         # 实时日志
sudo journalctl -u incomestreamai -n 100     # 最近100行

# Nginx管理
sudo nginx -t                                # 测试配置
sudo systemctl reload nginx                  # 重载配置
sudo systemctl restart nginx                 # 重启

# 数据库管理
sudo -u postgres psql -l                    # 列出数据库
sudo -u postgres psql incomestreamai_db      # 连接数据库
```

### 备份策略

```bash
#!/bin/bash
# backup.sh - 数据备份脚本

BACKUP_DIR="/opt/backups/incomestreamai"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
sudo -u postgres pg_dump incomestreamai_db > $BACKUP_DIR/db_backup_$DATE.sql

# 备份应用文件
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C /opt incomestreamai

# 删除7天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "备份完成: $DATE"
```

### 监控脚本

```bash
#!/bin/bash
# monitor.sh - 服务监控脚本

SERVICE_NAME="incomestreamai"
LOG_FILE="/var/log/incomestreamai_monitor.log"

# 检查服务状态
if ! systemctl is-active --quiet $SERVICE_NAME; then
    echo "$(date): $SERVICE_NAME 服务未运行，正在重启..." >> $LOG_FILE
    systemctl restart $SERVICE_NAME
fi

# 检查端口
if ! netstat -tuln | grep -q ":5000 "; then
    echo "$(date): 端口5000未监听，服务异常" >> $LOG_FILE
fi
```

## 🐛 故障排除

### 常见问题

1. **应用无法启动**
```bash
# 检查日志
sudo journalctl -u incomestreamai -n 50

# 常见原因：
# - 环境变量未正确设置
# - 数据库连接失败
# - 端口被占用
# - 依赖包未正确安装
```

2. **数据库连接失败**
```bash
# 检查PostgreSQL状态
sudo systemctl status postgresql

# 测试连接
psql -h localhost -U incomestreamai_user -d incomestreamai_db -W

# 检查配置
sudo cat /var/lib/pgsql/data/pg_hba.conf
```

3. **Nginx 502 Bad Gateway**
```bash
# 检查Gunicorn是否运行
netstat -tuln | grep 5000

# 检查Nginx配置
sudo nginx -t

# 查看Nginx日志
sudo tail -f /var/log/nginx/error.log
```

4. **静态文件无法访问**
```bash
# 检查文件权限
ls -la /opt/incomestreamai/static/

# 检查Nginx配置中的路径
sudo cat /etc/nginx/conf.d/incomestreamai.conf | grep static
```

### 性能优化

1. **数据库优化**
```sql
-- 创建索引
CREATE INDEX idx_analysis_status ON analysis(status);
CREATE INDEX idx_analysis_user ON analysis(user_id);

-- 定期清理
VACUUM ANALYZE;
```

2. **Nginx缓存配置**
```nginx
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

3. **应用监控**
```bash
# 安装监控工具
pip install flask-metrics prometheus-client

# 在应用中添加监控端点
```

## 🔄 更新和维护

### 应用更新

```bash
#!/bin/bash
# update.sh - 应用更新脚本

cd /opt/incomestreamai

# 备份当前版本
./backup.sh

# 拉取最新代码
git pull origin main

# 更新依赖
uv sync

# 重启服务
sudo systemctl restart incomestreamai

echo "应用更新完成"
```

### 依赖更新

```bash
# 更新uv管理的依赖
uv sync --upgrade

# 或手动更新特定包
uv add package_name@latest
```

## 📊 监控和日志

### 日志配置

在 `gunicorn.conf.py` 中配置日志：

```python
# 日志配置
accesslog = "/var/log/incomestreamai/access.log"
errorlog = "/var/log/incomestreamai/error.log"
loglevel = "info"

# 创建日志目录
sudo mkdir -p /var/log/incomestreamai
sudo chown $USER:$USER /var/log/incomestreamai
```

### 系统监控

```bash
# 安装系统监控工具
sudo dnf install -y htop iotop nethogs

# 监控系统资源
htop                    # CPU和内存
iotop                   # 磁盘I/O
nethogs                 # 网络使用
```

---

## 📞 技术支持

如果在部署过程中遇到问题，请检查：

1. **系统日志：** `journalctl -xe`
2. **应用日志：** `sudo journalctl -u incomestreamai -f`
3. **Nginx日志：** `sudo tail -f /var/log/nginx/error.log`
4. **数据库日志：** `sudo tail -f /var/lib/pgsql/data/log/postgresql.log`

**最后更新：** 2025年11月23日
**适用版本：** IncomeStreamAI v0.1.0
**文档维护：** AI助手
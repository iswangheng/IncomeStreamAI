# IncomeStreamAI 本地到远程同步指南

## 🔄 同步方案概览

您的项目已经配置了完整的本地开发到远程生产环境的同步机制：

- **本地开发**：SQLite + 开发模式 + 端口8080
- **远程生产**：PostgreSQL + 生产模式 + 端口80
- **代码管理**：Git + GitHub
- **自动化同步**：专用同步脚本

## 🚀 快速同步

### 方法一：使用自动化同步脚本（推荐）

```bash
# 运行同步脚本
./sync_to_remote.sh

# 选择同步方式：
# 1) 仅同步到 Git
# 2) 同步到 Git 并部署到远程服务器
# 3) 仅部署远程服务器
```

### 方法二：手动同步步骤

```bash
# 1. 提交本地更改
git add .
git commit -m "新功能开发"
git push origin main

# 2. SSH到远程服务器
ssh -i 001.pem root@101.34.152.109

# 3. 在服务器上更新
cd /opt/incomestreamai
git pull origin main
pkill -f "python.*main.py"
nohup python3 main.py > app.log 2>&1 &

# 4. 检查运行状态
ps aux | grep "python.*main.py"
```

## 📁 环境配置差异

### 本地开发环境 (`.env`)
```bash
DATABASE_URL=sqlite:///incomestreamai_local.db  # SQLite 本地数据库
FLASK_ENV=development                            # 开发模式
FLASK_DEBUG=1                                    # 调试开启
```

### 远程生产环境 (服务器 `.env`)
```bash
DATABASE_URL=postgresql://...?sslmode=disable   # PostgreSQL 生产数据库
FLASK_ENV=production                             # 生产模式
FLASK_DEBUG=0                                    # 调试关闭
```

## 🔧 开发工作流程

### 日常开发流程
1. **本地开发**：使用 `python3 main_local.py` 启动本地开发
2. **测试验证**：确保功能在本地 SQLite 环境下正常工作
3. **同步部署**：使用 `./sync_to_remote.sh` 同步到生产环境
4. **生产验证**：检查远程服务器应用运行状态

### 数据库变更处理
- **本地开发**：可以随时重置 SQLite：`rm incomestreamai_local.db`
- **生产部署**：SQLAlchemy 会自动处理 PostgreSQL 的表结构变更
- **数据安全**：生产数据保留在远程服务器，不会被本地开发影响

## 🛠️ 实用命令

### 本地开发
```bash
# 启动本地开发服务器
python3 main_local.py

# 运行环境测试
python3 test_local_setup.py

# 重置本地数据库
rm incomestreamai_local.db
```

### 远程管理
```bash
# 查看远程应用状态
ssh -i 001.pem root@101.34.152.109 "ps aux | grep python"

# 查看远程日志
ssh -i 001.pem root@101.34.152.109 "tail -f /opt/incomestreamai/app.log"

# 重启远程应用
ssh -i 001.pem root@101.34.152.109 "cd /opt/incomestreamai && pkill -f python && nohup python3 main.py > app.log 2>&1 &"
```

## 🔒 安全注意事项

1. **SSH密钥**：001.pem 已在 .gitignore 中，不会提交到 Git
2. **环境变量**：.env 文件包含敏感信息，不会同步到远程
3. **生产配置**：远程服务器使用独立的生产配置
4. **数据库分离**：本地开发和生产数据库完全独立

## 📝 版本控制策略

### Git 提交规范
```bash
# 功能开发
git commit -m "feat: 添加用户管理功能"

# 问题修复
git commit -m "fix: 修复登录页面样式问题"

# 配置变更
git commit -m "config: 更新数据库配置"
```

### 分支管理
- **main**：主分支，用于生产环境
- **develop**：开发分支（可选）
- **feature/***：功能分支（可选）

## 🚨 故障排除

### 同步失败
1. 检查 SSH 连接：`ssh -i 001.pem root@101.34.152.109`
2. 检查 Git 状态：`git status`
3. 查看同步脚本日志

### 部署失败
1. 检查远程服务器权限
2. 查看应用日志：`tail -f app.log`
3. 检查端口占用：`netstat -tlnp | grep :80`

### 数据库问题
1. 本地：删除 SQLite 文件重新创建
2. 远程：检查 PostgreSQL 服务状态

---

🎉 **现在您可以在本地自由开发，然后一键同步到生产环境了！**
# 项目部署指南

## 项目概述
这是一个基于Flask的Web应用，使用PostgreSQL数据库。

## 系统要求
- Python 3.11 或更高版本
- PostgreSQL 16
- 推荐使用 `uv` 作为包管理器（或使用pip）

## 环境变量配置

在部署前，需要设置以下环境变量：

### 必需的环境变量
```bash
# 数据库连接
DATABASE_URL=postgresql://用户名:密码@主机:端口/数据库名

# 会话密钥（请生成随机字符串）
SESSION_SECRET=你的随机密钥

# OpenAI API密钥
OPENAI_API_KEY=sk-your-api-key-here
```

### 可选的环境变量
根据你的应用需求，可能还需要其他环境变量。

## 本地部署步骤

### 1. 安装依赖

**使用 uv（推荐）：**
```bash
# 安装uv（如果还没安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 安装项目依赖
uv sync
```

**使用 pip：**
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 从pyproject.toml安装依赖
pip install -e .
```

### 2. 配置数据库

确保PostgreSQL已安装并运行，然后：

```bash
# 创建数据库
createdb 你的数据库名

# 设置DATABASE_URL环境变量
export DATABASE_URL="postgresql://用户名:密码@localhost:5432/数据库名"
```

### 3. 设置环境变量

创建 `.env` 文件（不要提交到版本控制）：
```bash
DATABASE_URL=postgresql://localhost/your_db
SESSION_SECRET=生成一个随机字符串
OPENAI_API_KEY=your-openai-api-key
```

### 4. 初始化数据库

应用会在首次启动时自动创建数据库表（通过 `db.create_all()`）。

### 5. 启动应用

**开发环境：**
```bash
# 使用uv
uv run gunicorn --bind 0.0.0.0:5000 --reload main:app

# 或使用python直接运行
python main.py
```

**生产环境：**
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

应用将在 `http://localhost:5000` 运行。

## 生产环境部署

### 部署到其他平台

#### Replit
1. 在Replit创建新项目
2. 上传项目文件或从GitHub导入
3. 在Secrets中配置环境变量
4. 点击Run按钮启动

#### Heroku
```bash
# 需要创建Procfile
echo "web: gunicorn main:app" > Procfile

# 部署
heroku create
heroku addons:create heroku-postgresql:mini
heroku config:set SESSION_SECRET=你的密钥
heroku config:set OPENAI_API_KEY=你的密钥
git push heroku main
```

#### Railway / Render
1. 连接GitHub仓库
2. 设置构建命令：`uv sync` 或 `pip install -e .`
3. 设置启动命令：`gunicorn --bind 0.0.0.0:$PORT main:app`
4. 在环境变量中设置 DATABASE_URL、SESSION_SECRET、OPENAI_API_KEY
5. 添加PostgreSQL数据库服务

#### Docker部署
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装uv
RUN pip install uv

# 复制项目文件
COPY . .

# 安装依赖
RUN uv sync

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

## 项目文件结构

```
.
├── app.py                  # Flask应用初始化
├── main.py                 # 应用入口
├── models.py               # 数据库模型
├── openai_service.py       # OpenAI服务
├── pyproject.toml          # 项目依赖
├── uv.lock                 # 依赖锁定文件
├── gunicorn.conf.py        # Gunicorn配置
├── static/                 # 静态资源（CSS、JS）
├── templates/              # HTML模板
├── prompts/                # 提示词文件
├── uploads/                # 上传文件目录
└── tests/                  # 测试文件

```

## 数据库迁移

如果需要修改数据库结构，建议使用Flask-Migrate：

```bash
# 安装
pip install flask-migrate

# 初始化
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## 常见问题

### 1. 数据库连接失败
- 检查 DATABASE_URL 格式是否正确
- 确认PostgreSQL服务是否运行
- 检查防火墙和网络配置

### 2. 环境变量未生效
- 重启应用服务
- 如在Replit，修改Secrets后需要重启整个工作区（运行 `kill 1`）

### 3. 依赖安装失败
- 确保Python版本 >= 3.11
- 尝试使用 `pip install --upgrade pip`
- 清理缓存：`uv cache clean` 或 `pip cache purge`

## 安全提醒

⚠️ **重要：**
- 不要将 `.env` 文件或包含密钥的文件提交到版本控制
- 在生产环境使用强随机SESSION_SECRET
- 定期轮换API密钥
- 使用HTTPS进行生产部署
- 限制数据库访问权限

## 技术支持

如有问题，请查看：
- Flask文档：https://flask.palletsprojects.com/
- SQLAlchemy文档：https://docs.sqlalchemy.org/
- Gunicorn文档：https://docs.gunicorn.org/

---

**部署日期：** 2025年11月23日  
**Python版本：** 3.11+  
**框架：** Flask + SQLAlchemy + PostgreSQL

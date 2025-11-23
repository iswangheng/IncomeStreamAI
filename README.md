# AI工具演示应用

基于Flask的AI分析工具Web应用。

## 快速开始

### 前置要求
- Python 3.11+
- PostgreSQL 16
- uv 包管理器（推荐）或 pip

### 安装与运行

1. **克隆项目**
```bash
git clone <your-repo-url>
cd <project-folder>
```

2. **安装依赖**
```bash
# 使用uv
uv sync

# 或使用pip
pip install -e .
```

3. **配置环境变量**
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，填入你的配置
nano .env
```

4. **启动应用**
```bash
# 开发环境
uv run gunicorn --bind 0.0.0.0:5000 --reload main:app

# 或
python main.py
```

访问 `http://localhost:5000`

## 项目结构

- `app.py` - Flask应用和数据库初始化
- `main.py` - 应用入口
- `models.py` - 数据库模型
- `openai_service.py` - OpenAI API服务
- `static/` - 静态资源（CSS、JavaScript）
- `templates/` - HTML模板
- `prompts/` - AI提示词
- `uploads/` - 用户上传文件

## 技术栈

- **后端：** Flask, SQLAlchemy, Gunicorn
- **数据库：** PostgreSQL
- **AI服务：** OpenAI API
- **前端：** HTML, CSS, JavaScript (原生)
- **认证：** Flask-Login, Flask-Dance (Replit Auth)

## 部署

详细部署指南请参阅 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

支持的部署平台：
- Replit
- Heroku
- Railway
- Render
- Docker
- 任何支持Python的云平台

## 环境变量

必需的环境变量（参见 `.env.example`）：
- `DATABASE_URL` - PostgreSQL数据库连接
- `SESSION_SECRET` - Flask会话密钥
- `OPENAI_API_KEY` - OpenAI API密钥

## 开发

### 运行测试
```bash
pytest tests/
```

### 数据库迁移
应用会在启动时自动创建数据库表。

## 安全注意事项

- 不要将 `.env` 文件提交到版本控制
- 使用强随机SESSION_SECRET
- 定期轮换API密钥
- 生产环境使用HTTPS

## 许可证

[添加你的许可证信息]

## 贡献

[添加贡献指南]

---

**最后更新：** 2025年11月23日

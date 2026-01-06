# IncomeStreamAI 本地开发环境设置指南

## 📋 前置要求

### 系统要求
- **操作系统**: macOS / Linux / Windows
- **Python**: 3.8 或更高版本
- **Git**: 用于版本控制

### 检查Python版本
```bash
python3 --version
# 应该显示 Python 3.8.x 或更高版本
```

## 🚀 快速开始

### 方法一：使用自动化脚本（推荐）

1. **克隆项目**
```bash
git clone https://github.com/iswangheng/IncomeStreamAI.git
cd IncomeStreamAI
```

2. **运行启动脚本**
```bash
chmod +x run_local.sh
./run_local.sh
```

脚本会自动：
- ✅ 检查Python版本
- ✅ 创建虚拟环境
- ✅ 安装所有依赖
- ✅ 检查环境配置
- ✅ 启动开发服务器

### 方法二：手动设置

1. **克隆项目**
```bash
git clone https://github.com/iswangheng/IncomeStreamAI.git
cd IncomeStreamAI
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或者 venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install --upgrade pip
pip install -e .
pip install python-dotenv pytest pytest-flask
```

4. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，配置以下内容：
# DATABASE_URL=sqlite:///incomestreamai_local.db
# OPENAI_API_KEY=your-openai-api-key-here
# SESSION_SECRET=your-secret-key-here
```

5. **启动应用**
```bash
python3 main.py
```

## ⚙️ 环境配置

### .env 文件配置

创建 `.env` 文件并配置以下变量：

```bash
# 数据库配置
DATABASE_URL=sqlite:///incomestreamai_local.db

# OpenAI API密钥（必需）
OPENAI_API_KEY=sk-your-actual-api-key-here

# Flask配置
SESSION_SECRET=your-secret-key-for-development
FLASK_ENV=development
FLASK_DEBUG=1
```

### 数据库选项

#### 选项1：SQLite（推荐用于本地开发）
```bash
DATABASE_URL=sqlite:///incomestreamai_local.db
```
- ✅ 无需额外安装
- ✅ 配置简单
- ✅ 适合开发和测试

#### 选项2：PostgreSQL
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/incomestreamai_local
```
- 需要安装PostgreSQL
- 适合生产环境模拟

## 🌐 访问应用

启动成功后，访问：
- **应用地址**: http://127.0.0.1:5000
- **调试模式**: 已启用
- **自动重载**: 代码修改后自动重启

## 📁 项目结构

```
IncomeStreamAI/
├── app.py                 # 主应用文件
├── main.py                # 应用启动入口
├── .env                   # 环境变量配置（需要创建）
├── .env.example           # 环境变量模板
├── pyproject.toml         # 项目依赖配置
├── run_local.sh          # 本地启动脚本
├── templates/             # HTML模板
├── static/               # 静态文件（CSS/JS）
├── uploads/              # 文件上传目录
└── instance/             # 数据库文件目录
```

## 🛠️ 开发工具

### 运行测试
```bash
# 激活虚拟环境后运行
pytest tests/
```

### 代码格式化
```bash
# 安装格式化工具
pip install black flake8

# 格式化代码
black .

# 检查代码质量
flake8 .
```

### 依赖管理
```bash
# 查看已安装的依赖
pip list

# 安装新依赖
pip install package-name

# 更新依赖
pip install --upgrade package-name

# 生成requirements.txt
pip freeze > requirements.txt
```

## 🔧 故障排除

### 常见问题

1. **Python版本不兼容**
   ```bash
   # 确保使用Python 3.8+
   python3 --version
   ```

2. **依赖安装失败**
   ```bash
   # 升级pip
   pip install --upgrade pip
   # 使用国内镜像
   pip install -i https://pypi.tuna.tsinghua.edu.cn/simple package-name
   ```

3. **OpenAI API错误**
   - 检查 `.env` 文件中的API密钥是否正确
   - 确认API密钥有足够的配额

4. **数据库连接错误**
   - 检查 `.env` 文件中的 `DATABASE_URL` 配置
   - 确保数据库服务正在运行（如果使用PostgreSQL）

5. **端口被占用**
   ```bash
   # 查找占用5000端口的进程
   lsof -i :5000
   # 杀死进程
   kill -9 <PID>
   ```

### 日志调试

应用启动后，可以在终端查看详细的调试信息，包括：
- HTTP请求日志
- 数据库查询日志
- 错误和警告信息

## 🎯 开发建议

1. **使用虚拟环境**: 避免依赖冲突
2. **定期更新依赖**: 保持项目依赖的最新状态
3. **编写测试**: 确保代码质量
4. **使用版本控制**: 定期提交代码更改
5. **检查API配额**: 监控OpenAI API使用情况

## 📚 相关文档

- [部署指南](./REMOTE_DEPLOYMENT_GUIDE.md)
- [部署改动记录](./DEPLOYMENT_CHANGES.md)
- [项目README](./README.md)

---

🤖 **配置完成后，您就可以开始本地开发了！**
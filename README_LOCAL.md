# IncomeStreamAI 本地开发环境快速启动指南

## 🚀 快速启动

### 1. 启动应用
```bash
# 方法一：使用自动化脚本
./run_local.sh

# 方法二：手动启动
python3 main_local.py
```

### 2. 访问应用
- **应用地址**: http://127.0.0.1:8080
- **登录页面**: http://127.0.0.1:8080/login

### 3. 默认管理员账号
- **手机号**: 18302196515
- **密码**: aibenzong9264

## 📁 本地文件结构

```
IncomeStreamAI/
├── .env                           # 本地环境配置
├── incomestreamai_local.db       # SQLite 数据库文件
├── main_local.py                  # 本地开发启动脚本
├── test_local_setup.py           # 本地环境测试脚本
├── requirements.txt              # 依赖列表
├── LOCAL_SETUP_GUIDE.md          # 详细设置指南
├── run_local.sh                  # 自动化启动脚本
└── ...
```

## 🧪 测试环境

运行测试脚本验证环境配置：
```bash
python3 test_local_setup.py
```

## ⚙️ 环境配置

本地开发使用 SQLite 数据库，配置如下：
- **数据库**: SQLite (incomestreamai_local.db)
- **端口**: 8080 (避免与系统服务冲突)
- **调试模式**: 开启
- **API密钥**: 使用配置的 OpenAI API Key

## 🔧 常见问题

1. **端口占用**: 如8080端口被占用，可修改 `main_local.py` 中的端口号
2. **依赖问题**: 运行 `pip install -r requirements.txt` 重新安装依赖
3. **数据库问题**: 删除 `incomestreamai_local.db` 文件，重启应用会重新创建

## 📝 开发说明

- 本地环境已修复 Python 3.9.6 的 hashlib.scrypt 兼容性问题
- 使用 pbkdf2_sha256 替代 scrypt 进行密码哈希
- 所有代码注释和文档均使用中文
- 测试和临时文件请放在 `test/` 文件夹中

---

🎉 **本地开发环境配置完成！** 现在可以开始开发了。
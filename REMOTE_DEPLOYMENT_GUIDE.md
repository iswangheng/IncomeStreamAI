# 远程服务器部署指南

## 🚀 快速部署（推荐）

### 一键部署脚本

只需运行一个命令，即可完成所有部署步骤：

```bash
./deploy_remote.sh
```

**脚本会自动完成：**
1. ✅ 同步 `app.py` 到服务器
2. ✅ 同步 `models.py` 到服务器
3. ✅ 同步 `templates/` 目录到服务器
4. ✅ 重启应用
5. ✅ 验证应用状态

---

## 📝 完整部署流程

```bash
# 1. 本地开发完成并测试
python3 main_local.py

# 2. 提交到Git（保留代码历史）
git add .
git commit -m "feat: 新功能描述"
git push origin main

# 3. 部署到远程服务器
./deploy_remote.sh

# 4. 验证部署
# 访问: http://101.34.152.109
```

---

## 📊 服务器信息

- **服务器IP**: 101.34.152.109
- **部署路径**: /opt/incomestreamai
- **应用端口**: 80
- **访问地址**: http://101.34.152.109
- **管理员**: 18302196515

---

## 🔍 常用命令

### 查看应用日志
```bash
ssh -i 001.pem root@101.34.152.109 'tail -f /opt/incomestreamai/app.log'
```

### 检查应用状态
```bash
ssh -i 001.pem root@101.34.152.109 'ps aux | grep python'
```

### 手动重启应用
```bash
ssh -i 001.pem root@101.34.152.109 'cd /opt/incomestreamai && pkill -f python && nohup python3 main.py > app.log 2>&1 &'
```

---

**最后更新**: 2025年1月6日

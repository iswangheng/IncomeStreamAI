# IncomeStreamAI - 项目配置与文档

> 本文件包含 IncomeStreamAI 项目的核心配置说明、架构信息、代码规范和改动日志，供 Claude AI Assistant 使用。

---

## 📖 项目概述

### 项目简介
**IncomeStreamAI** 是一个基于 Flask 的非劳务收入路径设计方案生成系统，通过 AI 分析用户输入，提供个性化的收入管道设计建议。

### 技术栈
- **后端框架**: Flask 3.1+
- **数据库**: PostgreSQL 16 / SQLite (开发环境)
- **ORM**: SQLAlchemy 2.0+
- **认证**: Flask-Login
- **AI服务**: OpenAI API
- **WSGI服务器**: Gunicorn (生产环境)
- **Python版本**: 3.9+ (本地) / 3.11+ (生产)

### 项目结构
```
IncomeStreamAI/
├── app.py                      # Flask应用主文件
├── models.py                   # 数据库模型定义
├── openai_service.py           # OpenAI服务封装
├── main.py                     # 应用入口
├── main_local.py               # 本地开发入口
├── templates/                  # HTML模板
│   ├── components/            # 可复用组件
│   ├── history_apple.html     # 历史记录页面
│   └── ...
├── static/                     # 静态资源
│   ├── css/                   # 样式文件
│   └── js/                    # JavaScript文件
├── prompts/                    # AI提示词文件
├── uploads/                    # 上传文件目录
├── requirements.txt            # Python依赖
├── .env                        # 环境变量配置
└── CLAUDE.md                   # 本文件
```

---

## 🏗️ 架构说明

### 核心模块

#### 1. 用户认证模块
- **文件**: `app.py` (line 100-300)
- **功能**: 用户登录、注册、权限管理
- **路由**: `/login`, `/register`, `/logout`
- **权限**: 普通用户 vs 管理员

#### 2. AI分析模块
- **文件**: `app.py` (line 400-1200)
- **功能**: 接收表单、调用OpenAI API、生成分析结果
- **路由**: `/api/analyze`, `/api/start_analysis`
- **AI服务**: `openai_service.py`

#### 3. 历史记录模块
- **文件**: `app.py` (line 2007-2071)
- **功能**: 查看历史分析记录
- **路由**: `/history`, `/history/<record_id>`
- **模板**: `history_apple.html`

#### 4. 知识库管理模块
- **文件**: `app.py` (line 1500-1800)
- **功能**: 上传、管理知识库文件
- **路由**: `/knowledge`, `/api/knowledge/upload`

### 数据库模型

#### User (用户表)
```python
- id: 主键
- phone: 手机号（唯一）
- password_hash: 密码哈希
- name: 姓名
- is_admin: 是否管理员
- ai_quota: AI分析总额度
- used_quota: 已使用次数
```

#### AnalysisResult (分析结果表)
```python
- id: UUID主键
- sequence_id: 自增数字ID
- user_id: 外键 → users.id
- form_data: 表单数据（JSON）
- result_data: 分析结果（JSON）
- project_name: 项目名称
- analysis_type: 分析类型
- created_at: 创建时间
```

#### KnowledgeItem (知识库条目表)
```python
- id: 主键
- filename: 文件名
- file_path: 文件路径
- content_summary: 内容摘要
- upload_time: 上传时间
```

---

## 📋 项目改动日志 (Changelog)

> 本章节记录所有重要功能更新、架构变更和部署信息，按时间倒序排列。

### 📅 2026-01-06 - 用户数据分析功能

#### ✨ 新增功能：管理员后台用户数据分析

**新增文件**:
- `templates/admin_users_analytics.html` - 用户数据分析页面模板
- `用户数据分析功能PRD.md` - 完整产品需求文档
- `用户数据分析-设计总结.md` - 快速参考设计文档

**改动文件**:
- `app.py` (line 3086-3462) - 添加5个新的API路由
- `models.py` (line 109-113) - 添加数据库索引优化

**新增功能**:
1. **用户数据分析页面** (`/admin/users-analytics`)
   - 在管理员后台新增独立标签页
   - Apple风格设计，优雅美观

2. **统计卡片** (3个核心指标)
   - 总用户数
   - 高价值用户（分析次数 > 3 且 30天内有登录）
   - 今日活跃（今天有登录或分析的用户）

3. **用户筛选功能** (5种筛选方式)
   - 全部用户
   - 高价值用户（分析次数 > 3 且 30天内有登录）
   - 活跃用户（7天内有登录）
   - 沉默用户（30天未登录）
   - 已耗尽额度（剩余额度 = 0）

4. **用户列表展示**
   - 手机号（完整显示）
   - 姓名
   - 分析次数
   - 最后登录（相对时间：刚刚、2小时前、昨天等）
   - 状态标签（高价值/活跃/沉默/已耗尽）
   - 操作按钮（查看详情）
   - 支持排序（默认按分析次数降序）
   - 支持搜索（手机号/姓名）
   - 支持分页（每页20条）

5. **用户详情弹窗**
   - 基础信息：姓名、手机号、注册时间、最后登录
   - 使用数据：分析次数、剩余额度、使用率（带进度条）
   - 最近活动：最近10条分析记录（项目名称 + 创建时间）

6. **数据导出功能**
   - 导出当前筛选结果为CSV文件
   - UTF-8编码，Excel可直接打开
   - 文件名格式：`users_export_YYYYMMDD_HHMMSS.csv`

**新增API路由**:
```python
# 页面路由
GET  /admin/users-analytics                      # 用户数据分析页面

# 数据API
GET  /admin/api/users/analytics/stats            # 统计数据
GET  /admin/api/users/analytics/list            # 用户列表（分页、筛选、排序、搜索）
GET  /admin/api/users/<int:user_id>/detail       # 用户详情
GET  /admin/api/users/export                    # 导出CSV
```

**数据库优化**:
```python
# User 模型添加索引
__table_args__ = (
    db.Index('idx_users_last_login', 'last_login'),
    db.Index('idx_users_phone', 'phone'),
)
```

**技术特点**:
- 使用 SQLAlchemy 子查询统计每个用户的分析次数
- 使用 `func.coalesce` 处理 NULL 值
- 使用 `outerjoin` 确保没有分析记录的用户也会显示
- 使用 `db.or_` 实现多字段搜索
- 使用防抖处理搜索输入（500ms延迟）
- 异步加载数据，提升用户体验

**高价值用户定义**:
```
高价值用户 = 分析次数 > 3  AND  30天内有登录
```
- **分析次数 > 3**: 用户有实际使用，产生了价值
- **30天内有登录**: 用户在近期内仍然活跃，没有完全流失
- 两个条件**同时满足**，筛选出有使用量且保持一定活跃度的用户

**用户状态标签**:
- **高价值**: 紫色渐变（#667eea → #764ba2）
- **活跃**: 绿色（#34c759）
- **沉默**: 灰色（#8e8e93）
- **已耗尽**: 红色（#ff3b30）

**权限控制**:
- 所有接口都需要 `@login_required` 和 `@admin_required` 装饰器
- 普通用户无法访问此功能

**性能优化**:
- 使用子查询避免 N+1 问题
- 添加数据库索引提升查询速度
- 分页查询，避免一次性加载所有数据
- 前端防抖处理，减少API调用

**相关文档**:
- `用户数据分析功能PRD.md` - 完整PRD文档（含界面设计、技术实现、验收标准）
- `用户数据分析-设计总结.md` - 快速参考设计文档

---

### 📅 2026-01-06 - 历史分析记录页面升级

#### ✨ 新增功能：显示用户信息

**改动文件**:
- `templates/history_apple.html` - 历史记录页面UI升级
- `app.py` (line 2007-2035) - 优化历史记录路由，添加用户数据预加载

**新增功能**:
1. 在每条分析记录卡片中显示用户头像和姓名
2. 用户头像：圆形渐变设计，显示姓名首字或手机号后两位
3. 管理员可见用户手机号，普通用户仅看姓名
4. 添加管理员徽章标识（渐变色背景）
5. 优化统计卡片，管理员显示活跃用户数量，普通用户显示平均团队规模
6. 使用 SQLAlchemy `joinedload` 预加载用户数据，避免 N+1 查询问题

**技术亮点**:
- **权限分离**: 管理员可查看所有用户的记录，普通用户只能看自己的
- **优雅设计**: 紫色渐变头像（#667eea → #764ba2），粉色渐变管理员徽章
- **性能优化**: 使用 `joinedload(AnalysisResult.user)` 一次查询获取所有关联数据
- **响应式布局**: 完美适配桌面和移动设备

**数据库关联**:
```python
# AnalysisResult 模型包含用户关联
user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
user = db.relationship('User', backref='analysis_results')
```

**权限控制逻辑**:
```python
if current_user.is_admin:
    # 管理员：查看所有记录
    analysis_records = AnalysisResult.query.options(
        joinedload(AnalysisResult.user)
    ).order_by(AnalysisResult.created_at.desc()).all()
else:
    # 普通用户：只看自己的记录
    analysis_records = AnalysisResult.query.options(
        joinedload(AnalysisResult.user)
    ).filter_by(user_id=current_user.id).order_by(
        AnalysisResult.created_at.desc()
    ).all()
```

**Git提交**:
- `620a6f0` - docs: 添加项目改动日志与更新指南
- `e04650c` - docs: 添加部署相关文档和脚本
- `77707c5` - feat: 升级历史分析记录页面，添加用户信息展示

**相关文档**:
- `HISTORY_PAGE_UPGRADE.md` - 功能升级详细说明
- `PROJECT_CHANGELOG.md` - 完整改动日志和更新指南
- `DEPLOYMENT_SUMMARY.md` - 部署总结
- `deploy_update.sh` - 自动化部署脚本

---

### 📅 2025-11-23 - 项目初始化

#### 🎯 基础功能建立

**核心功能**:
- 用户认证系统（手机号登录）
- AI分析表单提交
- 分析结果展示
- 知识库管理
- 历史记录查看

**部署环境**:
- 服务器IP: 101.34.152.109
- 数据库: PostgreSQL 16
- 运行端口: 80

---

## 🌐 线上环境配置

### 服务器信息
```bash
IP地址: 101.34.152.109
SSH用户: root
SSH密钥: 001.pem
项目路径: /opt/incomestreamai
访问地址: http://101.34.152.109
```

### 数据库配置
```bash
类型: PostgreSQL 16
数据库: incomestreamai_db
用户: incomestreamai_user
密码: incomeAI2024!
连接: postgresql://incomestreamai_user:incomeAI2024!@127.0.0.1:5432/incomestreamai_db?sslmode=disable
```

### 默认账号
```
管理员手机号: 18302196515
管理员密码: aibenzong9264
```

---

## 🔄 代码更新流程

### 方法一：自动化部署（推荐）⭐

```bash
# 1. 进入项目目录
cd "/Users/weilingkeji/360安全云盘同步版/000-海外/02-incomestream/IncomeStreamAI"

# 2. 运行部署脚本
./deploy_update.sh
```

### 方法二：手动更新

```bash
# 1. 修改代码并提交
git add .
git commit -m "描述改动"
git push origin main

# 2. 打包文件
tar -czf update.tar.gz app.py models.py templates/

# 3. 上传到服务器
scp -i 001.pem update.tar.gz root@101.34.152.109:/tmp/

# 4. SSH登录服务器
ssh -i 001.pem root@101.34.152.109

# 5. 在服务器上更新
cd /opt/incomestreamai
cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S)
tar -xzf /tmp/update.tar.gz
rm -f /tmp/update.tar.gz

# 6. 重启应用
pkill -f "python.*main.py"
sleep 2
nohup python3 main.py > app.log 2>&1 &
```

---

## 🛠️ 常用运维命令

### 应用管理
```bash
# 查看应用状态
ps aux | grep "python.*main.py" | grep -v grep

# 查看实时日志
tail -f /opt/incomestreamai/app.log

# 重启应用
cd /opt/incomestreamai && \
  pkill -f "python.*main.py" && \
  nohup python3 main.py > app.log 2>&1 &
```

### 数据库管理
```bash
# 连接数据库
PGPASSWORD='incomeAI2024!' psql -h 127.0.0.1 -U incomestreamai_user -d incomestreamai_db

# 备份数据库
pg_dump -U incomestreamai_user incomestreamai_db > backup.sql

# 查看数据库状态
systemctl status postgresql
```

---

## 📚 相关文档

### 部署文档
- `DEPLOYMENT_GUIDE.md` - 通用部署指南
- `REMOTE_DEPLOYMENT_GUIDE.md` - 远程服务器详细部署
- `DEPLOYMENT_SUMMARY.md` - 最新部署总结
- `SYNC_GUIDE.md` - 同步指南

### 功能文档
- `HISTORY_PAGE_UPGRADE.md` - 历史页面升级说明
- `QUICK_VIEW_GUIDE.md` - 快速查看指南
- `PROJECT_CHANGELOG.md` - 完整改动日志

### 开发文档
- `README.md` - 项目基本说明
- `README_LOCAL.md` - 本地开发指南
- `LOCAL_SETUP_GUIDE.md` - 本地环境设置

---

## ⚠️ 重要注意事项

### 代码规范
- ✅ 所有代码注释和文档必须使用中文
- ✅ 所有测试/临时文件必须放在 test/ 文件夹中
- ✅ 新文件必须包含详细的中文功能说明注释
- ✅ 创建新文件后必须更新相关文档

### 部署注意事项
- ⚠️ 远程服务器**不是Git仓库**，无法使用 `git pull`
- ⚠️ 必须使用 SCP/SFTP 方式上传文件
- ⚠️ 部署前务必备份旧文件
- ⚠️ 数据库密码：`incomeAI2024!`

### 文档同步更新
当发生以下变更时，必须同步更新本文件的 changelog 板块：
1. 功能模块新增或删除
2. 数据库结构变更
3. 架构设计调整
4. 线上环境配置变化
5. 重要的部署操作

---

## 🔮 未来改进计划

- [ ] 配置 CI/CD 自动化部署
- [ ] 在远程服务器初始化Git仓库
- [ ] 使用生产级WSGI服务器（Gunicorn + Nginx）
- [ ] 配置SSL证书，支持HTTPS
- [ ] 添加应用监控和告警
- [ ] 实现自动化数据库备份

---

**文档维护**: 本文件应在每次重要改动后更新 changelog 板块
**最后更新**: 2026-01-06
**维护人员**: Claude AI Assistant

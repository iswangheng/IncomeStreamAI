# 管理员后台 - 用户数据分析功能 PRD

## 📋 产品需求文档

### 一、需求概述

在现有的管理员后台 `/admin/dashboard` 中新增"用户数据分析"标签页，提供基础的**用户列表查看**、**筛选**和**高价值用户识别**功能。

**核心目标**：
- 帮助管理员快速识别高价值用户（分析次数 > 5）
- 查看用户基本使用情况（登录次数、分析次数）
- 支持基础筛选和数据导出

---

### 二、功能设计

#### 2.1 标签页入口

**位置**: 管理员 Dashboard 添加新标签页

**导航结构**:
```
管理员 Dashboard
├── 概览（现有）
├── 用户管理（现有）
└── 📊 用户数据分析（新增）← 重点
```

**标签页图标**: `fa-chart-line` 或 `fa-users`

---

#### 2.2 页面布局

```
┌───────────────────────────────────────────────────┐
│  用户数据分析                                      │
├───────────────────────────────────────────────────┤
│  统计卡片（3个）                                   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │总用户数 │  │高价值用户│  │今日活跃 │          │
│  │  128   │  │   45    │  │   12    │          │
│  └─────────┘  └─────────┘  └─────────┘          │
├───────────────────────────────────────────────────┤
│  筛选工具栏                                        │
│  [全部用户] [高价值用户▼] [搜索: 手机号/姓名] 🔍  │
│  [导出CSV📥] [刷新🔄]                             │
├───────────────────────────────────────────────────┤
│  用户列表                                          │
│  ┌────────────────────────────────────────────┐  │
│  │手机号  │姓名 │分析次数│最后登录│状态│操作 │  │
│  ├────────────────────────────────────────────┤  │
│  │138****01│张三 │   8   │2小时前 │活跃 │详情│  │
│  │138****02│李四 │   3   │昨天   │活跃 │详情│  │
│  │139****05│王五 │   12  │今天   │高价值│详情│  │
│  │...                                       │  │
│  └────────────────────────────────────────────┘  │
│  [← 上一页]  第 1/13 页  [下一页 →]             │
└───────────────────────────────────────────────────┘
```

---

#### 2.3 功能模块

##### **模块1: 统计卡片**

显示3个核心指标：

| 指标 | 说明 | 数据来源 |
|------|------|----------|
| **总用户数** | 系统注册用户总数 | `User.query.count()` |
| **高价值用户** | 分析次数 > 3 且 7天内有登录 | `AnalysisResult` + `last_login` |
| **今日活跃** | 今天有登录或分析的用户数 | `last_login` 或分析记录时间 |

---

##### **模块2: 用户筛选**

**筛选选项**（下拉菜单）:

| 选项值 | 说明 | 筛选逻辑 |
|--------|------|----------|
| **全部用户** | 显示所有用户 | 无筛选 |
| **高价值用户** | 分析次数 > 3 且 30天内有登录 | `分析次数>3 AND last_login>=30天前` |
| **活跃用户** | 7天内有登录 | `last_login >= 7天前` |
| **沉默用户** | 30天未登录 | `last_login < 30天前` |
| **已耗尽额度** | 剩余额度 = 0 | `remaining_quota = 0` |

**高价值用户定义说明**:
- **分析次数 > 3**: 表示用户有实际使用系统，产生了价值
- **30天内有登录**: 表示用户在近期内仍然活跃，没有完全流失
- 两个条件**同时满足**，筛选出有使用量且保持一定活跃度的用户

**搜索功能**:
- 支持按手机号搜索
- 支持按姓名搜索
- 实时搜索（输入即搜索，防抖处理）

---

##### **模块3: 用户列表**

**列定义**:

| 列名 | 数据 | 说明 |
|------|------|------|
| **手机号** | `phone` | 完整显示：13800138000 |
| **姓名** | `name` | 如果未设置显示"未设置" |
| **分析次数** | COUNT(analysis_results) | 该用户创建的分析记录总数 |
| **最后登录** | `last_login` | 相对时间显示：2小时前、昨天、7天前 |
| **状态** | 标签 | 显示：高价值 / 活跃 / 沉默 / 已耗尽 |
| **操作** | 按钮 | "查看详情"按钮 |

**状态标签逻辑**:
```
高价值  = 分析次数 > 3 AND 30天内有登录（紫色标签）
活跃    = 7天内有登录（绿色标签）
沉默    = 30天未登录（灰色标签）
已耗尽  = 剩余额度 = 0（红色标签）
```

**注意**: 一个用户可以同时拥有多个标签，例如：
- 既是"高价值"又是"活跃"
- 既是"活跃"又是"已耗尽"

**排序功能**:
- 默认按分析次数降序（高价值用户排在前面）
- 支持点击列头排序（分析次数、最后登录）

**分页功能**:
- 每页显示 20 条
- 显示总数和页码
- 上一页/下一页按钮

---

##### **模块4: 用户详情弹窗**

点击"查看详情"按钮弹出模态框：

```
┌──────────────────────────────────┐
│  用户详情          [✕ 关闭]      │
├──────────────────────────────────┤
│  👤 基础信息                     │
│  ─────────────────────────────  │
│  姓名: 张三                      │
│  手机号: 13800138001             │
│  注册时间: 2025-12-01            │
│  最后登录: 2小时前               │
│                                  │
│  📊 使用数据                     │
│  ─────────────────────────────  │
│  分析次数: 8 次                  │
│  剩余额度: 2 / 10                │
│  使用率: 80%                     │
│                                  │
│  📈 最近活动（最近10条）          │
│  ─────────────────────────────  │
│  2026-01-06 09:30  AI智能客服系统 │
│  2026-01-05 14:20  在线教育平台   │
│  2025-12-28 10:15  电商平台小程序 │
│  ...                              │
│                                  │
│          [关闭]                  │
└──────────────────────────────────┘
```

**弹窗内容**:

1. **基础信息区域**
   - 用户姓名、手机号
   - 注册时间、最后登录时间

2. **使用数据区域**
   - 分析次数（总数）
   - 额度使用情况（进度条）
   - 使用率百分比

3. **最近活动区域**
   - 最近10条分析记录
   - 显示项目名称和创建时间
   - 可点击跳转到历史详情

---

##### **模块5: 数据导出**

**功能**: 导出当前筛选结果为 CSV 文件

**导出按钮**: 顶部工具栏 "导出CSV" 按钮

**导出字段**:
- 手机号
- 姓名
- 分析次数
- 剩余额度
- 使用率
- 注册时间
- 最后登录时间

**文件格式**: CSV（UTF-8编码，Excel可直接打开）

**文件名**: `users_export_YYYYMMDD_HHMMSS.csv`

---

### 三、技术实现

#### 3.1 数据库查询优化

**关键查询**（需要高效执行）:

```python
# 1. 获取用户列表（带分析次数统计）
SELECT
    u.id, u.phone, u.name, u.last_login,
    u.ai_quota, u.used_quota,
    COUNT(ar.id) as analysis_count
FROM users u
LEFT JOIN analysis_results ar ON u.id = ar.user_id
GROUP BY u.id
ORDER BY analysis_count DESC
LIMIT 20 OFFSET 0

# 2. 高价值用户筛选（分析次数 > 3 且 30天内有登录）
SELECT u.*, COUNT(ar.id) as analysis_count
FROM users u
LEFT JOIN analysis_results ar ON u.id = ar.user_id
WHERE u.last_login >= DATE('now', '-30 days')
GROUP BY u.id
HAVING COUNT(ar.id) > 3

# 3. 统计指标
SELECT
    COUNT(*) as total_users,
    SUM(CASE WHEN analysis_count > 5 THEN 1 ELSE 0 END) as high_value_users,
    SUM(CASE WHEN last_login >= DATE('now', '-7 days') THEN 1 ELSE 0 END) as active_today
FROM users u
LEFT JOIN (SELECT user_id, COUNT(*) as count FROM analysis_results GROUP BY user_id) ar
ON u.id = ar.user_id
```

**性能优化**:
- 在 `analysis_results.user_id` 添加索引（已有）
- 在 `users.last_login` 添加索引（需要添加）
- 使用数据库聚合函数，减少数据传输

---

#### 3.2 后端API设计

**新增路由**:

```python
@app.route('/admin/users-analytics')
@login_required
@admin_required
def users_analytics():
    """用户数据分析页面"""
    return render_template('admin_users_analytics.html')

@app.route('/admin/api/users/analytics/stats')
@login_required
@admin_required
def api_users_analytics_stats():
    """获取统计数据"""
    stats = {
        'total_users': User.query.count(),
        'high_value_users': # 分析次数 > 3 且 7天内有登录的用户数
        'active_today': # 今日活跃用户数
    }
    return jsonify(stats)

@app.route('/admin/api/users/analytics/list')
@login_required
@admin_required
def api_users_analytics_list():
    """获取用户列表（支持分页、筛选、排序）"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    filter_type = request.args.get('filter', 'all')  # all/high_value/active/silent
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'analysis_count')  # analysis_count/last_login

    # 返回用户列表数据
    return jsonify({
        'users': [...],
        'total': 128,
        'page': page,
        'pages': 7
    })

@app.route('/admin/api/users/<int:user_id>/detail')
@login_required
@admin_required
def api_user_detail(user_id):
    """获取用户详情"""
    user = User.query.get_or_404(user_id)
    analysis_count = AnalysisResult.query.filter_by(user_id=user_id).count()
    recent_activities = AnalysisResult.query.filter_by(user_id=user_id)\
                        .order_by(AnalysisResult.created_at.desc())\
                        .limit(10).all()

    return jsonify({
        'user': user.to_dict(),
        'analysis_count': analysis_count,
        'recent_activities': [r.to_dict() for r in recent_activities]
    })

@app.route('/admin/api/users/export')
@login_required
@admin_required
def export_users_data():
    """导出用户数据为CSV"""
    filter_type = request.args.get('filter', 'all')
    # 生成CSV文件
    # 返回文件响应
```

---

#### 3.3 前端实现

**新增文件**: `templates/admin_users_analytics.html`

**技术栈**:
- 保持现有的设计风格（Apple风格）
- 使用现有的 CSS 框架（Bootstrap 5）
- 可选：添加轻量级图表库（Chart.js）用于简单的数据可视化

**关键组件**:

1. **统计卡片组件**
```html
<div class="stats-card">
    <div class="stat-item">
        <span class="stat-number" id="total-users">-</span>
        <span class="stat-label">总用户数</span>
    </div>
</div>
```

2. **用户列表组件**
```html
<table class="table">
    <thead>
        <tr>
            <th>手机号</th>
            <th>姓名</th>
            <th class="sortable" data-sort="analysis_count">
                分析次数 <i class="fas fa-sort"></i>
            </th>
            <th>最后登录</th>
            <th>状态</th>
            <th>操作</th>
        </tr>
    </thead>
    <tbody id="users-table-body">
        <!-- 数据行通过JS动态加载 -->
    </tbody>
</table>
```

3. **用户详情弹窗**
```html
<div class="modal" id="user-detail-modal">
    <div class="modal-dialog">
        <div class="modal-content">
            <!-- 用户详情内容 -->
        </div>
    </div>
</div>
```

**JavaScript 功能**:
- 加载统计数据
- 加载用户列表（支持分页）
- 筛选和搜索
- 排序
- 用户详情弹窗
- 数据导出

---

#### 3.4 数据库索引优化

**需要添加的索引**:

```python
# 在 User 模型中添加索引
class User(db.Model):
    # ... 现有字段 ...

    __table_args__ = (
        db.Index('idx_users_last_login', 'last_login'),
        db.Index('idx_users_phone', 'phone'),
    )
```

**迁移脚本**:
```bash
# 在线上服务器执行
CREATE INDEX idx_users_last_login ON users(last_login);
```

---

### 四、界面设计细节

#### 4.1 标签页样式

**设计要求**:
- 与现有管理员后台保持一致
- 使用现有的颜色方案和组件
- 标签页激活状态明显

**实现方式**:
```html
<ul class="nav nav-tabs">
    <li class="nav-item">
        <a class="nav-link" href="/admin/dashboard">概览</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" href="/admin/users">用户管理</a>
    </li>
    <li class="nav-item">
        <a class="nav-link active" href="/admin/users-analytics">
            <i class="fas fa-chart-line"></i> 用户数据分析
        </a>
    </li>
</ul>
```

---

#### 4.2 颜色方案

**状态标签颜色**:
```css
/* 高价值用户 - 紫色 */
.badge-high-value {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}

/* 活跃用户 - 绿色 */
.badge-active {
    background: #34c759;
    color: white;
}

/* 沉默用户 - 灰色 */
.badge-silent {
    background: #8e8e93;
    color: white;
}

/* 已耗尽额度 - 红色 */
.badge-exhausted {
    background: #ff3b30;
    color: white;
}
```

---

#### 4.3 响应式设计

**移动端适配**:
- 统计卡片自动换行
- 表格支持横向滚动
- 筛选工具栏堆叠显示

---

### 五、开发计划

#### Phase 1: 核心功能（本次开发）

**优先级 P0**:
- ✅ 用户列表展示（5个字段：手机号、姓名、分析次数、最后登录、状态、操作）
- ✅ 统计卡片（3个指标：总用户数、高价值用户、今日活跃）
- ✅ 基础筛选（全部/高价值/活跃/沉默/已耗尽）
- ✅ 搜索功能（手机号/姓名）
- ✅ 排序功能（点击列头排序，默认按分析次数降序）
- ✅ 用户详情弹窗（基础信息 + 使用数据 + 最近10条活动记录）
- ✅ 数据导出（CSV格式）

**预计工作量**: 1-2天

---

#### Phase 2: 增强功能（可选）

**优先级 P1**:
- 搜索功能
- 高级筛选（时间范围）
- 排序功能
- 分页优化

**预计工作量**: 0.5-1天

---

#### Phase 3: 高级功能（暂缓）

**优先级 P2**:
- 数据可视化图表
- 用户行为趋势
- 自定义筛选规则
- 批量操作

---

### 六、验收标准

#### 功能验收

- [ ] 管理员 Dashboard 可以看到"用户数据分析"标签页
- [ ] 统计卡片正确显示3个指标数据
- [ ] 用户列表可以正确加载和显示
- [ ] 筛选功能正常工作（高价值/活跃/沉默）
- [ ] 点击"查看详情"可以弹出用户详情
- [ ] 用户详情显示正确的基础信息和使用数据
- [ ] 导出CSV功能正常工作
- [ ] 分页功能正常

#### 性能验收

- [ ] 页面加载时间 < 2秒
- [ ] 用户列表加载时间 < 1秒
- [ ] 筛选响应时间 < 500ms
- [ ] 数据库查询使用索引

#### 兼容性验收

- [ ] Chrome 浏览器正常显示
- [ ] Safari 浏览器正常显示
- [ ] 移动端基本可用

---

### 七、非功能需求

#### 安全性
- 所有接口必须验证管理员权限
- 导出功能记录操作日志

#### 可用性
- 界面简洁，操作直观
- 提供 loading 状态提示
- 错误提示友好

#### 可维护性
- 代码注释清晰
- 遵循现有代码规范
- 所有注释使用中文

---

### 八、附录

#### A. 相关文档
- 现有管理员后台代码: `app.py` line 2073-2400
- 数据库模型: `models.py`
- 用户管理页面: `templates/admin_users.html`

#### B. 参考资料
- SQLAlchemy 聚合查询文档
- Flask 分页文档
- Bootstrap 表格和模态框文档

#### C. 数据字典
- **高价值用户**: 分析次数 > 3 **且** 30天内有登录的用户（综合活跃度和使用量）
- **活跃用户**: 7天内有登录的用户
- **沉默用户**: 30天未登录的用户
- **已耗尽额度**: 剩余额度 = 0 的用户

---

**文档版本**: v1.1
**创建日期**: 2026-01-06
**最后更新**: 2026-01-06
**产品负责人**: 用户
**技术负责人**: Claude AI
**预计完成时间**: 待定

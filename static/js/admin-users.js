/* 管理中心用户管理功能 */

let currentUsersData = [];

// 加载用户数据
async function loadUsersData() {
    console.log('用户管理页面功能已初始化');

    try {
        const response = await fetch('/admin/api/users', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            currentUsersData = data.users;
            updateUserStats(data.stats);
            renderUsersTable(data.users);
        } else {
            showToast(data.message || '加载用户数据失败', 'error');
        }
    } catch (error) {
        console.error('获取用户数据失败:', error);
        showToast('获取用户数据失败，请稍后重试', 'error');

        // 显示错误状态
        document.getElementById('usersTableContainer').innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h4 class="empty-title">加载失败</h4>
                <p class="empty-description">无法获取用户数据，请检查网络连接后重试。</p>
                <button class="btn btn-primary" onclick="loadUsersData()">
                    <i class="fas fa-refresh me-2"></i>
                    重新加载
                </button>
            </div>
        `;
    }
}

// 更新用户统计数据
function updateUserStats(stats) {
    document.getElementById('total-users').textContent = stats.total;
    document.getElementById('active-users').textContent = stats.active;
    document.getElementById('admin-users').textContent = stats.admin;
    document.getElementById('recent-users').textContent = stats.recent;
}

// 渲染用户卡片列表
function renderUsersTable(users) {
    const container = document.getElementById('usersTableContainer');

    if (!users || users.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-users"></i>
                </div>
                <h3 class="empty-title">暂无用户数据</h3>
                <p class="empty-description">系统中还没有注册用户，点击添加用户开始管理。</p>
            </div>
        `;
        return;
    }

    let cardsHTML = '<div class="users-grid">';

    users.forEach((user, index) => {
        const isCurrentUser = user.current_user_id === user.id;

        cardsHTML += `
            <div class="user-card fade-in" style="animation-delay: ${index * 0.1}s;">
                <div class="user-card-header">
                    <div class="user-avatar ${user.is_admin ? 'admin' : 'user'}">
                        <i class="fas ${user.is_admin ? 'fa-user-shield' : 'fa-user'}"></i>
                    </div>
                    <div class="user-info">
                        <div class="user-name">
                            ${user.name}
                        </div>
                        <div class="user-phone">${user.phone}</div>
                    </div>
                    <div class="status-indicator ${user.is_active ? 'active' : 'inactive'}" title="${user.is_active ? '用户正常' : '用户已禁用'}">
                        <i class="fas fa-circle"></i>
                    </div>
                </div>

                <div class="user-card-body">
                    <div class="user-details">
                        <div class="detail-item">
                            <span class="detail-label">角色</span>
                            <span class="role-badge ${user.is_admin ? 'admin' : 'user'}">
                                <i class="fas ${user.is_admin ? 'fa-shield-alt' : 'fa-user'}"></i>
                                ${user.is_admin ? '管理员' : '普通用户'}
                            </span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">状态</span>
                            <span class="status-badge ${user.is_active ? 'active' : 'inactive'}">
                                <i class="fas fa-${user.is_active ? 'check-circle' : 'times-circle'}"></i>
                                ${user.is_active ? '正常' : '禁用'}
                            </span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">注册时间</span>
                            <span class="detail-value">${user.created_at || '未知'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">最后登录</span>
                            <span class="detail-value">${user.last_login || '从未登录'}</span>
                        </div>
                    </div>
                </div>

                <div class="user-card-footer">
                    <div class="action-buttons">
                        <button class="action-btn edit" onclick="editUser(${user.id})" title="编辑用户">
                            <i class="fas fa-edit"></i>
                            <span>编辑</span>
                        </button>
                        ${!isCurrentUser ? `
                            <button class="action-btn ${user.is_active ? 'disable' : 'enable'}" onclick="toggleUserStatus(${user.id}, ${!user.is_active})" title="${user.is_active ? '禁用用户' : '启用用户'}">
                                <i class="fas fa-${user.is_active ? 'ban' : 'check'}"></i>
                                <span>${user.is_active ? '禁用' : '启用'}</span>
                            </button>
                            <button class="action-btn delete" onclick="deleteUser(${user.id})" title="删除用户">
                                <i class="fas fa-trash"></i>
                                <span>删除</span>
                            </button>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });

    cardsHTML += '</div>';
    container.innerHTML = cardsHTML;
}

// 过滤用户
function filterUsers() {
    const searchTerm = document.getElementById('userSearch').value.toLowerCase();
    const statusFilter = document.getElementById('userStatusFilter').value;

    let filteredUsers = currentUsersData.filter(user => {
        const matchesSearch = user.name.toLowerCase().includes(searchTerm) || 
                             user.phone.includes(searchTerm);

        let matchesStatus = true;
        if (statusFilter === 'active') {
            matchesStatus = user.active;
        } else if (statusFilter === 'inactive') {
            matchesStatus = !user.active;
        }

        return matchesSearch && matchesStatus;
    });

    renderUsersTable(filteredUsers);
}

// 添加用户表单提交
document.addEventListener('DOMContentLoaded', function() {
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>添加中...';

            // 如果提交失败，恢复按钮状态
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-user-plus me-2"></i>添加用户';
            }, 3000);
        });
    }
});

// 导出用户数据功能
function exportUsers() {
    // 获取当前显示的用户数据
    const users = currentUsersData || [];

    if (users.length === 0) {
        showToast('暂无用户数据可导出', 'error');
        return;
    }

    // 构建CSV数据
    const headers = ['用户ID', '姓名', '手机号', '角色', '状态', '注册时间', '最后登录'];
    const csvData = [headers];

    users.forEach(user => {
        csvData.push([
            user.id,
            user.name || '',
            user.phone || '',
            user.is_admin ? '管理员' : '普通用户',
            user.active ? '活跃' : '停用',
            user.created_at || '',
            user.last_login || '从未登录'
        ]);
    });

    // 转换为CSV格式
    const csvContent = csvData.map(row => 
        row.map(field => `"${String(field).replace(/"/g, '""')}"`).join(',')
    ).join('\n');

    // 添加BOM以支持中文
    const bom = '\uFEFF';
    const blob = new Blob([bom + csvContent], { type: 'text/csv;charset=utf-8;' });

    // 创建下载链接
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);

    // 生成文件名（包含当前日期）
    const now = new Date();
    const dateStr = now.getFullYear() + 
        String(now.getMonth() + 1).padStart(2, '0') + 
        String(now.getDate()).padStart(2, '0');
    link.setAttribute('download', `用户数据导出_${dateStr}.csv`);

    // 触发下载
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    showToast(`成功导出 ${users.length} 个用户数据`, 'success');
}

// 确保函数全局可访问
window.loadUsersData = loadUsersData;
window.filterUsers = filterUsers;
window.exportUsers = exportUsers;

// 添加refreshUsers函数以处理刷新用户列表按钮
function refreshUsers() {
    if (typeof loadUsersData === 'function') {
        loadUsersData();
        showToast('用户列表已刷新', 'success');
    }
}

// 确保refreshUsers函数全局可访问
window.refreshUsers = refreshUsers;

// 优雅的Toast提示函数
function showToast(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);

    // 创建toast元素
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button onclick="this.parentElement.remove()" style="background: none; border: none; color: inherit; cursor: pointer; margin-left: auto;">
            <i class="fas fa-times"></i>
        </button>
    `;

    // 添加到页面
    document.body.appendChild(toast);

    // 自动移除
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 300);
        }
    }, 5000);
}
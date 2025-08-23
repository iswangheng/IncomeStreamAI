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

// 渲染用户表格
function renderUsersTable(users) {
    const container = document.getElementById('usersTableContainer');
    
    if (!users || users.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="fas fa-users"></i>
                </div>
                <h4 class="empty-title">暂无用户数据</h4>
                <p class="empty-description">系统中还没有注册用户。</p>
            </div>
        `;
        return;
    }

    let tableHTML = `
        <table class="data-table">
            <thead>
                <tr>
                    <th>用户信息</th>
                    <th>角色</th>
                    <th>状态</th>
                    <th>注册时间</th>
                    <th>最后登录</th>
                    <th>操作</th>
                </tr>
            </thead>
            <tbody>
    `;

    users.forEach((user, index) => {
        const isCurrentUser = user.current_user_id === user.id;
        
        tableHTML += `
            <tr class="slide-up" style="animation-delay: ${index * 0.05}s;">
                <td>
                    <div style="display: flex; align-items: center;">
                        <div style="width: 40px; height: 40px; background: ${user.is_admin ? 'var(--color-accent)' : 'var(--color-primary)'}; color: var(--color-text-inverse); border-radius: var(--radius-md); display: flex; align-items: center; justify-content: center; margin-right: var(--space-3); font-weight: var(--font-semibold);">
                            <i class="fas ${user.is_admin ? 'fa-user-shield' : 'fa-user'}"></i>
                        </div>
                        <div>
                            <div style="font-weight: var(--font-medium); color: var(--color-text-primary);">
                                ${user.name}
                                ${isCurrentUser ? '<span style="font-size: var(--text-xs); color: var(--color-primary); margin-left: var(--space-2);">(当前用户)</span>' : ''}
                            </div>
                            <div style="font-size: var(--text-xs); color: var(--color-text-secondary);">${user.phone}</div>
                        </div>
                    </div>
                </td>
                <td>
                    ${user.is_admin ? 
                        '<span class="status-badge admin">管理员</span>' : 
                        '<span class="status-badge user">普通用户</span>'
                    }
                </td>
                <td>
                    ${user.active ? 
                        '<span class="status-badge active">活跃</span>' : 
                        '<span class="status-badge paused">停用</span>'
                    }
                </td>
                <td style="color: var(--color-text-secondary);">
                    ${user.created_at || '未知'}
                </td>
                <td style="color: var(--color-text-secondary);">
                    ${user.last_login || '从未登录'}
                </td>
                <td>
                    <div class="action-buttons">
                        <a href="/admin/users/${user.id}/edit?redirect_to=dashboard" class="action-btn edit" title="编辑用户">
                            <i class="fas fa-edit"></i>
                        </a>
                        
                        ${!isCurrentUser ? `
                        <form method="post" action="/admin/users/${user.id}/delete" 
                              onsubmit="return confirm('确定要删除用户 ${user.name} 吗？此操作不可恢复！')" style="display: inline;">
                            <button type="submit" class="action-btn delete" title="删除用户">
                                <i class="fas fa-trash"></i>
                            </button>
                        </form>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    });

    tableHTML += `
            </tbody>
        </table>
    `;

    container.innerHTML = tableHTML;
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

// 确保函数全局可访问
window.loadUsersData = loadUsersData;
window.filterUsers = filterUsers;
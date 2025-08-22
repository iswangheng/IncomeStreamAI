/* ================================
   用户菜单交互逻辑
   ================================ */

document.addEventListener('DOMContentLoaded', function() {
    const userMenu = document.querySelector('.user-menu');
    const userTrigger = document.querySelector('.user-trigger');
    const userDropdown = document.querySelector('.user-dropdown');
    
    if (!userMenu || !userTrigger || !userDropdown) return;
    
    // 检测是否为触摸设备
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    if (isTouchDevice) {
        // 移动端点击切换逻辑
        userTrigger.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            userMenu.classList.toggle('active');
        });
        
        // 点击其他地方关闭菜单 - 避免与移动端菜单冲突
        document.addEventListener('click', function(e) {
            // 如果点击的是移动端菜单相关元素，不关闭用户菜单
            const mobileDropdown = document.querySelector('.mobile-dropdown');
            const mobileToggle = document.querySelector('.mobile-menu-toggle');
            const backdrop = document.querySelector('.mobile-menu-backdrop');
            
            if (mobileDropdown && mobileDropdown.classList.contains('show')) {
                return; // 移动端菜单开启时不处理
            }
            
            if (e.target === mobileToggle || (mobileToggle && mobileToggle.contains(e.target))) {
                return; // 点击移动端菜单按钮时不处理
            }
            
            if (e.target === backdrop) {
                return; // 点击移动端背景遮罩时不处理
            }
            
            if (!userMenu.contains(e.target)) {
                userMenu.classList.remove('active');
            }
        });
        
        // 阻止下拉菜单内点击事件冒泡（除了链接）
        userDropdown.addEventListener('click', function(e) {
            if (e.target.tagName !== 'A' && !e.target.closest('a')) {
                e.stopPropagation();
            } else {
                // 点击链接后关闭菜单
                userMenu.classList.remove('active');
            }
        });
    } else {
        // 桌面端鼠标悬停逻辑（CSS已处理，这里添加键盘支持）
        userTrigger.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                userMenu.classList.toggle('active');
            }
            if (e.key === 'Escape') {
                userMenu.classList.remove('active');
                userTrigger.blur();
            }
        });
        
        // 键盘导航支持
        userDropdown.addEventListener('keydown', function(e) {
            const dropdownItems = userDropdown.querySelectorAll('.dropdown-item');
            const currentIndex = Array.from(dropdownItems).indexOf(document.activeElement);
            
            switch (e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    const nextIndex = (currentIndex + 1) % dropdownItems.length;
                    dropdownItems[nextIndex].focus();
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    const prevIndex = (currentIndex - 1 + dropdownItems.length) % dropdownItems.length;
                    dropdownItems[prevIndex].focus();
                    break;
                case 'Escape':
                    e.preventDefault();
                    userMenu.classList.remove('active');
                    userTrigger.focus();
                    break;
            }
        });
    }
    
    // 添加用户头像字母生成
    const userAvatar = document.querySelector('.user-avatar');
    const userName = document.querySelector('.user-name');
    
    if (userAvatar && userName) {
        const name = userName.textContent.trim();
        if (name) {
            // 取姓名的第一个字符作为头像
            const firstChar = name.charAt(0).toUpperCase();
            userAvatar.textContent = firstChar;
        } else {
            // 默认头像图标
            userAvatar.innerHTML = '<i class="fas fa-user"></i>';
        }
    }
    
    // 添加菜单项点击反馈
    const dropdownItems = document.querySelectorAll('.dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', function() {
            // 添加点击效果
            this.style.transform = 'scale(0.98)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
    
    // 为菜单项添加波纹效果
    dropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            ripple.classList.add('ripple-effect');
            
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.style.position = 'absolute';
            ripple.style.borderRadius = '50%';
            ripple.style.background = 'rgba(255, 255, 255, 0.5)';
            ripple.style.transform = 'scale(0)';
            ripple.style.animation = 'ripple-animation 0.6s linear';
            ripple.style.pointerEvents = 'none';
            
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// 添加波纹动画样式
const style = document.createElement('style');
style.textContent = `
@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}
`;
document.head.appendChild(style);
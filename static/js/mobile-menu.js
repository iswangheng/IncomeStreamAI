
document.addEventListener('DOMContentLoaded', function() {
    console.log('Mobile menu functions initialized');
    
    // 移动端菜单切换函数
    function toggleMobileMenu() {
        console.log('Toggle mobile menu called from dashboard');
        const dropdown = document.querySelector('.mobile-dropdown');
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        
        if (dropdown && menuToggle) {
            const isVisible = dropdown.classList.contains('show');
            
            if (isVisible) {
                dropdown.classList.remove('show');
                dropdown.style.display = 'none';
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
                console.log('Menu closed');
                // 移除背景遮罩
                removeBackdrop();
            } else {
                dropdown.classList.add('show');
                // 强制设置显示样式
                dropdown.style.display = 'block';
                dropdown.style.position = 'fixed';
                dropdown.style.top = '64px';
                dropdown.style.zIndex = '2147483647';
                dropdown.style.visibility = 'visible';
                dropdown.style.opacity = '1';
                dropdown.style.pointerEvents = 'auto';
                
                menuToggle.innerHTML = '<i class="fas fa-times"></i>';
                console.log('Menu opened - forced styles applied');
                // 添加背景遮罩
                addBackdrop();
                
                // 调试信息
                const rect = dropdown.getBoundingClientRect();
                console.log('Dropdown position:', rect);
                console.log('Dropdown computed styles:', window.getComputedStyle(dropdown));
            }
        } else {
            console.log('Dropdown or menuToggle not found');
        }
    }
    
    // 添加背景遮罩
    function addBackdrop() {
        let backdrop = document.querySelector('.mobile-menu-backdrop');
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.className = 'mobile-menu-backdrop';
            backdrop.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.4);
                z-index: 2147483646;
                backdrop-filter: blur(3px);
                -webkit-backdrop-filter: blur(3px);
                transform: translateZ(0);
                -webkit-transform: translateZ(0);
            `;
            backdrop.addEventListener('click', toggleMobileMenu);
            backdrop.addEventListener('touchstart', toggleMobileMenu);
            document.body.appendChild(backdrop);
            
            // 禁止背景滚动
            document.body.style.overflow = 'hidden';
        }
    }
    
    // 移除背景遮罩
    function removeBackdrop() {
        const backdrop = document.querySelector('.mobile-menu-backdrop');
        if (backdrop) {
            backdrop.remove();
            // 恢复背景滚动
            document.body.style.overflow = '';
        }
    }
    
    // 绑定汉堡菜单点击事件
    const menuToggle = document.querySelector('.mobile-menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMobileMenu();
        });
    }
    
    // 点击菜单项后关闭菜单
    const dropdownItems = document.querySelectorAll('.mobile-dropdown .dropdown-item');
    dropdownItems.forEach(item => {
        item.addEventListener('click', function() {
            const dropdown = document.querySelector('.mobile-dropdown');
            const menuToggle = document.querySelector('.mobile-menu-toggle');
            
            if (dropdown && menuToggle) {
                dropdown.classList.remove('show');
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
                removeBackdrop();
            }
        });
    });
    
    // 全局暴露函数供其他脚本使用
    window.toggleMobileMenu = toggleMobileMenu;
    
    // 处理窗口大小变化
    window.addEventListener('resize', function() {
        if (window.innerWidth > 768) {
            const dropdown = document.querySelector('.mobile-dropdown');
            const menuToggle = document.querySelector('.mobile-menu-toggle');
            
            if (dropdown && menuToggle) {
                dropdown.classList.remove('show');
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
                removeBackdrop();
            }
        }
    });
});

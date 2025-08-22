
document.addEventListener('DOMContentLoaded', function() {
    console.log('Mobile menu functions initialized');
    
    // 移动端菜单切换函数
    let isToggling = false; // 防止重复调用
    
    function toggleMobileMenu() {
        if (isToggling) {
            console.log('Toggle already in progress, skipping');
            return;
        }
        
        isToggling = true;
        setTimeout(() => { isToggling = false; }, 300); // 防抖
        
        console.log('Toggle mobile menu called');
        const dropdown = document.querySelector('.mobile-dropdown');
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        
        if (dropdown && menuToggle) {
            const isVisible = dropdown.classList.contains('show');
            
            if (isVisible) {
                dropdown.classList.remove('show');
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
                console.log('Menu closed');
            } else {
                dropdown.classList.add('show');
                menuToggle.innerHTML = '<i class="fas fa-times"></i>';
                console.log('Menu opened');
            }
        } else {
            console.log('Dropdown or menuToggle not found');
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
            }
        });
    });
    
    // 点击页面其他地方关闭菜单
    document.addEventListener('click', function(e) {
        const dropdown = document.querySelector('.mobile-dropdown');
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        
        if (dropdown && menuToggle && dropdown.classList.contains('show')) {
            // 如果点击的不是菜单或菜单按钮，则关闭菜单
            if (!dropdown.contains(e.target) && !menuToggle.contains(e.target)) {
                dropdown.classList.remove('show');
                menuToggle.innerHTML = '<i class="fas fa-bars"></i>';
            }
        }
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
            }
        }
    });
});

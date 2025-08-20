/**
 * Angela AI - 未来科幻增强交互效果
 * Future-Enhanced Interactive Effects
 * 高端大气上档次的交互动画和特效
 */

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', function() {
    
    // 初始化所有增强效果
    initEnhancedEffects();
    initScrollAnimations();
    initParticleEffects();
    initHoverEffects();
    initLoadingAnimations();
    
});

/**
 * 初始化增强效果
 */
function initEnhancedEffects() {
    // 移除预加载动画类
    setTimeout(() => {
        document.body.classList.remove('preload-animations');
    }, 100);
    
    // 添加GPU加速类到关键元素
    const interactiveElements = document.querySelectorAll('.interactive, .card, .btn');
    interactiveElements.forEach(el => {
        el.classList.add('gpu-accelerated');
    });
}

/**
 * 初始化滚动动画
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                entry.target.classList.add('animate-in-view');
            }
        });
    }, observerOptions);
    
    // 观察所有动画元素
    const animatedElements = document.querySelectorAll('.fade-in, .slide-up, .scale-in');
    animatedElements.forEach(el => {
        el.style.animationPlayState = 'paused';
        observer.observe(el);
    });
}

/**
 * 初始化粒子效果
 */
function initParticleEffects() {
    // 创建浮动粒子容器
    const particleContainer = document.createElement('div');
    particleContainer.className = 'particle-container';
    particleContainer.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: -1;
        overflow: hidden;
    `;
    document.body.appendChild(particleContainer);
    
    // 创建粒子
    for (let i = 0; i < 20; i++) {
        createParticle(particleContainer);
    }
}

/**
 * 创建单个粒子
 */
function createParticle(container) {
    const particle = document.createElement('div');
    const size = Math.random() * 4 + 1;
    const colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe'];
    const color = colors[Math.floor(Math.random() * colors.length)];
    
    particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: ${color};
        border-radius: 50%;
        opacity: ${Math.random() * 0.6 + 0.2};
        box-shadow: 0 0 ${size * 2}px ${color};
    `;
    
    // 随机位置
    particle.style.left = Math.random() * 100 + '%';
    particle.style.top = Math.random() * 100 + '%';
    
    container.appendChild(particle);
    
    // 添加浮动动画
    animateParticle(particle);
}

/**
 * 粒子动画
 */
function animateParticle(particle) {
    const duration = Math.random() * 20000 + 10000; // 10-30秒
    const startX = parseInt(particle.style.left);
    const startY = parseInt(particle.style.top);
    const endX = Math.random() * 100;
    const endY = Math.random() * 100;
    
    particle.animate([
        {
            transform: `translate(0, 0) scale(1)`,
            opacity: particle.style.opacity
        },
        {
            transform: `translate(${(endX - startX) * 3}px, ${(endY - startY) * 3}px) scale(0.5)`,
            opacity: 0
        }
    ], {
        duration: duration,
        easing: 'ease-in-out',
        fill: 'forwards'
    }).onfinish = () => {
        // 重新开始动画
        particle.style.left = Math.random() * 100 + '%';
        particle.style.top = Math.random() * 100 + '%';
        particle.style.opacity = Math.random() * 0.6 + 0.2;
        setTimeout(() => animateParticle(particle), Math.random() * 2000);
    };
}

/**
 * 初始化悬浮效果
 */
function initHoverEffects() {
    // 卡片悬浮发光效果
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
            this.style.filter = 'brightness(1.05)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.filter = 'brightness(1)';
        });
    });
    
    // 按钮波纹效果
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            createRippleEffect(e, this);
        });
    });
    
    // 输入框焦点效果
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('input-focused');
            createFocusGlow(this);
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('input-focused');
            removeFocusGlow(this);
        });
    });
}

/**
 * 创建波纹效果
 */
function createRippleEffect(event, element) {
    const ripple = document.createElement('div');
    const rect = element.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
    `;
    
    // 添加波纹动画样式
    if (!document.getElementById('ripple-styles')) {
        const style = document.createElement('style');
        style.id = 'ripple-styles';
        style.textContent = `
            @keyframes ripple {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    element.style.position = 'relative';
    element.style.overflow = 'hidden';
    element.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

/**
 * 创建焦点发光效果
 */
function createFocusGlow(element) {
    const glow = document.createElement('div');
    glow.className = 'focus-glow';
    glow.style.cssText = `
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #667eea, #764ba2, #f093fb, #4facfe);
        border-radius: inherit;
        z-index: -1;
        opacity: 0;
        animation: glowPulse 1.5s ease-in-out infinite alternate;
    `;
    
    // 添加发光动画样式
    if (!document.getElementById('glow-styles')) {
        const style = document.createElement('style');
        style.id = 'glow-styles';
        style.textContent = `
            @keyframes glowPulse {
                0% { opacity: 0.3; transform: scale(1); }
                100% { opacity: 0.7; transform: scale(1.02); }
            }
        `;
        document.head.appendChild(style);
    }
    
    element.parentElement.style.position = 'relative';
    element.parentElement.appendChild(glow);
}

/**
 * 移除焦点发光效果
 */
function removeFocusGlow(element) {
    const glow = element.parentElement.querySelector('.focus-glow');
    if (glow) {
        glow.style.animation = 'none';
        glow.style.opacity = '0';
        setTimeout(() => glow.remove(), 300);
    }
}

/**
 * 初始化加载动画
 */
function initLoadingAnimations() {
    // 页面加载完成后的入场动画
    const pageElements = document.querySelectorAll('.fade-in, .slide-up, .scale-in');
    pageElements.forEach((element, index) => {
        element.style.animationDelay = (index * 0.1) + 's';
    });
    
    // 为表单提交添加加载效果
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // 检查是否是个人资料或修改密码页面的表单
            if (window.location.pathname.includes('/profile') || 
                window.location.pathname.includes('/change_password')) {
                showSimpleLoadingOverlay();
            } else {
                showLoadingOverlay();
            }
        });
    });
}

/**
 * 显示加载覆盖层
 */
function showLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="loading-content">
            <div class="loading-spinner"></div>
            <div class="loading-text">
                <h3>AI正在智能分析</h3>
                <p>请稍候，正在生成专业的收入管道方案...</p>
            </div>
        </div>
    `;
    
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.8);
        backdrop-filter: blur(10px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        animation: fadeIn 0.5s ease-out forwards;
    `;
    
    // 添加加载动画样式
    if (!document.getElementById('loading-styles')) {
        const style = document.createElement('style');
        style.id = 'loading-styles';
        style.textContent = `
            .loading-content {
                text-align: center;
                color: white;
            }
            
            .loading-spinner {
                width: 60px;
                height: 60px;
                border: 3px solid rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                border-top: 3px solid #667eea;
                animation: spin 1s linear infinite;
                margin: 0 auto 2rem;
            }
            
            .loading-text h3 {
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #667eea, #f093fb);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .loading-text p {
                opacity: 0.8;
                font-size: 1rem;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes fadeIn {
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(overlay);
}

// 简单的加载状态，用于个人资料等非AI分析场景
function showSimpleLoadingOverlay() {
    const overlay = document.createElement('div');
    overlay.className = 'simple-loading-overlay';
    overlay.innerHTML = `
        <div class="simple-loading-content">
            <div class="simple-loading-spinner"></div>
        </div>
    `;
    
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(5px);
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        animation: fadeIn 0.3s ease-out forwards;
    `;
    
    // 添加简单加载动画样式
    if (!document.getElementById('simple-loading-styles')) {
        const style = document.createElement('style');
        style.id = 'simple-loading-styles';
        style.textContent = `
            .simple-loading-content {
                text-align: center;
            }
            
            .simple-loading-spinner {
                width: 40px;
                height: 40px;
                border: 3px solid rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                border-top: 3px solid #007AFF;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            @keyframes fadeIn {
                to { opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(overlay);
}

// 鼠标跟随光标效果已移除，使用普通鼠标样式

/**
 * 性能优化：节流函数
 */
function throttle(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * 响应式处理
 */
function handleResize() {
    const isMobile = window.innerWidth <= 768;
    
    if (isMobile) {
        // 移动设备优化
        document.body.classList.add('mobile-optimized');
    } else {
        document.body.classList.remove('mobile-optimized');
    }
}

// 响应式处理
window.addEventListener('resize', throttle(handleResize, 250));
handleResize(); // 初始调用
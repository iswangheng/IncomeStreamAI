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

    // 为表单提交添加加载效果，但排除特定表单
    const forms = document.querySelectorAll('form:not(.no-loading-overlay)');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            showSimpleLoadingOverlay();
        });
    });
}

/**
 * 显示消息提示（5秒自动消失）
 */
function showToast(message, type = 'info', duration = 5000) {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <div class="toast-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="removeToastElement(this.parentElement.parentElement)">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;

    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        min-width: 300px;
        background: ${type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#d1ecf1'};
        color: ${type === 'success' ? '#155724' : type === 'error' ? '#721c24' : '#0c5460'};
        border: 1px solid ${type === 'success' ? '#c3e6cb' : type === 'error' ? '#f5c6cb' : '#bee5eb'};
        border-radius: 8px;
        padding: 12px 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        opacity: 0;
        transform: translateX(100%);
        transition: all 0.3s ease;
    `;

    document.body.appendChild(toast);

    // 触发入场动画
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);

    // 自动消失
    setTimeout(() => {
        removeToastElement(toast);
    }, duration);
}

/**
 * 移除Toast元素的辅助函数
 */
function removeToastElement(toastElement) {
    if (toastElement && toastElement.parentNode) {
        toastElement.style.opacity = '0';
        toastElement.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.remove();
            }
        }, 300);
    }
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

/**
 * 初始化所有交互功能
 */
function initializeInteractions() {
    console.log('交互功能已初始化');

    // 确保所有交互元素都已初始化
    initEnhancedEffects();

    // 添加点击反馈效果
    const interactiveElements = document.querySelectorAll('.interactive, .btn');
    interactiveElements.forEach(element => {
        element.addEventListener('click', function() {
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
}

// 页面加载完成后初始化
        document.addEventListener('DOMContentLoaded', function() {
            initializeInteractions();
        });

        // 移动端字段编辑函数
        function editPersonField(personIndex, fieldType) {
            // 触发编辑人物的模态框
            const editButton = document.querySelector(`[onclick="editPerson(${personIndex})"]`);
            if (editButton) {
                editButton.click();

                // 延迟聚焦到对应字段
                setTimeout(() => {
                    let targetField;
                    if (fieldType === 'resources') {
                        targetField = document.querySelector('#editPersonModal textarea[placeholder*="资源"]');
                    } else if (fieldType === 'needs') {
                        targetField = document.querySelector('#editPersonModal textarea[placeholder*="需求"], #editPersonModal textarea[placeholder*="高兴"]');
                    }

                    if (targetField) {
                        targetField.focus();
                        targetField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }, 300);
            }
        }

// 优雅的确认弹窗函数 - 全局使用
function showElegantConfirm(message, onConfirm, onCancel = null) {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'elegant-confirm-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;

    // 创建确认框
    const confirmBox = document.createElement('div');
    confirmBox.className = 'elegant-confirm-box';
    confirmBox.style.cssText = `
        background: white;
        border-radius: 20px;
        padding: 32px;
        max-width: 420px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        transform: scale(0.9) translateY(20px);
        transition: all 0.3s ease;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

    // 创建图标
    const icon = document.createElement('div');
    icon.innerHTML = '<i class="fas fa-question-circle"></i>';
    icon.style.cssText = `
        font-size: 48px;
        color: #FF9500;
        margin-bottom: 20px;
        animation: bounceIn 0.6s ease;
    `;

    // 创建消息
    const messageEl = document.createElement('div');
    messageEl.textContent = message;
    messageEl.style.cssText = `
        font-size: 18px;
        color: #1d1d1f;
        line-height: 1.4;
        margin-bottom: 28px;
        font-weight: 500;
    `;

    // 创建按钮容器
    const buttonContainer = document.createElement('div');
    buttonContainer.style.cssText = `
        display: flex;
        gap: 12px;
        justify-content: center;
    `;

    // 取消按钮
    const cancelBtn = document.createElement('button');
    cancelBtn.textContent = '取消';
    cancelBtn.style.cssText = `
        background: #f5f5f5;
        color: #666;
        border: none;
        border-radius: 12px;
        padding: 14px 24px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        min-width: 80px;
    `;

    // 确定按钮
    const confirmBtn = document.createElement('button');
    confirmBtn.textContent = '确定';
    confirmBtn.style.cssText = `
        background: #FF3B30;
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 24px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        min-width: 80px;
    `;

    // 按钮悬停效果
    cancelBtn.onmouseenter = () => {
        cancelBtn.style.background = '#ebebeb';
        cancelBtn.style.transform = 'translateY(-1px)';
    };
    cancelBtn.onmouseleave = () => {
        cancelBtn.style.background = '#f5f5f5';
        cancelBtn.style.transform = 'translateY(0)';
    };

    confirmBtn.onmouseenter = () => {
        confirmBtn.style.background = '#ff2d20';
        confirmBtn.style.transform = 'translateY(-1px)';
        confirmBtn.style.boxShadow = '0 8px 25px rgba(255, 59, 48, 0.4)';
    };
    confirmBtn.onmouseleave = () => {
        confirmBtn.style.background = '#FF3B30';
        confirmBtn.style.transform = 'translateY(0)';
        confirmBtn.style.boxShadow = 'none';
    };

    // 关闭弹窗函数
    const closeConfirm = () => {
        overlay.style.opacity = '0';
        confirmBox.style.transform = 'scale(0.9) translateY(20px)';
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.remove();
            }
        }, 300);
    };

    // 事件监听
    cancelBtn.onclick = () => {
        closeConfirm();
        if (onCancel) onCancel();
    };

    confirmBtn.onclick = () => {
        closeConfirm();
        setTimeout(() => {
            if (onConfirm) onConfirm();
        }, 100);
    };

    overlay.onclick = (e) => {
        if (e.target === overlay) {
            closeConfirm();
            if (onCancel) onCancel();
        }
    };

    // 添加动画样式
    if (!document.getElementById('elegant-global-styles')) {
        const style = document.createElement('style');
        style.id = 'elegant-global-styles';
        style.textContent = `
            @keyframes bounceIn {
                0% { transform: scale(0.3); opacity: 0; }
                50% { transform: scale(1.05); }
                70% { transform: scale(0.9); }
                100% { transform: scale(1); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }

    // 组装确认框
    buttonContainer.appendChild(cancelBtn);
    buttonContainer.appendChild(confirmBtn);

    confirmBox.appendChild(icon);
    confirmBox.appendChild(messageEl);
    confirmBox.appendChild(buttonContainer);
    overlay.appendChild(confirmBox);
    document.body.appendChild(overlay);

    // 显示动画
    setTimeout(() => {
        overlay.style.opacity = '1';
        confirmBox.style.transform = 'scale(1) translateY(0)';
    }, 10);

    // ESC键关闭
    const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            closeConfirm();
            if (onCancel) onCancel();
            document.removeEventListener('keydown', handleKeyDown);
        }
    };
    document.addEventListener('keydown', handleKeyDown);
}

// 优雅的提示弹窗函数 - 全局使用
function showElegantAlert(message, type = 'info') {
    // 创建遮罩层
    const overlay = document.createElement('div');
    overlay.className = 'elegant-alert-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: 0;
        transition: opacity 0.3s ease;
    `;

    // 创建弹窗
    const alertBox = document.createElement('div');
    alertBox.className = 'elegant-alert-box';
    alertBox.style.cssText = `
        background: white;
        border-radius: 20px;
        padding: 32px;
        max-width: 420px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        transform: scale(0.9) translateY(20px);
        transition: all 0.3s ease;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;

    // 图标配置
    const iconConfig = {
        success: { icon: 'check-circle', color: '#34C759' },
        error: { icon: 'exclamation-triangle', color: '#FF3B30' },
        warning: { icon: 'exclamation-circle', color: '#FF9500' },
        info: { icon: 'info-circle', color: '#007AFF' }
    };

    const config = iconConfig[type] || iconConfig.info;

    // 创建内容
    const icon = document.createElement('div');
    icon.innerHTML = `<i class="fas fa-${config.icon}"></i>`;
    icon.style.cssText = `
        font-size: 48px;
        color: ${config.color};
        margin-bottom: 20px;
        animation: bounceIn 0.6s ease;
    `;

    const messageEl = document.createElement('div');
    messageEl.textContent = message;
    messageEl.style.cssText = `
        font-size: 18px;
        color: #1d1d1f;
        line-height: 1.4;
        margin-bottom: 28px;
        font-weight: 500;
    `;

    const button = document.createElement('button');
    button.textContent = '确定';
    button.style.cssText = `
        background: ${config.color};
        color: white;
        border: none;
        border-radius: 12px;
        padding: 14px 32px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        min-width: 100px;
    `;

    // 按钮悬停效果
    button.onmouseenter = () => {
        button.style.transform = 'translateY(-2px)';
        button.style.boxShadow = `0 8px 25px ${config.color}40`;
    };
    button.onmouseleave = () => {
        button.style.transform = 'translateY(0)';
        button.style.boxShadow = 'none';
    };

    // 关闭弹窗函数
    const closeAlert = () => {
        overlay.style.opacity = '0';
        alertBox.style.transform = 'scale(0.9) translateY(20px)';
        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.remove();
            }
        }, 300);
    };

    // 事件监听
    button.onclick = closeAlert;
    overlay.onclick = (e) => {
        if (e.target === overlay) closeAlert();
    };

    // 组装弹窗
    alertBox.appendChild(icon);
    alertBox.appendChild(messageEl);
    alertBox.appendChild(button);
    overlay.appendChild(alertBox);
    document.body.appendChild(overlay);

    // 显示动画
    setTimeout(() => {
        overlay.style.opacity = '1';
        alertBox.style.transform = 'scale(1) translateY(0)';
    }, 10);

    // ESC键关闭
    const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            closeAlert();
            document.removeEventListener('keydown', handleKeyDown);
        }
    };
    document.addEventListener('keydown', handleKeyDown);
}

// 确保所有函数全局可访问
window.showElegantConfirm = showElegantConfirm;
window.showElegantAlert = showElegantAlert;
/**
 * 页面跳转加载状态管理
 * Apple风格的全页面加载效果
 */

class PageLoadingManager {
    constructor() {
        this.loadingOverlay = null;
        this.isLoading = false;
        this.loadingTimeout = null;
        this.minLoadingTime = 300; // 最小显示时间，避免闪烁
        this.maxLoadingTime = 10000; // 最大加载时间，防止卡住
        
        this.init();
    }

    init() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }

        // 监听页面加载完成事件
        window.addEventListener('load', () => this.hideLoading());
        
        // 监听浏览器前进后退
        window.addEventListener('pageshow', (event) => {
            if (event.persisted) {
                this.hideLoading();
            }
        });
    }

    setupEventListeners() {
        this.loadingOverlay = document.getElementById('pageLoadingOverlay');
        
        if (!this.loadingOverlay) {
            console.warn('页面加载覆盖层未找到');
            return;
        }

        // 为所有导航链接添加加载效果
        this.attachLoadingToLinks();
        
        // 为表单提交添加加载效果
        this.attachLoadingToForms();
    }

    attachLoadingToLinks() {
        // 选择所有需要加载效果的链接
        const selectors = [
            'nav a[href]:not([href^="#"]):not([href^="javascript:"]):not(.no-loading)',
            '.dropdown-item[href]:not([href^="#"]):not([href^="javascript:"]):not(.no-loading)',
            'a[href]:not([href^="#"]):not([href^="javascript:"]):not(.external):not(.no-loading)'
        ];

        selectors.forEach(selector => {
            const links = document.querySelectorAll(selector);
            links.forEach(link => {
                // 跳过外部链接
                if (this.isExternalLink(link.href)) return;
                
                link.addEventListener('click', (e) => {
                    // 检查是否是有效的导航链接
                    if (this.shouldShowLoading(link, e)) {
                        this.showLoading();
                    }
                });
            });
        });
    }

    attachLoadingToForms() {
        const forms = document.querySelectorAll('form:not(.no-loading)');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                // 如果是AJAX表单，不显示页面加载
                if (form.classList.contains('ajax-form')) return;
                
                this.showLoading();
            });
        });
    }

    shouldShowLoading(link, event) {
        // 检查是否按住了修饰键（新窗口打开）
        if (event.metaKey || event.ctrlKey || event.shiftKey) return false;
        
        // 检查是否是右键点击
        if (event.button !== 0) return false;
        
        // 检查是否有阻止默认行为
        if (event.defaultPrevented) return false;
        
        // 检查是否是当前页面
        if (link.href === window.location.href) return false;
        
        return true;
    }

    isExternalLink(href) {
        try {
            const url = new URL(href, window.location.href);
            return url.hostname !== window.location.hostname;
        } catch (e) {
            return false;
        }
    }

    showLoading() {
        if (this.isLoading || !this.loadingOverlay) return;
        
        this.isLoading = true;
        
        // 清除之前的定时器
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
        }
        
        // 显示加载覆盖层
        this.loadingOverlay.classList.add('show');
        
        // 设置最大加载时间保护
        this.loadingTimeout = setTimeout(() => {
            this.hideLoading();
        }, this.maxLoadingTime);
        
        // 添加body类防止滚动
        document.body.classList.add('page-loading');
    }

    hideLoading() {
        if (!this.isLoading || !this.loadingOverlay) return;
        
        // 确保最小显示时间
        setTimeout(() => {
            this.isLoading = false;
            this.loadingOverlay.classList.remove('show');
            document.body.classList.remove('page-loading');
            
            // 清除定时器
            if (this.loadingTimeout) {
                clearTimeout(this.loadingTimeout);
                this.loadingTimeout = null;
            }
        }, this.minLoadingTime);
    }

    // 手动控制加载状态的方法
    static show() {
        if (window.pageLoadingManager) {
            window.pageLoadingManager.showLoading();
        }
    }

    static hide() {
        if (window.pageLoadingManager) {
            window.pageLoadingManager.hideLoading();
        }
    }
}

// 创建全局实例
window.pageLoadingManager = new PageLoadingManager();

// 提供全局方法
window.showPageLoading = () => PageLoadingManager.show();
window.hidePageLoading = () => PageLoadingManager.hide();

console.log('页面加载状态管理器已初始化');
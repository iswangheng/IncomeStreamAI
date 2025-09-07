/**
 * 页面跳转加载状态管理
 * Apple风格的全页面加载效果
 */

class PageLoadingManager {
    constructor() {
        this.loadingOverlay = null;
        this.isLoading = false;
        this.loadingTimeout = null;
        this.maxLoadingTime = 8000; // 最大加载时间，防止卡住
        this.loadingStartTime = 0;
        
        this.init();
    }

    init() {
        // 等待DOM加载完成
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setupEventListeners());
        } else {
            this.setupEventListeners();
        }

        // 监听页面完全加载完成事件
        window.addEventListener('load', () => {
            // 延迟一点确保页面完全渲染
            setTimeout(() => this.hideLoading(), 50);
        });
        
        // 监听页面显示事件（包括从缓存恢复）
        window.addEventListener('pageshow', (event) => {
            setTimeout(() => this.hideLoading(), 50);
        });

        // 监听DOM内容加载完成
        if (document.readyState === 'complete') {
            setTimeout(() => this.hideLoading(), 50);
        }
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
        this.loadingStartTime = Date.now();
        
        // 清除之前的定时器
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
        }
        
        // 立即显示加载覆盖层
        this.loadingOverlay.classList.add('show');
        
        // 设置最大加载时间保护
        this.loadingTimeout = setTimeout(() => {
            console.warn('页面加载超时，强制隐藏加载动画');
            this.hideLoading();
        }, this.maxLoadingTime);
        
        // 添加body类防止滚动
        document.body.classList.add('page-loading');
    }

    hideLoading() {
        if (!this.isLoading || !this.loadingOverlay) return;
        
        const loadingDuration = Date.now() - this.loadingStartTime;
        
        // 立即隐藏，不需要最小时间延迟
        this.isLoading = false;
        this.loadingOverlay.classList.remove('show');
        document.body.classList.remove('page-loading');
        
        // 清除定时器
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
            this.loadingTimeout = null;
        }
        
        console.log(`页面加载完成，耗时: ${loadingDuration}ms`);
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
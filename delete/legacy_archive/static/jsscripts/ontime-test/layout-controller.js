/**
 * 布局控制器 - 处理页面布局相关的功能
 */
export const layoutController = {
    /**
     * 调整内容高度以确保始终填满页面
     */
    adjustContentHeight() {
        // 获取各个关键元素
        const leftSection = document.querySelector('.left-section .section-content');
        const rightSection = document.querySelector('.right-section .section-content');
        const header = document.querySelector('.section-header');
        
        if (leftSection && rightSection && header) {
            const headerHeight = header.offsetHeight;
            const windowHeight = window.innerHeight;
            const contentHeight = windowHeight - headerHeight;
            
            // 设置内容区域高度
            leftSection.style.height = `${contentHeight}px`;
            rightSection.style.height = `${contentHeight}px`;
        }
    },
    
    /**
     * 初始化布局
     */
    init() {
        // 添加窗口大小调整监听器
        window.addEventListener('resize', this.adjustContentHeight);
        
        // 初始调整
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(this.adjustContentHeight, 100);
        });
        
        // 如果DOM已经加载完成，则立即执行
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(this.adjustContentHeight, 100);
        }
    },
    
    /**
     * 清理事件监听器
     */
    cleanup() {
        window.removeEventListener('resize', this.adjustContentHeight);
    }
};

// 自动初始化
layoutController.init();

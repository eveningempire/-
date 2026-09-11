import { layoutController } from '/static/jsscripts/ontime-test/layout-controller.js';

export const uiController = {
    // 在需要重新调整布局的地方调用
    adjustLayout() {
        layoutController.adjustContentHeight();
    }
};

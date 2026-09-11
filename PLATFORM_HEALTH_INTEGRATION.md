# 平台健康评估算法集成说明

已将 `platform_handoff_20260911_v1/health_bundle` 以独立服务方式接入 Django。

## 接口

- `GET /api/v1/health-assessment/status/`：检查算法包和模型是否可用
- `POST /api/v1/health-assessment/evaluate/`：提交一条窗口证据
- `POST /api/v1/health-assessment/batch/`：提交 JSON 数组或 `{lines: [...]}`
- `POST /api/v1/health-assessment/summary/`：获取会话 weakest-link proxy 汇总
- `POST /api/v1/health-assessment/reset/`：清理会话状态

前端入口为 `/platform-health`。输入必须是算法包规定的窗口级证据，不是原始遥测；标签字段会被拒绝。告警当前按交付包约束保持 `ABSTAIN`，定位为开发状态，不能作为安全控制依据。

## 配置

默认从项目上两级目录读取 `platform_handoff_20260911_v1`。部署时可设置 `PHM_PLATFORM_HANDOFF_DIR`；设置 `PHM_HEALTH_ASSESSMENT_ENABLED=false` 可关闭加载。模型依赖缺失时 Django 仍可启动，状态接口会返回原因。

交付包模型引用了原训练模块名，项目内 `health_assessment/p1_v3_strict/candidates.py` 提供了反序列化兼容层；它不改变模型文件，也不宣称重新训练或提升算法资质。

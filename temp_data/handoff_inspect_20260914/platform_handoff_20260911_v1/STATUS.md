# 平台就绪度摘要

| 模块 | 当前级别 | 可做 | 不可做/待补 |
|---|---|---|---|
| 健康评估 | Integration-ready development | 加载 bundle、校验 schema、生成组件 HI/定位输出、弃权 | 原始遥测端到端、安全报警、正式 P1 冻结 |
| RUL P1 bundle | Shadow only | 接口、加载、延迟和日志联调 | 真实 RUL 声称、决策触发 |
| RUL LOX bundle | Shadow only | 与 409 数据 LOX 特征 schema 的影子链路 | 物理寿命验收、泛化结论 |
| 数据合同 | Proxy-only | 数据适配、删失声明和防泄漏校验 | 监督 RUL 训练：409 数据全删失 |

平台第一阶段的验收标准应是：合同校验正确、模型可重复加载、错误输入明确拒绝、输出全部带 provenance，并且强制保持 shadow/非 actionable 标志。

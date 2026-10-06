# 寿命预测模块

平台提供两类寿命预测接口:

- `rul_service`:调用交付包中的 health-main 集成模型,输入含 `HI_norm`、`HI` 或 `health_index` 的 CSV,输出 RUL,单位为小时(h)。
- `lifetime_prediction`:保留原 CMG 寿命预测接口,用于兼容历史页面和数据库数据。

新部署请优先从平台"寿命预测"页面调用 health-main 集成模型。训练模型至少需要 51 行健康指数数据;数据不足或缺少 HI 列时,接口会返回明确提示。

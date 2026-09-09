# 项目范围与材料要求映射

| 材料要求 | 当前骨架位置 | 状态 |
| --- | --- | --- |
| 状态监测、健康评估、寿命预测 | `health_management/`、`lifetime_prediction/`、`phm/` | 接口占位 |
| 故障模式与结构模型、MSFG | `rule_detection/`、`msfg_analysis/` | 沿用 CMG 模块 |
| 数据接入、存储、导出 | `data_management/` | 沿用 CMG 模块 |
| 告警、消息和权限 | `health_management/`、`users/` | 沿用 CMG 模块 |
| B/S 可视化 | `frontend/`、`static/` | 沿用 CMG 入口 |
| 算法与仿真数据 | `phm/domain_contracts.py` | 暂不实现/不提供 |

用户请求中的“算法和仿真数据先不用处理”优先于材料中对最终交付物的描述；材料内容仅用于确定模块边界，不视为本阶段必须实现的功能。

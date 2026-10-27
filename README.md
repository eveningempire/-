# 重复使用运载器健康管理平台

本项目采用 Django + Vue 前后端架构,面向重复使用运载器故障预测与健康管理(PHM),提供状态监测、故障诊断、健康评估、寿命预测及仿真数据接入功能。

目录对应 CMG 的数据管理、健康管理、规则检测、多信号流图、寿命预测、智能感知和用户权限模块;新增 `phm/` 作为领域编排层。

算法接入顺序建议为:测点/数据字典 → 结构模型 → 故障诊断 → 健康指数(HI)→ RUL → 维修决策。

## 目录说明

- `phm_backend/`：Django 配置和路由；`phm/`、`datasets/` 等为业务应用，迁移文件随应用保留。
- `frontend/src/`、`frontend/public/`：前端源码与资源；`frontend/dist/` 是当前页面成品。
- `integrations/`、`health-main/`、`health_assessment/`、`platform_handoff_20260911_v1/`：算法、模型和 MATLAB 接入资源。
- `db.sqlite3`、`media/`、`config/`：当前数据库、上传数据和现场配置，需一并备份。
- `.venv/`：本机运行环境；根目录启动、停止和检查脚本保持原位置。
- `data_management/`、`health_management/`、`rule_detection/`、`msfg_analysis/`、`lifetime_prediction/` 等兼容模块保留原路径。
- `docs/`、`交付文档/`：接口说明、验证材料和正式交付文档。
- 离线交付包应在项目外部单独生成；仓库内不保留完整的重复交付副本。

文档预览、QA 渲染、重复前端构建和一次性检查脚本属于过程文件。相关目录已加入 `.gitignore`，正式文档保存在 `交付文档/`。

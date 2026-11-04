# 重复使用运载器健康管理平台

## 从 GitHub 下载后启动（Windows）

请下载 **main 分支**。GitHub 版已包含 Hier14 权重与 scaler、15 个部件的寿命预测模型、Simulink 模型和真实仿真样例，无需另外寻找模型文件。

1. 安装 64 位 Python 3.10、3.11 或 3.12（推荐 3.10.11），将项目完整解压。
2. 双击 `start_phm_platform.bat`。首次运行自动创建 `.venv`、联网安装依赖并初始化 SQLite；已有 `offline/python` 时自动使用离线依赖。
3. 双击 `create_superuser.bat` 创建自己的管理员账号，然后访问 <http://127.0.0.1:8000/>。
4. 双击 `import_sample_data.bat` 导入真实仿真数据，刷新数据集页面后即可选择诊断、健康评估和寿命预测输入。
5. 停止时双击 `stop_phm_platform.bat`。

前端成品已经提交，不需要 Node.js、npm、Redis 或 MySQL。GitHub 下载版不携带 Python 安装包、个人数据库、账号密码和上传记录；首次安装需要联网。

### 仿真数据与 MATLAB

仓库内 `simulation_samples.zip` 包含正常及 13 类故障各一组未经改写的完整原始/派生 CSV，共 28 个文件。完整数据集有 492 个 CSV，约 1.05 GiB，放在 [GitHub Release](https://github.com/eveningempire/-/releases/tag/phm-github-20261104)。运行 `python download_simulation_data.py` 会下载并校验完整包；重启后自动优先使用完整包，再运行 `import_sample_data.bat` 可导入其余数据。

离线数据回放、诊断、健康评估与寿命推理无需 MATLAB。**实时 Simulink 仿真需要本机 MATLAB/Simulink 许可证及匹配的 MATLAB Engine**，请在仿真页面选择当前电脑的安装目录并按提示配置；随附模型版本为 R2023a。MATLAB 2012 的 HTTP 遥测接口不等于能够运行 R2023a 模型。

### 安装验证

```powershell
# 不启动网页，检查依赖、迁移、模型校验和与实际加载
powershell -NoProfile -ExecutionPolicy Bypass -File .\start_phm_platform.ps1 -CheckOnly
# 尚未安装依赖时也可检查模型文件是否下载完整
python verify_phm_delivery.py --assets-only
# 导入样例后执行真实模型推理检查
.\.venv\Scripts\python.exe verify_github_inference.py
```

如果已有运行环境，可先执行上述检查。启动失败会列出缺失或损坏文件，不会仅把服务标为“演示可用”。详细使用区别见 [README_请先阅读.md](README_请先阅读.md)。

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

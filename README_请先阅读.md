# PHM 平台客户交付版

版本日期：2026-09-18

请先阅读根目录的 `项目使用说明.md`，按照“首次安装”和“启动与停止”章节完成部署。

## 快速开始

1. 将整个 `phm_platform` 目录解压到不含特殊权限限制的位置，例如 `D:\PHM\phm_platform`。
2. 安装 64 位 Python 3.9 或 3.10。
3. 在项目根目录按 `项目使用说明.md` 创建 `.venv` 并安装 `requirements.txt`。
4. 双击 `create_superuser.bat` 创建管理员账号。
5. 双击 `start_cmg_platform.bat`，浏览器访问 `http://127.0.0.1:8000/`。
6. 停止平台时双击 `stop_cmg_platform.bat`。

## MATLAB 接入说明

MATLAB 采用手动 HTTP 上报方式，不使用 MATLAB Engine，平台不会直接控制 MATLAB。请在平台创建实时采集会话，复制页面生成的代码并粘贴到 MATLAB 命令窗口执行。工具与示例位于 `integrations\matlab\`。

## 交付内容

- Django 后端与 Vue 前端源码；
- 已构建完成的前端页面；
- SQLite 数据库与示例/业务数据；
- 故障诊断、健康评估和寿命预测所需算法资源；
- MATLAB 实时数据上报函数及示例；
- 安装、操作、备份与故障排查说明。

为保护交付安全并控制体积，压缩包未包含 Git 历史、开发虚拟环境、`node_modules`、日志、缓存、临时构建副本、`.env` 和历史数据库原始导出。首次运行会自动创建日志目录。

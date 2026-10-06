# 离线运行时说明

交付包内的 `runtime\python310` 是 Python 3.10.11 的便携运行时,`offline\python` 保存项目所需的离线 wheel。首次执行 `setup_migration.ps1` 时,脚本会在项目目录创建 `.venv` 并从本地 wheel 安装依赖。

运行时和依赖均来自压缩包,正常部署无需网络。请完整解压并保留目录结构;如果只复制启动脚本,脚本会提示缺少运行时或离线依赖。

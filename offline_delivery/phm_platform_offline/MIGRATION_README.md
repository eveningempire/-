# PHM 离线迁移说明

当前交付包已经包含 Python 3.10.11 运行时、离线依赖、前端成品、SQLite 数据库和模型资源。目标电脑无需联网,也不需要单独下载 Python 或 Node.js。

## 首次运行

1. 完整解压 `phm_platform_offline` 目录,不要只复制脚本。
2. 在该目录打开 PowerShell。
3. 执行 `powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_migration.ps1`。
4. 执行 `.\start_phm_platform.bat`,浏览器访问 `http://127.0.0.1:8000/`。

脚本会优先使用包内 `runtime\python310\python.exe` 创建项目虚拟环境,再从 `offline\python` 安装依赖。整个过程不访问网络。

## 日常启动和停止

- 启动:`.\start_phm_platform.bat`
- 停止:`.\stop_phm_platform.bat`
- 卸载本地虚拟环境:`.\uninstall_phm_platform.bat`

文件夹名称和解压位置可以更改,脚本使用自身目录定位资源,不依赖固定盘符。

# PHM 平台客户交付版

## 快速启动

1. 将整个 `phm_platform_offline` 文件夹解压到本地磁盘任意位置。
2. 双击根目录的 `start_phm_platform.bat`。
3. 浏览器访问 `http://127.0.0.1:8000/`。
4. 停止系统时双击 `stop_phm_platform.bat`。

交付包已经包含 Python 3.10.11、离线依赖、前端成品、SQLite 数据库、Hier14、health-main、健康评估适配器和 MATLAB 接口。正常启动不需要连接互联网，不需要另外安装 Python、Node.js、Redis 或 MySQL，也不需要执行 `npm install`。

首次启动时，脚本会使用 `runtime\python310\python.exe` 在本地创建 `.venv`，再从 `offline\python` 安装依赖。请保持压缩包完整解压，不要单独复制启动脚本。

## 创建管理员

首次需要管理员账号时，在包根目录打开 PowerShell，执行：

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

如果 `.venv` 尚未创建，先双击 `start_phm_platform.bat`，等待启动完成后再执行上面的命令。

## 目录约定

- `runtime\python310`：包内 Python 3.10.11 运行时
- `offline\python`：离线 Python wheel 依赖
- `frontend\dist`：已经构建好的前端页面
- `health-main`：Hier14 预测器、配置和模型权重
- `platform_handoff_20260911_v1`：健康评估适配器和模型资产
- `integrations\matlab`：MATLAB 2012 兼容的 HTTP 上报接口
- `db.sqlite3`：SQLite 数据库

文件夹名称和解压位置可以更改；启动脚本按自身所在目录定位资源，不依赖固定盘符。不要删除上述运行目录。`delete\legacy_archive`、`delete\rule_detetion`、`gengxin`、`new`、`qcy` 和 `json_backups` 等历史/临时目录已从交付包移除。

## MATLAB 2012

平台创建采集会话后，在“实时状态监测 → MATLAB 实时采集”复制代码。MATLAB 2012 先确认：

```matlab
usejava('jvm')
```

返回 `1` 后再发送数据。接口使用 MATLAB 自带 Java HTTP 客户端，不需要联网安装工具箱。

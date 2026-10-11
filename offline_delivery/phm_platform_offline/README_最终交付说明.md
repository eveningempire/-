# PHM 平台最终离线交付版

版本:2026-09-27
适用系统:Windows 10/11 64 位

## 一键启动

1. 将整个 `phm_platform_offline` 文件夹解压到本地磁盘,例如 `D:\PHM\phm_platform_offline`。路径可以更换,建议路径只使用英文字母、数字和下划线。
2. 双击 `start_phm_platform.bat`。
3. 首次启动会自动完成以下工作:
   - 使用包内 Python 3.10.11 创建本地 `.venv`;
   - 从 `offline\python` 安装全部离线依赖;
   - 执行数据库迁移;
   - 启动 Django 服务并打开浏览器。
4. 打开 `http://127.0.0.1:8000/`。

首次初始化可能需要几分钟。整个过程不需要互联网,也不需要预先安装 Python、Node.js、Redis 或 MySQL。

## 创建管理员

首次启动初始化完成后,打开新的 PowerShell 窗口,进入包根目录执行:

```powershell
.\.venv\Scripts\python.exe manage.py createsuperuser
```

按提示输入用户名、邮箱和密码。已经存在管理员账号时不需要重复创建。

## 日常启动和停止

- 启动:双击 `start_phm_platform.bat`;
- 停止:双击 `stop_phm_platform.bat`,或在服务器窗口按 `Ctrl+C`;
- 地址:`http://127.0.0.1:8000/`;
- 默认使用 SQLite,数据库文件为 `db.sqlite3`;
- 日志位于 `logs\django.log`。

如果 8000 端口被其他程序占用,先关闭占用程序再启动。启动窗口不要关闭。

## 已包含内容

- Python 3.10.11 可移植运行时和本地 wheel 依赖;
- 已构建的 Vue 页面和静态资源;
- Django 后端、SQLite 数据库及示例数据;
- Hier14 故障诊断工程、配置和模型权重;
- 健康评估适配器和模型注册资源;
- MATLAB 2012 兼容的实时遥测发送函数;
- 仿真数据资产和离线算法资源。

## MATLAB 2012 实时接入

平台创建会话后,进入"状态监测 → MATLAB 实时采集",点击"创建并获取 MATLAB 参数"。在弹出的代码中选择包内目录:

```text
phm_platform_offline\integrations\matlab
```

MATLAB 2012 先执行:

```matlab
usejava('jvm')
```

返回 `1` 后执行网页提供的连接代码,再发送测试样本。发送函数通过 MATLAB 自带 Java HTTP 客户端工作,不使用 `webwrite`、`weboptions`、`jsonencode`、`jsondecode` 或 MATLAB Engine,也不需要联网安装工具。

同一台电脑使用:

```text
http://127.0.0.1:8000
```

如果 MATLAB 位于另一台电脑,把地址中的 `127.0.0.1` 改为平台电脑的局域网 IP,并确保 8000 端口可访问。

要求:`time` 严格递增;所有信号是有限标量数值;同一会话的字段保持一致。仿真重新从 0 秒开始时,请创建新会话。

## 算法状态灯

- Hier14:包内已配置,启动后自动查找 `health-main`;
- 健康评估适配器:包内已配置,自动查找 `platform_handoff_20260911_v1`;
- RUL Shadow:开发登记状态,暂不作为正式在线推理;
- 仿真数据:包内带有离线资产,未连接现场 MATLAB 时显示等待属于正常现象。

## 常见问题

### 看到"Python 3.10 not found"

确认压缩包完整解压,并检查:

```text
runtime\python310\python.exe
```

然后再次双击 `start_phm_platform.bat`。不要把旧电脑上的 Python 3.9 `.venv` 复制进来。

### 页面没有更新

停止平台后重新启动,并在浏览器按 `Ctrl+F5`。

### MATLAB 找不到函数

在 MATLAB 执行:

```matlab
which phm_send_telemetry
```

确认路径指向当前离线包的 `integrations\matlab\phm_send_telemetry.m`。

### 令牌无效

令牌只在创建会话时显示一次。重新创建采集会话并复制完整令牌。

### 数据不触发告警

先在"异常告警中心"选择同一会话并开启实时检测,再从 MATLAB 发送数据。

## 数据备份

停止平台后备份以下内容:

```text
db.sqlite3
media\
config\
```

请不要删除数据库或媒体目录中的现场数据。


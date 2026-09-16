# MATLAB 实时联动与故障演示操作说明

## 1. 启动平台

在项目根目录运行：

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

浏览器打开 `http://127.0.0.1:8000` 并登录。进入“状态监测”，选择“MATLAB 实时采集”。管理员点击“创建采集会话”，填写名称后保存页面弹出的采集地址和令牌。

## 2. 配置 MATLAB

不要复制网页中的 Markdown 链接符号 `[]()`，只保留纯文本 URL。把以下路径加入 MATLAB：

```matlab
addpath('E:/实验项目/航天管理项目/phm_platform/integrations/matlab');
addpath('E:/实验项目/航天管理项目/phm_platform/integrations/matlab/examples');
```

将页面生成的地址和令牌保存为变量：

```matlab
ingestUrl = 'http://127.0.0.1:8000/api/v1/phm/telemetry/sessions/<会话ID>/ingest/';
token = '<页面生成的令牌>';
```

令牌通过 `Authorization: Bearer <token>` 发送，不要把令牌写入公开脚本或提交到代码仓库。

## 3. 运行内置故障注入演示

在“实时异常告警中心”选择同一会话，打开“实时检测”，然后在 MATLAB 执行：

```matlab
responses = demo_realtime_fault_injection(ingestUrl, token, 3.0);
```

脚本在 3 秒前发送正常压力，3 秒起将压力降至告警阈值以下。命令窗口中应看到 `accepted=1 alarms=0` 变为 `accepted=1 alarms=1`。网页会出现推进剂泄漏告警、隔离对象和下降的健康指数。

## 4. 接入自己的仿真回调

在 MATLAB 或 Simulink 的桌面仿真采样回调中调用：

```matlab
response = phm_send_telemetry(ingestUrl, token, struct( ...
    'time', t, ...
    'pressure', pressure, ...
    'temperature', temperature));
```

`time` 必须严格递增；同一会话中的字段集合必须保持一致；所有值必须是有限标量数值。高频模型建议缓存 1–1000 个采样点后批量发送，不要在每个求解器内部步都发 HTTP。

## 5. 演示结束与常见问题

- 在“实时状态监测”点击“结束采集”后可以导出 CSV，但该会话不能继续写入。
- 仿真重新从 `time=0` 开始时必须新建会话。
- 出现“采集令牌无效”时，重新创建会话并复制新令牌。
- 远程 MATLAB 不使用 `127.0.0.1`，应改成平台服务器 IP，并配置 Django `ALLOWED_HOSTS` 和防火墙。

## 6. 故障事件与重演接口

实时告警会自动生成故障事件。也可以通过 `POST /api/v1/phm/fault-events/` 创建手工事件，`GET /api/v1/phm/fault-events/<事件ID>/` 按时间窗口返回表格行和曲线序列。通过 `POST /api/v1/phm/fault-events/<事件ID>/replays/` 创建重演，参数 `start`、`end`、`speed` 分别表示时间窗口和倍速；随后对 `/api/v1/phm/fault-replays/<重演ID>/` 发送 `play`、`pause`、`restart`、`seek`、`speed` 或 `tick` 控制重演进度。

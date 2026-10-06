# MATLAB 2012 实时联动与故障演示操作说明

## 1. 启动平台

在项目根目录运行:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

浏览器打开 `http://127.0.0.1:8000` 并登录。进入"状态监测",选择"MATLAB 实时采集"。管理员点击"创建采集会话",填写名称后保存页面弹出的采集地址和令牌。

## 2. 配置 MATLAB 2012

MATLAB 2012 使用本目录中的 Java HTTP 兼容层发送 JSON,不需要安装 MATLAB Engine 或联网安装额外工具包。先确认 Java 可用:

```matlab
usejava('jvm')
```

命令窗口应返回 `1`。然后把以下路径加入 MATLAB(也可直接复制网页弹窗中的目录选择代码):

```matlab
addpath('E:/你的离线包/phm_platform_offline/integrations/matlab');
addpath('E:/你的离线包/phm_platform_offline/integrations/matlab/examples');
```

将页面生成的地址和令牌保存为变量:

```matlab
ingestUrl = 'http://127.0.0.1:8000/api/v1/phm/telemetry/sessions/<会话ID>/ingest/';
token = '<页面生成的令牌>';
```

令牌通过 `Authorization: Bearer <token>` 发送,不要把令牌写入公开脚本或提交到代码仓库。

## 3. 发送单条测试数据

```matlab
testSample = struct('time', 0, 'pressure', 10.0, 'temperature', 25.0);
response = phm_send_telemetry(ingestUrl, token, testSample);
disp(response);
```

正常时 `response.ok` 为 `1`、`response.accepted` 为 `1`,网页实时采样数变为 1。服务器原始 JSON 在 `response.raw` 中。

## 4. 运行内置故障注入演示

在"实时异常告警中心"选择同一会话,打开"实时检测",然后在 MATLAB 执行:

```matlab
responses = demo_realtime_fault_injection(ingestUrl, token, 3.0);
```

脚本在 3 秒前发送正常压力,3 秒起将压力降至告警阈值以下。命令窗口中应看到 `accepted=1 alarms=0` 变为 `accepted=1 alarms=1`。网页会出现推进剂泄漏告警、隔离对象和下降的健康指数。

## 5. 接入自己的仿真回调

在 MATLAB 或 Simulink 的桌面仿真采样回调中调用:

```matlab
response = phm_send_telemetry(ingestUrl, token, struct( ...
    'time', t, ...
    'pressure', pressure, ...
    'temperature', temperature));
```

`time` 必须严格递增;同一会话中的字段集合必须保持一致;所有值必须是有限标量数值;高频模型建议缓存 1–1000 个采样点后批量发送。

## 6. 连接失败时检查

- MATLAB 和平台在同一台电脑:地址保留 `127.0.0.1`。
- MATLAB 在另一台电脑:把 `127.0.0.1` 改为平台电脑的局域网 IP,并确保 8000 端口可访问。
- `usejava('jvm')` 返回 `0`:当前 MATLAB 启动方式没有 Java,需使用带 Java 的桌面 MATLAB 重新启动。
- 提示函数未定义:确认已执行 `addpath`,并运行 `which phm_send_telemetry`。
- 提示令牌无效:令牌可能复制不完整,请在平台重新创建采集会话。
- 重新从 `time=0` 开始仿真:请新建会话,旧会话不允许时间倒退。


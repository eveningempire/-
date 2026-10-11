# MATLAB 2012 实时联动与故障演示操作说明

## 1. 启动平台

在项目根目录运行:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload
```

浏览器打开 `http://127.0.0.1:8000` 并登录。进入"状态监测",选择"MATLAB 实时采集"。管理员点击"创建采集会话",填写名称并选择实时检测算法、窗口长度和步长后，保存页面弹出的采集地址和令牌。基础规则模式按单点规则检测；Hier14、MSFG + TEAMS-RT、PCA-iForest 按窗口检测。

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

正常时 esponse.ok` 为 `1`、esponse.accepted` 为 `1`,网页实时采样数变为 1。服务器原始 JSON 在 esponse.raw` 中。

## 4. 按会话算法发送数据

在“实时异常告警中心”选择同一会话并打开“实时检测”。如果选择算法模式，必须连续发送不少于会话配置的窗口长度（默认 30）个采样点；窗口未满时只保存数据，不生成算法判定。每个窗口完成后，在“算法窗口诊断结果”查看算法、判定、置信度和窗口时间；规则告警单独显示。

Hier14、MSFG + TEAMS-RT 和 PCA-iForest 要求输入字段满足对应算法的数据契约。不要为了触发结果只发送 `pressure`；应从实际 MATLAB/Simulink 信号组成完整 struct，并保持同一会话字段集合不变。

## 5. 运行内置故障注入演示

在"实时异常告警中心"选择同一会话,打开"实时检测",然后在 MATLAB 执行:

```matlab
responses = demo_realtime_fault_injection(ingestUrl, token, 3.0);
```

脚本在 3 秒前发送正常压力,3 秒起将压力降至告警阈值以下。命令窗口中应看到 `accepted=1 alarms=0` 变为 `accepted=1 alarms=1`。网页会出现推进剂泄漏告警、隔离对象和下降的健康指数。

## 6. 接入自己的仿真回调

在 MATLAB 或 Simulink 的桌面仿真采样回调中调用:

```matlab
response = phm_send_telemetry(ingestUrl, token, struct( ...
    'time', t, ...
    'pressure', pressure, ...
    'temperature', temperature));
```

`time` 必须严格递增;同一会话中的字段集合必须保持一致;所有值必须是有限标量数值;高频模型建议按窗口缓存后批量发送（一次最多 1000 个点）。

## 7. 连接失败时检查

- MATLAB 和平台在同一台电脑:地址保留 `127.0.0.1`。
- MATLAB 在另一台电脑:把 `127.0.0.1` 改为平台电脑的局域网 IP,并确保 8000 端口可访问。
- `usejava('jvm')` 返回 `0`:当前 MATLAB 启动方式没有 Java,需使用带 Java 的桌面 MATLAB 重新启动。
- 提示函数未定义:确认已执行 `addpath`,并运行 `which phm_send_telemetry`。
- 提示令牌无效:令牌可能复制不完整,请在平台重新创建采集会话。
- 算法结果为空:确认已启用实时检测、已发送达到窗口长度的数据，并检查字段是否满足所选算法的数据要求。
- 重新从 `time=0` 开始仿真:请新建会话,旧会话不允许时间倒退。


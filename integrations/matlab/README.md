# MATLAB 实时遥测

平台监测页 → 选择数据源 → MATLAB 实时采集 → 管理员创建会话，复制上报地址和令牌。
将本目录加入 MATLAB 路径：`addpath('平台目录/integrations/matlab')`。

项目内置了一个最小可运行示例：

```matlab
addpath('平台目录/integrations/matlab');
addpath('平台目录/integrations/matlab/examples');
demo_send_telemetry( ...
    'http://127.0.0.1:8000/api/v1/phm/telemetry/sessions/<会话ID>/ingest/', ...
    '<创建会话时返回的Token>');
```

运行前先在网页创建 MATLAB 采集会话，并将 `<会话ID>` 和 Token 替换为真实值。
成功时 MATLAB 会返回 `ok: 1`、`accepted: 20`；随后在网页选择该会话即可看到 20 条数据。

在 MATLAB 在线采集循环或 Simulink 仿真采样回调中，传入**当前真实信号**：

```matlab
phm_send_telemetry(ingestUrl, token, ...
    struct('time', t, 'pressure', pressure, 'temperature', temperature));
```

`time` 为仿真秒，必须严格递增；其余字段可自定义，全部为有限标量数值。同一会话字段一致。
支持一次上报 1–1000 条 struct 数组。不要在每个高频求解步执行 HTTP，建议缓存后每 0.2–1 秒批量发送。
Simulink 模型可以在桌面仿真的 MATLAB 回调/Level-2 MATLAB S-Function 中调用此函数；它不是可生成嵌入式代码的模块。
将模型实际端口的标量值传给上述函数，不会由平台自动编造信号或自动绑定未知模型端口。
仿真结束后在平台点击“结束采集”；重启仿真（time 归零）需要新建会话。

页面每秒按游标获取新样本；超过 5 秒没有新点显示断流，不重复插入最后一点。
样本保存到数据库，可关闭页面后重新查看会话。导出按钮下载当时已收到的全部采样（不是图表的最近 1000 条），UTF-8 BOM CSV。
用户可查看及导出，管理员创建及结束采集；MATLAB 仅持有单个会话的写入令牌。
远程 MATLAB 将 localhost 换成平台服务器地址，并在 Django ALLOWED_HOSTS 和网络监听配置中配置该服务器。

接口：POST `/api/v1/phm/telemetry/sessions/<id>/ingest/`
鉴权：`Authorization: Bearer <token>`
请求：`{"samples":[{"time":0,"pressure":1.2,"temperature":300}]}`
旧的无会话上报接口不再用于监测页面。此桥接以实际 HTTP 上报为准，不依赖 MATLAB Engine。

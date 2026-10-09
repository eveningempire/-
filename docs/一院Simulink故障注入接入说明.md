# 一院 Simulink 故障注入接入

## 来源与执行入口

来源：`C:/Users/HP/Desktop/一院项目.zip`，SHA256：
`6fcfdf0f67aa358cf30ba6a3da7c4c0e2bc9fa0d6a7e40e09f71633d12c3e5a7`。

包内入口实际名为 `simulate/simulate_main.py`，是 PyQt 界面程序；同目录的
`simulate_core.py` 已抽出相同的 Simulink 参数设置与 CSV 导出逻辑。
平台直接调用后者的 `run_simulation()`，避免 GUI 和作者电脑上的固定路径。
核心及环境清单位于 `integrations/algorithm_assets/simulation/`。
`rocket_sim.slx` 与平台原有模型一致，SHA256：
`2fa9a6644a1f45fbe6a6a198037f0771ccfcc8860220984f17c442e3ad05f85a`。

核心保留甲方的 13 个 Constant、Step1、Step2 路径以及原始参数输出计算方式。
平台适配增加了可选 Engine 依赖、阶段回调、参数和采样校验；重置失败会终止运行。
这些改动不改变故障模型。程序保留甲方 `start_time <= Time <= end_time` 的标签规则，
故障恢复边界样本仍标记为 1；FaultFlag 是注入真值，不是诊断结论。

## 页面参数映射

| 页面/API 参数 | 核心参数 | 模型操作 |
| --- | --- | --- |
| 子系统 + 故障类型 | power_fault / control_fault | 对应 F1–F13 Constant 的 Value=0；另一个子系统无故障 |
| injection_time | start_time | 对应 Step1 的 Time，Before=0、After=1 |
| end_time | end_time | 对应 Step2 的 Time，Before=0、After=1 |
| flight_count | flight_count | rocket_sim/Th 的 Value=flight_count*480 |

时间满足 `0 <= injection_time < end_time <= 480`，单位为秒。
飞行次数是 0–20 的整数，对应累计使用时间；本次仿真 StopTime 固定为 480 秒。
原程序没有严重度参数，因此新任务不接受 severity，不转换旧演示故障名称。
可选无故障生成正常基线。

动力：泵气蚀、涡轮转速下降、管路堵塞、主阀门卡滞、燃气泄漏、燃烧不稳定、喷管堵塞。
控制：TVC偏角不足、RCS推力不足、栅格舵偏角不足、控制器无信号、陀螺仪恒偏差、陀螺仪卡死。

## 运行与结果

实时故障注入和离线生成页面共用真实仿真接口：

- `GET /api/v1/simulation-demo/sample/`：模型、Engine 导入状态和故障列表。
- `POST /api/v1/simulation-demo/workflows/`：保存参数，返回任务 UUID。
- `POST /api/v1/simulation-demo/workflows/<uuid>/generate/`：启动独立后台进程，返回 202。
- `GET /api/v1/simulation-demo/workflows/<uuid>/`：轮询阶段、错误和输出。

示例请求体：

```json
{"mode":"realtime","subsystem":"动力","fault_mode":"泵气蚀","injection_time":40,"end_time":100,"flight_count":0}
```

阶段依次为 queued、starting_engine、configuring、solving、exporting、registering、completed。
失败会保存错误并允许重试；排队、运行或完成的任务不会重复启动。
执行需要登录及 submit_simulation 权限。

后台通过当前平台 Python 执行 `manage.py run_simulink_task <uuid>`。
输出和日志位于 `media/simulink_runs/<uuid>/`。
`scope_data.csv`（29 个参数）与 `P_values.csv`（17 个参数）校验后同时登记到 Dataset，
可在数据管理、诊断和故障回放中选取。Time 是时间，FaultFlag 是真值，均不作为参数。
页面预览有采样限制，完整数据保留在 CSV 中。

原程序的 `eng.sim()` 在求解完成后一次性返回；当前实时页面显示后台执行状态和完成后的结果，
不接收逐点在线求解遥测，也不在浏览器合成故障数据或以故障真值伪造诊断结果。

## 环境与验证

模型保存版本为 MATLAB/Simulink R2023a；甲方依赖清单中的 Engine 版本是 9.14。
本机实际安装目录为 `D:/new`（可执行文件 `D:/new/bin/matlab.exe`），版本为 R2022b / 9.13，
已在平台 Python 3.9.13 环境安装本机配套 Engine，并实际验证 Simulink 许可证及求解。
本机安装命令如下，在项目根目录执行：

```powershell
& '.venv/Scripts/python.exe' -m pip install wheel
& '.venv/Scripts/python.exe' -m pip install --no-deps --no-build-isolation 'D:/new/extern/engines/python'
& '.venv/Scripts/python.exe' -c 'import matlab.engine; print(matlab.engine.__file__)'
```

其他机器应使用与其 MATLAB 版本兼容的 Python 及本机 Engine 安装源。
压缩包中的 `rocket_simulation.yml` 是甲方原清单；其中 Python 3.11 不适用于本机 R2022b，
本次复用平台 `.venv` 的 Python 3.9，没有按原清单另建环境。
可通过 `SIMULINK_MODEL_PATH` 指向其他位置的同名 `rocket_sim.slx`。
Engine 导入成功只代表基础运行条件已配置，实际许可证和模型依赖仍以求解结果为准。

本地 `integrations/algorithm_assets/simulation/runtime.json` 记录 R2022b / Engine 9.13，
并启用 `allow_newer_model`。核心仅在本次 Engine 会话中临时关闭 `ErrorIfLoadNewModel`，
结束后恢复原设置；没有修改或重新保存 `rocket_sim.slx`。
环境变量 `SIMULINK_ALLOW_NEWER_MODEL=0` 可禁用兼容加载。

2026-10-09 已真实完成正常基线、泵气蚀 40–100 秒、陀螺仪恒偏差 180–240 秒三组 480 秒求解，
新增原始/派生 CSV 六份，Dataset ID 541–546。全部输出通过列数、有限值、时间轴及标签区间校验。
MATLAB 对 R2023a 的模型元数据发出兼容警告；部分新旧正常姿态信号存在差异，
不能据此认定 R2022b 与甲方原运行环境数值等价。

21 项故障注入、CSV schema、诊断服务和评估测试通过，Django 检查及前端构建通过。
Playwright 使用实际后台数据验证运行环境、完成任务、CSV 下载链接、诊断窗口事件及派生输入报错后的恢复，
1440/390 像素视口无页面横向溢出。详细数据、算法评估及复现方式见
[真实仿真联调与算法验证报告](./真实仿真联调与算法验证_20261009.md)。

## 附带数据

`simulate_data_+1.zip` 与此前已导入的甲方数据相同：492 个 CSV，246 对原始/派生文件，
14 份正常基线和 478 份故障文件，共 8,881,850 行，Dataset ID 49–540。
`simulate_data_+0.zip` 有 384 个 CSV（根目录为 data_batch），逐文件大小、CRC 和 SHA256 均与已导入的对应文件一致，
全部属于已导入集合，复用现有数据集。+0 源包已保留在 integrations/simulation_assets。
`health-main.zip` 是另一份健康管理应用源码，本次不覆盖平台现有诊断模型或健康评估实现。

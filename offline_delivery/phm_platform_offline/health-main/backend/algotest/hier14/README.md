# Hier14 demo integration

Hier14 端到端故障诊断接入 health 平台 demo。

## 依赖

- conda 环境 `diag`(PyTorch + pandas)
- 同级目录 `fault_diagnosis_tcn_transformer`(Hier14 模型源码)
- `simulate/datacsv/scope_data.csv`(29 维 S 遥测 + 时间列)

可选环境变量:

- `HIER14_REPO`:模型源码仓库路径
- `HEALTH_DATACSV_DIR`:simulate 数据目录

## API

`GET /algorithm/hier14/`

可选 query:`csv=/path/to/scope_data.csv`(默认读 `simulate/datacsv/scope_data.csv`)

响应新增 `window_series`:每个滑窗的诊断结果与时间范围;`pred_label` / `class_probs` 取**最后一个窗口**(当前时刻),`aggregate_*` 为全文件平均(参考用)。

## 前端

算法配置 → 模型故障诊断算法 → **Hier14 端到端** → 开始评估

- 右侧「Hier14 滑窗诊断时序」折线图:`P(正常)` 随时间变化,红点标非 normal 窗口
- 「诊断结果」弹窗内有大图版时序
- 鼠标悬停可看每个窗口的 Top3 概率

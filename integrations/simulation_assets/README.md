# 钱泽故障诊断仿真数据集

GitHub 版附 `simulation_samples.zip`：正常与 13 类故障各一组完整原始/派生 CSV，共 28 个文件，均直接选自原压缩包、未经修改。`simulation_samples.json` 记录每个成员的 SHA-256 和完整来源包的校验和。页面显示实际文件数及“真实样例”标识。

完整 492 个 CSV 位于 [GitHub Release](https://github.com/eveningempire/-/releases/tag/phm-github-20261104)。在根目录运行 `python download_simulation_data.py` 下载，或手动放入 `simulate_data_+1.zip`；重启后自动优先使用完整包。`HEALTH_SIMULATION_ARCHIVE` 可指定现场数据包，显式配置路径错误时不会替换为样例。

双击根目录 `import_sample_data.bat` 可将当前使用的压缩包导入数据集列表，支持重复执行。下面的数量描述完整来源包。

来源:`AnyShare://钱泽_SY2424114/一院项目/仿真数据/simulate_data_+1.zip`。本机同步文件位于 `E:\实验项目\一院项目\仿真数据\simulate_data_+1.zip`。

## 接入方式

原 ZIP 以只读资产形式复制到本目录,不进行 3.45 GB 全量解压。Django 的 `simulation_dataset` 应用通过 `zipfile` 流式读取目录与指定 CSV 的前若干行,既保留源数据,也避免项目产生大量散文件。

SHA-256:`065C0D8AA82AEAE22802CAB6CE17127DCE1332602C7841723FFB7E0C84256F01`

## 数据结构

- 14 个场景目录:1 个正常 `baseline`,13 个故障/退化场景。
- 492 个 CSV,即 246 组样本。
- 每组通常由原始状态量 CSV 与同名 `_P.csv` 派生参数 CSV 构成。
- 原始字段:`Time`、位置/速度/姿态、推力、`S1`–`S17`、`FaultFlag`。
- 派生字段:`Time`、`P1`–`P17`、`FaultFlag`。
- 文件名 `fcN` 表示飞行次数/批次维度;`tN` 表示故障或退化注入时刻。

## 场景映射

| 目录 | 含义 |
| --- | --- |
| baseline | 正常基线 |
| bengqixi | 泵气蚀 |
| wolun | 涡轮退化 |
| guanlu | 管路故障 |
| zhufa | 主阀故障 |
| ranqi | 燃气系统 |
| ranshao | 燃烧故障 |
| penguan | 喷管故障 |
| tvc / rcs | TVC / RCS 故障 |
| geduo | 栅格舵故障 |
| kongzhiqi | 控制器故障 |
| tuoluoyi_piancha | 陀螺仪偏差 |
| tuoluoyi_kasi | 陀螺仪卡死 |

## API

- `GET /api/v1/simulation-dataset/catalog/`:数据集及各场景统计。
- `GET /api/v1/simulation-dataset/files/<category>/`:场景文件列表。
- `GET /api/v1/simulation-dataset/preview/?member=...&limit=30`:安全抽样预览,最多 200 行。

## 使用边界

数据是 MATLAB/Simulink 批量仿真的输出,而不是 MATLAB 模型本体。本阶段用于目录浏览、诊断数据选择和后续算法输入;不会在页面打开时启动 MATLAB,也不会一次性把 3.45 GB 数据装入内存。

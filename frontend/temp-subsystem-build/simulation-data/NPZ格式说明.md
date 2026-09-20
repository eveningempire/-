# `.npz`（你说的“npm文件”）字段说明与使用指南

本文档说明本目录下各个 `plot_*.py` 脚本通过 `--save-npz xxx.npz` 导出的 **NumPy 压缩文件**（`.npz`）里包含哪些字段、字段含义、以及后人如何在别处直接复现图形。

> 说明：`.npz` 是 `numpy.savez_compressed` 的输出格式，本质是一个“带键名的数组包”。用 `np.load()` 读取即可。

---

## 1. 导出策略（默认为何文件小）

- **默认（推荐）**：`--save-npz out.npz` 只保存“**实际用于绘图的降采样后数据**”，保证能复现图形，同时文件体积随 `--downsample` 近似线性变小。
- **可选全量**：`--save-npz out.npz --save-npz-full` 会额外保存“降采样前”的数组（用于后续更精细分析），文件会显著变大。

---

## 2. 默认必含字段（所有脚本通用）

下面字段在**默认导出**（不加 `--save-npz-full`）时都会包含，用它们就能重画 2×2 图：

- **`days_full`**：全局曲线的 X 轴数组（“时间/天”），长度为全局绘图点数（已降采样）。
- **`current`**：全局电流曲线的 Y 数组（已降采样）。
- **`voltage`**：全局电压曲线的 Y 数组（已降采样）。
- **`days_short`**：局部曲线的 X 轴数组（通常 0–300 的线性轴，已降采样）。
- **`I`**：局部电流曲线的 Y 数组（已降采样）。
- **`V`**：局部电压曲线的 Y 数组（已降采样）。

元信息字段（大多数脚本都会有）：

- **`csv`**：输入 CSV 路径（`plot_m*`、`plot_r*`）。
- **`downsample`**：降采样倍数（int）。

融合脚本（`plot_z1/z2/z3.py`）额外元信息：

- **`csv1` / `csv2`**：两份输入 CSV。
- **`alpha`**：融合系数。
- **`start`**：局部片段起点（与 MATLAB 脚本一致）。

---

## 3. 复现外观用的可选字段（建议优先读取）

为保证“后人画出来的图”和当初保存时一致，部分脚本会把显示参数也写入 `.npz`。常见字段如下（存在则用，不存在就用默认值/脚本默认值）：

- **`xlim_full`**：全局子图 X 轴范围 `[xmin, xmax]`
- **`xlim_short`**：局部子图 X 轴范围
- **`ylim_current_full` / `ylim_voltage_full`**：全局电流/电压 Y 轴范围
- **`ylim_current_short` / `ylim_voltage_short`**：局部电流/电压 Y 轴范围
- **`label_time_full` / `label_time_short` / `label_current` / `label_voltage`**：坐标轴标签
- **`legend_current` / `legend_voltage`**：图例文字

注意：有少数脚本可能分别给电流/电压设置不同的 `xlim`（例如 `plot_r3.py` 导出 `xlim_current_full`、`xlim_voltage_full`）。存在就按字段使用即可。

---

## 4. `--save-npz-full` 时额外包含的字段（统一命名）

当使用 `--save-npz-full` 时，会额外保存“降采样前”的数组（便于更精细的再处理）。这些字段命名在各脚本里已统一：

- **`days_full_full`**：降采样前的全局 X 轴
- **`current_full`**：降采样前的全局电流 Y
- **`voltage_full`**：降采样前的全局电压 Y
- **`days_short_full`**：降采样前的局部 X 轴
- **`I_full`**：降采样前的局部电流 Y
- **`V_full`**：降采样前的局部电压 Y

---

## 5. 后人如何使用：最小复现示例

### 5.1 读取并查看有哪些字段

```python
import numpy as np

d = np.load("plot_m1_ds20.npz", allow_pickle=True)
print(d.files)  # 所有键名
```

### 5.2 直接重画四宫格（通用模板）

```python
import numpy as np
import matplotlib.pyplot as plt

d = np.load("plot_m1_ds20.npz", allow_pickle=True)

days_full = d["days_full"]
current = d["current"]
voltage = d["voltage"]
days_short = d["days_short"]
I = d["I"]
V = d["V"]

# 这些字段“有就用，没有就跳过”
xlim_full = d["xlim_full"] if "xlim_full" in d.files else None
xlim_short = d["xlim_short"] if "xlim_short" in d.files else None

ylim_current_full = d["ylim_current_full"] if "ylim_current_full" in d.files else None
ylim_voltage_full = d["ylim_voltage_full"] if "ylim_voltage_full" in d.files else None
ylim_current_short = d["ylim_current_short"] if "ylim_current_short" in d.files else None
ylim_voltage_short = d["ylim_voltage_short"] if "ylim_voltage_short" in d.files else None

label_time_full = str(d["label_time_full"]) if "label_time_full" in d.files else "时间/天"
label_time_short = str(d["label_time_short"]) if "label_time_short" in d.files else "时间/秒"
label_current = str(d["label_current"]) if "label_current" in d.files else "电流/A"
label_voltage = str(d["label_voltage"]) if "label_voltage" in d.files else "电压/V"
legend_current = str(d["legend_current"]) if "legend_current" in d.files else "电流"
legend_voltage = str(d["legend_voltage"]) if "legend_voltage" in d.files else "电压"

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

ax = axes[0, 0]
ax.plot(days_full, current, lw=1.5, color="blue", label=legend_current)
if xlim_full is not None: ax.set_xlim(*xlim_full)
if ylim_current_full is not None: ax.set_ylim(*ylim_current_full)
ax.set_xlabel(label_time_full); ax.set_ylabel(label_current); ax.legend(); ax.grid(True)

ax = axes[0, 1]
ax.plot(days_short, I, lw=1.5, color="blue", label=legend_current)
if xlim_short is not None: ax.set_xlim(*xlim_short)
if ylim_current_short is not None: ax.set_ylim(*ylim_current_short)
ax.set_xlabel(label_time_short); ax.set_ylabel(label_current); ax.legend(); ax.grid(True)

ax = axes[1, 0]
ax.plot(days_full, voltage, lw=1.5, color="red", label=legend_voltage)
if xlim_full is not None: ax.set_xlim(*xlim_full)
if ylim_voltage_full is not None: ax.set_ylim(*ylim_voltage_full)
ax.set_xlabel(label_time_full); ax.set_ylabel(label_voltage); ax.legend(); ax.grid(True)

ax = axes[1, 1]
ax.plot(days_short, V, lw=1.5, color="red", label=legend_voltage)
if xlim_short is not None: ax.set_xlim(*xlim_short)
if ylim_voltage_short is not None: ax.set_ylim(*ylim_voltage_short)
ax.set_xlabel(label_time_short); ax.set_ylabel(label_voltage); ax.legend(); ax.grid(True)

fig.tight_layout()
plt.show()
```

---

## 6. 常见问题

- **Q：为什么 `.npz` 里没有原始 CSV 的全量数据？**  
  A：默认只保存“用于绘图的降采样后数据”，用于复现图形；如果需要全量，使用 `--save-npz-full`。

- **Q：为什么 `days_short` 看起来像 0–300，但标签写“秒”？**  
  A：这继承自原 MATLAB 脚本：它把局部 10000 点线性映射到 0–300 的轴，物理含义由原数据采样率决定。



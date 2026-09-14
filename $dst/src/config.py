# src/config.py
"""
故障诊断配置（对齐 simulate/batch_sim 仿真 CSV）。
"""

import os

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class Config:
    # ========== 仿真数据路径 ==========
    simulate_data_dir = os.path.join(_PROJECT_ROOT, "data", "simulate")
    processed_data_dir = os.path.join(_PROJECT_ROOT, "data", "processed", "simulate")
    raw_data_path = os.path.join(_PROJECT_ROOT, "data", "raw", "plant_data.csv")

    csv_ignore_patterns = ("_P.csv",)
    csv_ignore_subdirs = ("data_batch",)

    # ========== 表格列 ==========
    time_column = "Time"
    fault_flag_column = "FaultFlag"
    feature_columns = [
        "X", "Y", "H",
        "Vx", "Vy", "Vz",
        "FT",
        "Roll", "Pitch", "Yaw",
        "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9",
        "S10_X", "S10_Y", "S10_Z",
        "S11", "S12", "S13", "S14", "S15", "S16", "S17",
    ]

    # ========== 故障类别（14 类单标签）==========
    CLASS_NAMES = [
        "正常",
        "泵气蚀",
        "涡轮转速下降",
        "管路堵塞",
        "主阀门卡滞",
        "燃气泄漏",
        "燃烧不稳定",
        "喷管堵塞",
        "TVC偏角不足",
        "RCS推力不足",
        "栅格舵偏角不足",
        "控制器无信号",
        "陀螺仪恒偏差",
        "陀螺仪卡死",
    ]

    # English labels for plots / reports (avoid CJK font issues in matplotlib)
    CLASS_NAMES_EN = [
        "Normal",
        "Pump cavitation",
        "Turbine speed drop",
        "Line blockage",
        "Main valve stuck",
        "Gas leak",
        "Combustion instability",
        "Nozzle blockage",
        "TVC deflection loss",
        "RCS thrust loss",
        "Grid fin deflection loss",
        "Controller no signal",
        "Gyro bias",
        "Gyro stuck",
    ]

    # Physical meaning of telemetry features (for interpretation reports)
    FEATURE_PHYSICS = {
        "X": "Inertial position X (m)",
        "Y": "Inertial position Y (m)",
        "H": "Altitude H (m)",
        "Vx": "Velocity X (m/s)",
        "Vy": "Velocity Y (m/s)",
        "Vz": "Velocity Z (m/s)",
        "FT": "Total thrust FT (N)",
        "Roll": "Roll angle (deg)",
        "Pitch": "Pitch angle (deg)",
        "Yaw": "Yaw angle (deg)",
        "S1": "Propulsion/actuator state S1",
        "S2": "Propulsion/actuator state S2",
        "S3": "Propulsion/actuator state S3",
        "S4": "Propulsion/actuator state S4",
        "S5": "Propulsion/actuator state S5",
        "S6": "Propulsion/actuator state S6",
        "S7": "Propulsion/actuator state S7",
        "S8": "Propulsion/actuator state S8",
        "S9": "Propulsion/actuator state S9",
        "S10_X": "TVC / actuator command X",
        "S10_Y": "TVC / actuator command Y",
        "S10_Z": "TVC / actuator command Z",
        "S11": "Propulsion/actuator state S11",
        "S12": "Propulsion/actuator state S12",
        "S13": "Propulsion/actuator state S13",
        "S14": "Propulsion/actuator state S14",
        "S15": "Propulsion/actuator state S15",
        "S16": "Propulsion/actuator state S16",
        "S17": "Propulsion/actuator state S17",
    }

    POWER_FAULT_NAMES = CLASS_NAMES[1:8]
    CONTROL_FAULT_NAMES = CLASS_NAMES[8:14]

    SLUG_TO_CLASS_ID = {
        "baseline": 0,
        "bengqixi": 1,
        "wolun": 2,
        "guanlu": 3,
        "zhufa": 4,
        "ranqi": 5,
        "ranshao": 6,
        "penguan": 7,
        "tvc": 8,
        "rcs": 9,
        "geduo": 10,
        "kongzhiqi": 11,
        "tuoluoyi_piancha": 12,
        "tuoluoyi_kasi": 13,
    }

    FAULT_NAME_TO_CLASS_ID = {
        "无故障": 0,
        "泵气蚀": 1,
        "涡轮转速下降": 2,
        "管路堵塞": 3,
        "主阀门卡滞": 4,
        "燃气泄漏": 5,
        "燃烧不稳定": 6,
        "喷管堵塞": 7,
        "TVC偏角不足": 8,
        "RCS推力不足": 9,
        "栅格舵偏角不足": 10,
        "控制器无信号": 11,
        "陀螺仪恒偏差": 12,
        "陀螺仪卡死": 13,
    }

    CLASS_ID_TO_SLUG = {v: k for k, v in SLUG_TO_CLASS_ID.items()}

    classification_mode = "single_label"
    fault_columns = CLASS_NAMES
    num_classes = len(CLASS_NAMES)

    flight_counts = [0, 3, 6, 9]

    # ========== 预处理 ==========
    use_cwt = False
    cwt_wavelet = "morl"
    cwt_n_scales = 32

    # 原始 CSV：中位 dt≈0.031s（~32Hz），480s 约 1.9 万行；变步长求解器输出，需先降采样再滑窗。
    # 参考陈志刚等 TCN-Transformer 齿轮箱文：以固定长度样本段（常见 1024/2048 点）入网；
    # 这里用 seq_len=128（2 的幂），配合 row_interval 使物理窗长约 8–16s。
    row_interval = 4          # 间隔采样：每 4 行取 1 行 → 有效 ~8Hz，dt≈0.125s/点
    raw_dt = 0.031            # 原始 CSV 中位时间步 (s)
    sample_dt = raw_dt * row_interval  # 降采样后每点时间 (s)，用于热力图横轴
    seq_len = 128             # 滑窗长度（点数），约 128×0.125≈16s
    window_stride = 64        # 滑窗步长（点数），50% 重叠
    pred_len = 1

    POWER_FAULT_CLASS_IDS = tuple(range(1, 8))   # 动力故障 1–7
    CONTROL_FAULT_CLASS_IDS = tuple(range(8, 14))  # 飞控故障 8–13

    # 按滑窗样本随机划分（分层），非按 CSV 文件
    split_by = "sample"
    train_ratio = 0.75
    val_ratio = 0.10
    test_ratio = 0.15
    random_seed = 42

    # 故障类：仅在 FaultFlag==1 连续段内滑窗；正常类：仅在 FaultFlag==0 连续段内滑窗
    train_on_fault_segment_only = True
    train_on_normal_segment_only = True
    normal_segment_flag_value = 0

    # 飞控类（8–13）：FaultFlag==1 段起点后再跳过 T_min 才开始滑窗（故障表征成熟）
    control_fault_mature_sec = 5.0   # 秒；设为 0 则与动力类相同，从段首滑窗

    # ========== 模型 ==========
    input_dim = len(feature_columns)
    d_model = 64
    n_heads = 7              # 编码器原始头数；总头数 n_heads+1=8，需 d_model % 8 == 0
    n_heads_decoder = 8      # 解码器头数（无诊断头），需 d_model % n_heads_decoder == 0
    num_encoder_layers = 3
    num_decoder_layers = 3
    dim_feedforward = 128
    dropout = 0.1

    tcn_channels = [64, 64, 64]
    kernel_size = 3

    # ========== 训练 ==========
    feature_clip = 5.0        # StandardScaler 后裁剪，抑制极端样本导致梯度爆炸
    batch_size = 64
    learning_rate = 5e-4
    weight_decay = 1e-4
    grad_clip_norm = 0.5
    num_epochs = 300
    lr_schedule = "ReduceLROnPlateau"
    step_size = 50
    gamma = 0.5
    patience = 30
    lr_patience = 8           # ReduceLROnPlateau：val_loss 不降则减 LR

    loss_type = "cross_entropy"

    log_dir = os.path.join(_PROJECT_ROOT, "logs")
    checkpoint_dir = os.path.join(_PROJECT_ROOT, "checkpoints")
    result_dir = os.path.join(_PROJECT_ROOT, "results")
    tensorboard_log = True

    device = "cuda"
    seed = 42

    num_workers = 0

    @classmethod
    def class_name(cls, class_id: int, english: bool = False) -> str:
        names = cls.CLASS_NAMES_EN if english else cls.CLASS_NAMES
        return names[int(class_id)]

    @classmethod
    def feature_physics(cls, feature_name: str) -> str:
        return cls.FEATURE_PHYSICS.get(feature_name, feature_name)

    @classmethod
    def slug_to_class_id(cls, slug: str) -> int:
        key = slug.strip().lower()
        if key not in cls.SLUG_TO_CLASS_ID:
            raise KeyError(f"未知故障目录 slug: {slug!r}")
        return cls.SLUG_TO_CLASS_ID[key]

    @classmethod
    def to_dict(cls):
        return {
            k: v
            for k, v in cls.__dict__.items()
            if not k.startswith("__") and not callable(v)
        }

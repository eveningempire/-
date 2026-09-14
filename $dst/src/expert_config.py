"""子系统专家配置（Phase 2 推进 / Phase 3 姿控）。"""

import os

from .config import Config
from .residual_features import (
    GNC_FEATURE_PHYSICS,
    GNC_RESIDUAL_COLUMNS,
    GNC_RESIDUAL_COLUMNS_V21,
    build_gnc_residual_features_v21,
)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 推进链路透传：推力 + 推进状态量 + 速度（工况上下文）
PROPULSION_FEATURE_COLUMNS = [
    "FT",
    "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9",
    "Vx", "Vy", "Vz",
]

# 全局 class_id -> 姿控专家局部标签 0–6
GNC_GLOBAL_TO_LOCAL = {0: 0, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5, 13: 6}
GNC_LOCAL_TO_GLOBAL = {v: k for k, v in GNC_GLOBAL_TO_LOCAL.items()}


class PropulsionExpertConfig(Config):
    """
    推进专家：正常(0) + 动力故障(1–7)，共 8 类。
    标签与全局 class_id 0–7 一致，无需重映射。
    """

    expert_name = "propulsion"
    allowed_class_ids = (0, 1, 2, 3, 4, 5, 6, 7)
    active_feature_columns = list(PROPULSION_FEATURE_COLUMNS)

    CLASS_NAMES = Config.CLASS_NAMES[:8]
    CLASS_NAMES_EN = Config.CLASS_NAMES_EN[:8]
    num_classes = 8
    input_dim = len(PROPULSION_FEATURE_COLUMNS)

    processed_data_dir = os.path.join(_PROJECT_ROOT, "data", "processed", "simulate_propulsion")
    checkpoint_dir = os.path.join(_PROJECT_ROOT, "checkpoints", "propulsion")
    result_dir = os.path.join(_PROJECT_ROOT, "results", "propulsion")
    log_dir = os.path.join(_PROJECT_ROOT, "logs", "propulsion")

    # 正常类样本偏少：更小滑窗步长 + 训练时加大 loss 权重
    normal_window_stride = 32       # 默认 fault 仍为 64；正常约 2x 窗口
    use_class_weight = True
    normal_class_weight_multiplier = 1.5

    @classmethod
    def model_feature_columns(cls):
        return list(cls.active_feature_columns)


class GNCExpertConfig(Config):
    """
    姿控专家：正常(0) + 飞控故障(8–13)，共 7 类。
    训练标签映射为 0–6；推理时用 LOCAL_TO_GLOBAL 还原全局 class_id。
    """

    expert_name = "gnc"
    allowed_class_ids = (0, 8, 9, 10, 11, 12, 13)
    class_id_remap = dict(GNC_GLOBAL_TO_LOCAL)
    use_residual_features = True
    gnc_residual_version = 2.1
    feature_set = "v2.1"
    active_feature_columns = list(GNC_RESIDUAL_COLUMNS_V21)

    CLASS_NAMES = [Config.CLASS_NAMES[0]] + Config.CLASS_NAMES[8:14]
    CLASS_NAMES_EN = [Config.CLASS_NAMES_EN[0]] + Config.CLASS_NAMES_EN[8:14]
    FEATURE_PHYSICS = {**Config.FEATURE_PHYSICS, **GNC_FEATURE_PHYSICS}
    num_classes = 7
    input_dim = len(GNC_RESIDUAL_COLUMNS_V21)

    processed_data_dir = os.path.join(_PROJECT_ROOT, "data", "processed", "simulate_gnc")
    checkpoint_dir = os.path.join(_PROJECT_ROOT, "checkpoints", "gnc")
    result_dir = os.path.join(_PROJECT_ROOT, "results", "gnc")
    log_dir = os.path.join(_PROJECT_ROOT, "logs", "gnc")

    include_prefault_normal_from_fault_csv = True
    prefault_normal_slugs = ("tvc", "rcs", "geduo")
    prefault_normal_max_windows_per_file = 30
    baseline_normal_window_stride = 64
    prefault_normal_window_stride = 128
    use_class_weight = True
    normal_class_weight_multiplier = 3.0
    class_weight_multipliers = [1.0, 1.5, 1.3, 1.4, 1.3, 1.0, 1.0]
    use_weighted_sampler = False

    # 飞控故障窗：仅保留与执行器阶段匹配的样本（如 TVC 不在 RCS 段）
    filter_fault_windows_by_actuator_phase = True
    actuator_phase_filter_mode = "center"  # center | all
    actuator_phase_for_filter = "time"     # 仿真用时间 band；实测可改 telemetry

    @classmethod
    def model_feature_columns(cls):
        return list(cls.active_feature_columns)

    @classmethod
    def global_class_id(cls, local_id: int) -> int:
        return int(GNC_LOCAL_TO_GLOBAL[int(local_id)])

    @classmethod
    def residual_feature_builder(cls, df, sample_dt: float = 0.125):
        return build_gnc_residual_features_v21(df, sample_dt=sample_dt)


HIER14_FEATURE_COLUMNS = list(Config.feature_columns) + list(GNC_RESIDUAL_COLUMNS_V21)


class Hier14Config(Config):
    """
    单模型层次化 14 类：29d 原始遥测 + 27d GNC v2.1 残差 → 56d；
    coarse (normal/prop/control) + prop fine (1–7) + gnc fine (8–13)。
    """

    expert_name = "hier14"
    append_gnc_residual_features = True
    use_residual_features = False
    gnc_residual_version = 2.1
    feature_set = "v2.1"
    active_feature_columns = list(HIER14_FEATURE_COLUMNS)

    FEATURE_PHYSICS = {**Config.FEATURE_PHYSICS, **GNC_FEATURE_PHYSICS}
    num_classes = 14
    input_dim = len(HIER14_FEATURE_COLUMNS)

    processed_data_dir = os.path.join(_PROJECT_ROOT, "data", "processed", "simulate_hier14")
    checkpoint_dir = os.path.join(_PROJECT_ROOT, "checkpoints", "hier14")
    result_dir = os.path.join(_PROJECT_ROOT, "results", "hier14")
    log_dir = os.path.join(_PROJECT_ROOT, "logs", "hier14")

    include_prefault_normal_from_fault_csv = True
    prefault_normal_slugs = ("tvc", "rcs", "geduo")
    prefault_normal_max_windows_per_file = 30
    baseline_normal_window_stride = 64
    prefault_normal_window_stride = 128
    filter_fault_windows_by_actuator_phase = True
    actuator_phase_filter_mode = "center"
    actuator_phase_for_filter = "time"

    use_hierarchical_head = True
    coarse_num_classes = 3
    prop_fine_num_classes = 7
    gnc_fine_num_classes = 6
    hierarchical_loss_weights = (0.25, 0.35, 0.40)

    use_class_weight = True
    normal_class_weight_multiplier = 2.5
    class_weight_multipliers_gnc_fine = (1.5, 1.3, 1.4, 1.3, 1.0, 1.0)

    @classmethod
    def model_feature_columns(cls):
        return list(cls.active_feature_columns)

    @classmethod
    def residual_feature_builder(cls, df, sample_dt: float = 0.125):
        return build_gnc_residual_features_v21(df, sample_dt=sample_dt)


FAULT_HIER13_CLASS_ID_REMAP = {gid: gid - 1 for gid in range(1, 14)}


class FaultHier13Config(Hier14Config):
    """
    二级故障分类：仅 1–13，coarse 2 类（推进故障 / 姿控故障）。
    训练标签映射为局部 0–12。
    """

    expert_name = "fault_hier13"
    allowed_class_ids = tuple(range(1, 14))
    class_id_remap = dict(FAULT_HIER13_CLASS_ID_REMAP)

    CLASS_NAMES = Config.CLASS_NAMES[1:14]
    CLASS_NAMES_EN = Config.CLASS_NAMES_EN[1:14]
    num_classes = 13

    processed_data_dir = os.path.join(_PROJECT_ROOT, "data", "processed", "simulate_fault_hier13")
    checkpoint_dir = os.path.join(_PROJECT_ROOT, "checkpoints", "fault_hier13")
    result_dir = os.path.join(_PROJECT_ROOT, "results", "fault_hier13")
    log_dir = os.path.join(_PROJECT_ROOT, "logs", "fault_hier13")

    coarse_num_classes = 2
    prop_fine_num_classes = 7
    gnc_fine_num_classes = 6
    hierarchical_loss_weights = (0.25, 0.35, 0.40)

    use_class_weight = True
    normal_class_weight_multiplier = 1.0
    class_weight_multipliers_gnc_fine = (1.5, 1.3, 1.4, 1.3, 1.0, 1.0)

    include_prefault_normal_from_fault_csv = False


class TwoStageDataConfig(Hier14Config):
    """统一两级流水线数据：0–13 全类 + 一级统计特征。"""

    expert_name = "two_stage"
    allowed_class_ids = tuple(range(14))
    num_classes = 14
    save_window_context = True

    processed_data_dir = os.path.join(_PROJECT_ROOT, "data", "processed", "two_stage")
    processed_marker = "X_hier56_train.npy"


class GatedTwoStageConfig(TwoStageDataConfig):
    """A4：监督门控 + Fault-Hier13 联合训练（56d，与 Hier14 可比）。"""

    expert_name = "two_stage_a4"
    use_hierarchical_head = True
    use_gated_hier_head = True
    coarse_num_classes = 2
    prop_fine_num_classes = 7
    gnc_fine_num_classes = 6

    binary_loss_weight = 0.40
    fault_loss_weight = 0.60
    hierarchical_loss_weights = (0.25, 0.35, 0.40)

    use_class_weight = True
    normal_class_weight_multiplier = 2.0
    class_weight_multipliers_gnc_fine = (1.5, 1.3, 1.4, 1.3, 1.0, 1.0)

    checkpoint_dir = os.path.join(_PROJECT_ROOT, "checkpoints", "two_stage", "a4")
    result_dir = os.path.join(_PROJECT_ROOT, "results", "two_stage", "a4")
    log_dir = os.path.join(_PROJECT_ROOT, "logs", "two_stage", "a4")


class BinaryStage1Config(TwoStageDataConfig):
    """A3：监督二分类一级 + 独立 Fault-Hier13 二级。"""

    expert_name = "two_stage_a3"
    use_hierarchical_head = False
    num_classes = 2
    CLASS_NAMES = ["正常", "故障"]
    CLASS_NAMES_EN = ["Normal", "Fault"]

    use_class_weight = True
    normal_class_weight_multiplier = 1.5

    checkpoint_dir = os.path.join(_PROJECT_ROOT, "checkpoints", "two_stage", "a3")
    result_dir = os.path.join(_PROJECT_ROOT, "results", "two_stage", "a3")
    log_dir = os.path.join(_PROJECT_ROOT, "logs", "two_stage", "a3")


class EnsembleDataConfig(Config):
    """14 类统一滑窗（仅用于 ensemble 评估数据构建）。"""

    expert_name = "ensemble"
    allowed_class_ids = tuple(range(14))
    num_classes = 14
    use_residual_features = False
    filter_fault_windows_by_actuator_phase = True
    actuator_phase_filter_mode = "center"
    actuator_phase_for_filter = "time"
    control_fault_mature_sec = 5.0
    include_prefault_normal_from_fault_csv = True
    prefault_normal_slugs = ("tvc", "rcs", "geduo")
    prefault_normal_max_windows_per_file = 30
    baseline_normal_window_stride = 64
    prefault_normal_window_stride = 128
    train_on_normal_segment_only = True
    train_on_fault_segment_only = True

"""姿控子系统专家：复用 TCN-Transformer 骨干，7 类输出。"""

from .tcn_transformer import TCNTransformerDiagnosis

GNCExpert = TCNTransformerDiagnosis

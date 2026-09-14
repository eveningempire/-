"""推进子系统专家：复用 TCN-Transformer 骨干，8 类输出。"""

from .tcn_transformer import TCNTransformerDiagnosis

PropulsionExpert = TCNTransformerDiagnosis

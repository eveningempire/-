import math

import torch
import torch.nn as nn
from .tcn import TCN
from .transformer_encoder import TransformerEncoder
from .transformer_decoder import TransformerDecoder

class PositionalEncoding(nn.Module):
    """固定位置编码，用于注入时序信息"""
    def __init__(self, d_model, max_len=5000):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x: (batch, seq_len, d_model)
        return x + self.pe[:, :x.size(1), :]

class TCNTransformerDiagnosis(nn.Module):
    """
    完整模型：
    - TCN 提取局部特征（位置：编码器前端）
    - 位置编码
    - Transformer 编码器（带诊断注意力头）
    - Transformer 解码器
    - 输出层：Sigmoid + FCN 分类
    """
    def __init__(self, config):
        super().__init__()
        self.config = config
        # 输入特征映射到 d_model
        self.input_proj = nn.Linear(config.input_dim, config.d_model)

        # TCN 部分（输出通道数 = d_model）
        self.tcn = TCN(
            input_dim=config.d_model,
            num_channels=[config.d_model] * len(config.tcn_channels),
            kernel_size=config.kernel_size,
            dropout=config.dropout
        )

        # 位置编码
        self.pos_encoder = PositionalEncoding(config.d_model)
        self.input_norm = nn.LayerNorm(config.d_model)
        self.tcn_norm = nn.LayerNorm(config.d_model)

        # Transformer 编码器（总头数 = n_heads + 1）
        self.encoder = TransformerEncoder(
            num_layers=config.num_encoder_layers,
            d_model=config.d_model,
            n_heads_original=config.n_heads,   # 原始头数，内部会再加1
            dropout=config.dropout,
            ff_dim=config.dim_feedforward
        )

        # Transformer 解码器（独立头数，无诊断头）
        self.decoder = TransformerDecoder(
            num_layers=config.num_decoder_layers,
            d_model=config.d_model,
            n_heads=getattr(config, "n_heads_decoder", config.n_heads),
            dropout=config.dropout,
            ff_dim=config.dim_feedforward
        )

        # 输出层：先预测下一时刻的序列（原论文方式），然后通过 Sigmoid + FCN 分类
        # 预测下一时刻的输出维度 = input_dim（因为要预测所有特征）
        self.output_proj = nn.Linear(config.d_model, config.input_dim)
        self.head_norm = nn.LayerNorm(config.input_dim)

        # FCN 分类头（输入为预测出的序列特征，经过展平后）
        # 为简单起见，使用预测序列的最后一个时间步的输出进行分类
        fcn_layers = [
            nn.Linear(config.input_dim, 64),
            nn.LeakyReLU(0.2),
            nn.Dropout(config.dropout),
            nn.Linear(64, config.num_classes),
        ]
        if getattr(config, "classification_mode", "single_label") == "multi_label":
            fcn_layers.append(nn.Sigmoid())
        self.fcn = nn.Sequential(*fcn_layers)

    def forward(self, src, tgt=None, return_diagnosis_attn=False):
        """
        Args:
            src: 输入序列 (batch, seq_len, input_dim)
            tgt: 解码器输入（训练时使用，通常是右移一位的目标序列）
            return_diagnosis_attn: 是否返回诊断注意力权重
        Returns:
            logits: 故障类别概率 (batch, num_classes)
            diag_attn_time: 时间维度注意力矩阵 (batch, seq_len, seq_len) 若 return=True
        """
        batch_size, seq_len, _ = src.shape

        # 1. 输入映射到 d_model
        x = self.input_norm(self.input_proj(src))

        # 2. TCN 提取局部特征（保持序列长度不变）
        x = self.tcn_norm(self.tcn(x))

        # 3. 位置编码
        x = self.pos_encoder(x)

        # 4. Transformer 编码器（获得诊断注意力）
        if return_diagnosis_attn:
            enc_out, diag_attn_time = self.encoder(x, return_diagnosis_attn=True)
        else:
            enc_out = self.encoder(x)

        # 5. 解码器（原论文用于时序预测，这里按原文逻辑）
        if tgt is None:
            # 推理时：使用 src 的最后一个时间步作为简单起点（可根据需要更复杂）
            tgt_input = src[:, -1:, :]                     # (B, 1, input_dim)
            tgt_input = self.input_proj(tgt_input)         # (B, 1, d_model)
        else:
            tgt_input = self.input_proj(tgt)               # (B, tgt_len, d_model)

        dec_out = self.decoder(tgt_input, enc_out)        # (B, tgt_len, d_model)

        # 6. 预测下一时刻的特征（原论文用于校验，但分类直接使用 dec_out 的最后一个时间步）
        pred_features = self.output_proj(dec_out)          # (B, tgt_len, input_dim)
        last_pred = self.head_norm(pred_features[:, -1, :])

        # 7. FCN 分类
        logits = self.fcn(last_pred)                       # (B, num_classes)

        if return_diagnosis_attn:
            return logits, diag_attn_time
        else:
            return logits
import torch
import torch.nn as nn
import math

class MultiHeadAttentionWithDiagnosis(nn.Module):
    """多头自注意力，原始头数 + 1 个诊断头，额外返回诊断头的注意力权重"""
    def __init__(self, d_model, n_heads_original, dropout=0.1):
        super().__init__()
        assert d_model % (n_heads_original + 1) == 0, "d_model 必须能被总头数整除"
        self.d_model = d_model
        self.n_heads_original = n_heads_original
        self.n_heads_total = n_heads_original + 1
        self.d_k = d_model // self.n_heads_total

        self.w_qs = nn.Linear(d_model, d_model)
        self.w_ks = nn.Linear(d_model, d_model)
        self.w_vs = nn.Linear(d_model, d_model)
        self.fc = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)

        self.scale = math.sqrt(self.d_k)

    def forward(self, query, key, value, mask=None, return_diagnosis_attn=False):
        batch_size = query.size(0)

        # 线性变换并拆分为多头
        Q = self.w_qs(query).view(batch_size, -1, self.n_heads_total, self.d_k).transpose(1, 2)
        K = self.w_ks(key).view(batch_size, -1, self.n_heads_total, self.d_k).transpose(1, 2)
        V = self.w_vs(value).view(batch_size, -1, self.n_heads_total, self.d_k).transpose(1, 2)

        # 计算注意力分数
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        attn_scores = torch.clamp(attn_scores, min=-50.0, max=50.0)
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)

        attn_weights = torch.softmax(attn_scores, dim=-1)   # (B, heads, seq_len, seq_len)
        attn_weights = self.dropout(attn_weights)

        # 加权求和
        context = torch.matmul(attn_weights, V)             # (B, heads, seq_len, d_k)
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        output = self.fc(context)

        if return_diagnosis_attn:
            # 诊断注意力头是最后一个头
            diag_attn = attn_weights[:, -1, :, :]            # (B, seq_len, seq_len)
            return output, diag_attn
        else:
            return output

class EncoderLayer(nn.Module):
    """Transformer 编码器的一层：多头注意力 + 前馈网络 + 残差 + LayerNorm"""
    def __init__(self, d_model, n_heads_original, dropout=0.1, ff_dim=128):
        super().__init__()
        self.self_attn = MultiHeadAttentionWithDiagnosis(d_model, n_heads_original, dropout)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)

    def forward(self, x, mask=None, return_diagnosis_attn=False):
        # Pre-LN：先归一化再注意力/FFN，训练更稳定
        if return_diagnosis_attn:
            attn_out, diag_attn = self.self_attn(
                self.norm1(x), self.norm1(x), self.norm1(x), mask, return_diagnosis_attn=True
            )
        else:
            attn_out = self.self_attn(self.norm1(x), self.norm1(x), self.norm1(x), mask)
        x = x + self.dropout1(attn_out)

        ff_out = self.feed_forward(self.norm2(x))
        x = x + self.dropout2(ff_out)

        if return_diagnosis_attn:
            return x, diag_attn
        else:
            return x

class TransformerEncoder(nn.Module):
    """堆叠多层 EncoderLayer"""
    def __init__(self, num_layers, d_model, n_heads_original, dropout, ff_dim):
        super().__init__()
        self.layers = nn.ModuleList([
            EncoderLayer(d_model, n_heads_original, dropout, ff_dim)
            for _ in range(num_layers)
        ])
        self.final_norm = nn.LayerNorm(d_model)

    def forward(self, x, mask=None, return_diagnosis_attn=False):
        # 存储每一层的诊断注意力（一般只需要最后一层）
        diag_attns = []
        for layer in self.layers:
            if return_diagnosis_attn:
                x, diag_attn = layer(x, mask, return_diagnosis_attn=True)
                diag_attns.append(diag_attn)
            else:
                x = layer(x, mask)
        x = self.final_norm(x)
        if return_diagnosis_attn:
            return x, diag_attns[-1]   # 返回最后一层的诊断注意力
        else:
            return x
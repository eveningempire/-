# src/models/transformer_decoder.py 修复版

import torch
import torch.nn as nn
import math

class DecoderSelfAttention(nn.Module):
    """解码器中的掩码自注意力"""
    def __init__(self, d_model, n_heads, dropout=0.1):
        super().__init__()
        assert d_model % n_heads == 0, f"d_model ({d_model}) must be divisible by n_heads ({n_heads})"
        self.d_k = d_model // n_heads
        self.n_heads = n_heads
        self.d_model = d_model
        
        self.w_qs = nn.Linear(d_model, d_model)
        self.w_ks = nn.Linear(d_model, d_model)
        self.w_vs = nn.Linear(d_model, d_model)
        self.fc = nn.Linear(d_model, d_model)
        self.dropout = nn.Dropout(dropout)
        self.scale = math.sqrt(self.d_k)

    def forward(self, query, key, value, mask=None):
        batch_size = query.size(0)
        
        # 线性变换并拆分为多头
        Q = self.w_qs(query).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        K = self.w_ks(key).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)
        V = self.w_vs(value).view(batch_size, -1, self.n_heads, self.d_k).transpose(1, 2)

        # 计算注意力分数
        attn_scores = torch.matmul(Q, K.transpose(-2, -1)) / self.scale
        attn_scores = torch.clamp(attn_scores, min=-50.0, max=50.0)
        if mask is not None:
            attn_scores = attn_scores.masked_fill(mask == 0, -1e9)
        
        attn_weights = torch.softmax(attn_scores, dim=-1)
        attn_weights = self.dropout(attn_weights)

        # 加权求和
        context = torch.matmul(attn_weights, V)
        context = context.transpose(1, 2).contiguous().view(batch_size, -1, self.d_model)
        return self.fc(context)


class DecoderLayer(nn.Module):
    """解码器单层：掩码自注意力 + 编码器-解码器注意力 + 前馈"""
    def __init__(self, d_model, n_heads, dropout, ff_dim):
        super().__init__()
        self.self_attn = DecoderSelfAttention(d_model, n_heads, dropout)
        self.cross_attn = DecoderSelfAttention(d_model, n_heads, dropout)
        self.feed_forward = nn.Sequential(
            nn.Linear(d_model, ff_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(ff_dim, d_model)
        )
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        self.dropout1 = nn.Dropout(dropout)
        self.dropout2 = nn.Dropout(dropout)
        self.dropout3 = nn.Dropout(dropout)

    def forward(self, x, encoder_output, src_mask=None, tgt_mask=None):
        # Pre-LN
        attn_self = self.self_attn(self.norm1(x), self.norm1(x), self.norm1(x), tgt_mask)
        x = x + self.dropout1(attn_self)

        attn_cross = self.cross_attn(self.norm2(x), encoder_output, encoder_output, src_mask)
        x = x + self.dropout2(attn_cross)

        ff = self.feed_forward(self.norm3(x))
        x = x + self.dropout3(ff)
        return x


class TransformerDecoder(nn.Module):
    def __init__(self, num_layers, d_model, n_heads, dropout, ff_dim):
        super().__init__()
        self.layers = nn.ModuleList([
            DecoderLayer(d_model, n_heads, dropout, ff_dim)
            for _ in range(num_layers)
        ])
        self.final_norm = nn.LayerNorm(d_model)

    def forward(self, x, encoder_output, src_mask=None, tgt_mask=None):
        for layer in self.layers:
            x = layer(x, encoder_output, src_mask, tgt_mask)
        return self.final_norm(x)
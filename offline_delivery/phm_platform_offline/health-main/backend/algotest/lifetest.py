import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ========== 1. 数据读取与预处理 ==========
csv_path = "D:\pythonpro\datacsv\sys\system1.csv"   # ⚠️ 换成你的CSV路径
df = pd.read_csv(csv_path)

# 特征列和标签列
feature_cols = [col for col in df.columns if col != "flag"]
X = df[feature_cols].values
y = df["flag"].values

# 标准化(重要)
scaler = StandardScaler()
X = scaler.fit_transform(X)

# 训练集只用 flag=1 样本来训练 VAE-GAN
X_train = X[y == 1]
X_test = X

# 转 tensor
X_train_t = torch.tensor(X_train, dtype=torch.float32)
X_test_t = torch.tensor(X_test, dtype=torch.float32)

input_dim = X_train.shape[1]
latent_dim = 8

# ========== 2. 定义 VAE-GAN 模型 ==========

class Encoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 64)
        self.fc_mu = nn.Linear(64, latent_dim)
        self.fc_logvar = nn.Linear(64, latent_dim)

    def forward(self, x):
        h = F.relu(self.fc1(x))
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar

class Decoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.fc1 = nn.Linear(latent_dim, 64)
        self.fc2 = nn.Linear(64, input_dim)

    def forward(self, z):
        h = F.relu(self.fc1(z))
        return self.fc2(h)  # 不加激活,回归型输出

class Discriminator(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.fc(x)

encoder = Encoder(input_dim, latent_dim)
decoder = Decoder(input_dim, latent_dim)
discriminator = Discriminator(input_dim)

# 优化器
vae_params = list(encoder.parameters()) + list(decoder.parameters())
vae_optimizer = optim.Adam(vae_params, lr=1e-3)
disc_optimizer = optim.Adam(discriminator.parameters(), lr=1e-3)

# ========== 3. 损失函数 ==========
def vae_loss(x, recon_x, mu, logvar):
    recon_loss = F.mse_loss(recon_x, x, reduction='mean')
    kl_div = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
    return recon_loss + 0.01 * kl_div

bce = nn.BCELoss()

# ========== 4. 训练 VAE-GAN ==========
n_epochs = 200
for epoch in range(n_epochs):
    # ----------------- Train VAE (Encoder+Decoder) -----------------
    encoder.train()
    decoder.train()
    discriminator.eval()  # 固定判别器

    mu, logvar = encoder(X_train_t)
    std = torch.exp(0.5 * logvar)
    eps = torch.randn_like(std)
    z = mu + eps * std
    recon = decoder(z)

    # VAE loss
    loss_vae = vae_loss(X_train_t, recon, mu, logvar)

    # GAN generator loss:让判别器误判生成的样本
    fake_pred = discriminator(recon)
    valid_labels = torch.ones_like(fake_pred)
    loss_gan = bce(fake_pred, valid_labels)

    total_vae_gan_loss = loss_vae + 1.0 * loss_gan

    vae_optimizer.zero_grad()
    total_vae_gan_loss.backward()
    vae_optimizer.step()

    # ----------------- Train Discriminator -----------------
    encoder.eval()
    decoder.eval()
    discriminator.train()

    # 判别真实
    real_pred = discriminator(X_train_t)
    real_loss = bce(real_pred, torch.ones_like(real_pred))

    # 判别生成
    with torch.no_grad():
        mu, logvar = encoder(X_train_t)
        z = mu + torch.randn_like(mu) * torch.exp(0.5 * logvar)
        fake_samples = decoder(z)
    fake_pred = discriminator(fake_samples)
    fake_loss = bce(fake_pred, torch.zeros_like(fake_pred))

    loss_disc = (real_loss + fake_loss) / 2

    disc_optimizer.zero_grad()
    loss_disc.backward()
    disc_optimizer.step()

    if (epoch+1) % 20 == 0:
        print(f"[Epoch {epoch+1}] VAE+GAN Loss: {total_vae_gan_loss.item():.4f} | Disc Loss: {loss_disc.item():.4f}")

# ========== 5. 测试与再飞预测 ==========
encoder.eval()
decoder.eval()
discriminator.eval()

with torch.no_grad():
    mu, logvar = encoder(X_test_t)
    z = mu
    recon = decoder(z)
    # 重构误差
    recon_error = torch.mean((recon - X_test_t)**2, dim=1).numpy()
    # 判别器概率
    disc_prob = discriminator(X_test_t).squeeze().numpy()

# 设定阈值(基于训练集)
recon_train_err = []
with torch.no_grad():
    mu_t, logvar_t = encoder(X_train_t)
    z_t = mu_t
    recon_t = decoder(z_t)
    recon_train_err = torch.mean((recon_t - X_train_t)**2, dim=1).numpy()

threshold = recon_train_err.mean() + 3 * recon_train_err.std()

# 根据重构误差 + 判别器概率做再飞预测
pred_flag = (recon_error < threshold) & (disc_prob > 0.5)
pred_flag = pred_flag.astype(int)

# 结果展示
result_df = pd.DataFrame({
    "recon_error": recon_error,
    "disc_prob": disc_prob,
    "pred_flag": pred_flag,
    "true_flag": y
})
print(result_df.head())

# 简单准确率
acc = (result_df["pred_flag"] == result_df["true_flag"]).mean()
print(f"✅ 再飞预测准确率: {acc*100:.2f}%")

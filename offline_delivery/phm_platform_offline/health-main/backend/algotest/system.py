import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import pandas as pd
import numpy as np
import random
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
# ===================== 1️⃣ 数据读取 =====================
csv_path = r"D:\pythonpro\datacsv\sys\system1.csv"
df = pd.read_csv(csv_path)

power = df['power'].values
control = df['control'].values
y = df['flag'].values

scaler = StandardScaler()
power = scaler.fit_transform(power.reshape(-1,1)).flatten()
control = scaler.fit_transform(control.reshape(-1,1)).flatten()

# ===================== 2️⃣ 定义 VAE-GAN =====================
class Encoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, 32)
        self.fc_mu = nn.Linear(32, latent_dim)
        self.fc_logvar = nn.Linear(32, latent_dim)
    def forward(self, x):
        h = F.relu(self.fc1(x))
        return self.fc_mu(h), self.fc_logvar(h)

class Decoder(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super().__init__()
        self.fc1 = nn.Linear(latent_dim, 32)
        self.fc2 = nn.Linear(32, input_dim)
    def forward(self, z):
        h = F.relu(self.fc1(z))
        return self.fc2(h)

class Discriminator(nn.Module):
    def __init__(self, input_dim):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    def forward(self, x):
        return self.fc(x)

# ===================== 3️⃣ 训练 + 评估函数 =====================
def train_and_evaluate(weight_power, save_model=True):
    weight_control = 1 - weight_power
    X_weighted = (weight_power * power + weight_control * control).reshape(-1,1)
    X_train = X_weighted[y == 1]
    X_test = X_weighted

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    X_test_t = torch.tensor(X_test, dtype=torch.float32)

    input_dim = 1
    latent_dim = 2

    encoder = Encoder(input_dim, latent_dim)
    decoder = Decoder(input_dim, latent_dim)
    discriminator = Discriminator(input_dim)

    vae_params = list(encoder.parameters()) + list(decoder.parameters())
    vae_optimizer = optim.Adam(vae_params, lr=1e-3)
    disc_optimizer = optim.Adam(discriminator.parameters(), lr=1e-3)

    bce = nn.BCELoss()

    def vae_loss(x, recon_x, mu, logvar):
        recon_loss = F.mse_loss(recon_x, x, reduction='mean')
        kl_div = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())
        return recon_loss + 0.01 * kl_div

    # --- 训练 VAE-GAN ---
    for epoch in range(50):  # 小训练迭代,加快模拟退火
        # Train VAE
        encoder.train(); decoder.train(); discriminator.eval()
        mu, logvar = encoder(X_train_t)
        z = mu + torch.randn_like(mu) * torch.exp(0.5*logvar)
        recon = decoder(z)
        loss_vae = vae_loss(X_train_t, recon, mu, logvar)
        fake_pred = discriminator(recon)
        loss_gan = bce(fake_pred, torch.ones_like(fake_pred))
        total_loss = loss_vae + loss_gan
        vae_optimizer.zero_grad()
        total_loss.backward()
        vae_optimizer.step()

        # Train discriminator
        encoder.eval(); decoder.eval(); discriminator.train()
        real_pred = discriminator(X_train_t)
        real_loss = bce(real_pred, torch.ones_like(real_pred))
        with torch.no_grad():
            mu, logvar = encoder(X_train_t)
            z = mu + torch.randn_like(mu) * torch.exp(0.5*logvar)
            fake_samples = decoder(z)
        fake_pred = discriminator(fake_samples)
        fake_loss = bce(fake_pred, torch.zeros_like(fake_pred))
        disc_loss = (real_loss + fake_loss)/2
        disc_optimizer.zero_grad()
        disc_loss.backward()
        disc_optimizer.step()

    # --- 评估 ---
    encoder.eval(); decoder.eval(); discriminator.eval()
    with torch.no_grad():
        mu, logvar = encoder(X_test_t)
        z = mu
        recon = decoder(z)
        recon_error = torch.mean((recon - X_test_t)**2, dim=1).numpy()
        disc_prob = discriminator(X_test_t).squeeze().numpy()

    # 阈值(训练集)
    with torch.no_grad():
        mu_t, logvar_t = encoder(X_train_t)
        z_t = mu_t
        recon_t = decoder(z_t)
        recon_train_err = torch.mean((recon_t - X_train_t)**2, dim=1).numpy()
    threshold = recon_train_err.mean() + 3*recon_train_err.std()

    pred_flag = (recon_error < threshold) & (disc_prob > 0.5)
    pred_flag = pred_flag.astype(int)
    acc = (pred_flag == y).mean()

    SAVE_DIR = r'D:\pythonpro\health\backend\algotest' 

     # ✅ 保存模型(在最优时调用)
    if save_model:
        torch.save(encoder.state_dict(), f"{SAVE_DIR}/encoder_best.pt")
        torch.save(decoder.state_dict(), f"{SAVE_DIR}/decoder_best.pt")
        torch.save(discriminator.state_dict(), f"{SAVE_DIR}/discriminator_best.pt")
        print(f"📦 已保存最优模型到 {SAVE_DIR}/")

    return acc

# ===================== 4️⃣ 模拟退火 =====================
def simulated_annealing(max_iter=30, T0=1.0, alpha=0.95):
    # 初始权重
    w = 0.5
    best_w = w
    best_score = train_and_evaluate(w)
    T = T0
    print(f"初始权重={w:.2f}, 准确率={best_score:.4f}")

    for i in range(max_iter):
        # 生成邻域解
        new_w = np.clip(w + np.random.uniform(-0.1, 0.1), 0.0, 1.0)
        new_score = train_and_evaluate(new_w)

        # 接受判据
        if new_score > best_score:
            w = new_w
            best_w = new_w
            best_score = new_score
        else:
            # 模拟退火概率接受
            prob = np.exp((new_score - best_score) / T)
            if random.random() < prob:
                w = new_w

        T *= alpha
        print(f"迭代{i+1}: 当前w={w:.3f}, 当前准确率={new_score:.4f}, 最佳w={best_w:.3f}, 最佳准确率={best_score:.4f}, 温度={T:.4f}")

    return best_w, best_score

best_w, best_acc = simulated_annealing()
print(f"✅ 最优权重 power={best_w:.3f}, control={1-best_w:.3f}, 准确率={best_acc:.4f}")

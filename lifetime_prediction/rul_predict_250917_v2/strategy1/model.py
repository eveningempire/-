import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

class VAE(nn.Module):
    def __init__(self, input_dim, latent_dim=8):
        super(VAE, self).__init__()
        # Encoder
        self.encoder_fc1 = nn.Linear(input_dim, 32)
        self.encoder_fc2_mu = nn.Linear(32, latent_dim)
        self.encoder_fc2_log_var = nn.Linear(32, latent_dim)

        # Decoder
        self.decoder_fc1 = nn.Linear(latent_dim, 32)
        self.decoder_fc2 = nn.Linear(32, input_dim)

        self.relu = nn.ReLU()

    def encode(self, x):
        h1 = self.relu(self.encoder_fc1(x))
        return self.encoder_fc2_mu(h1), self.encoder_fc2_log_var(h1)

    def reparameterize(self, mu, log_var):
        std = torch.exp(0.5 * log_var)
        eps = torch.randn_like(std)
        return mu + eps * std

    def decode(self, z):
        h3 = self.relu(self.decoder_fc1(z))
        return self.decoder_fc2(h3) # No activation on output for reconstruction

    def forward(self, x):
        mu, log_var = self.encode(x)
        z = self.reparameterize(mu, log_var)
        return self.decode(z), mu, log_var

def vae_loss_function(recon_x, x, mu, log_var):
    # Reconstruction loss (MSE)
    BCE = nn.functional.mse_loss(recon_x, x, reduction='sum')
    # KL divergence loss
    # 0.5 * sum(1 + log(sigma^2) - mu^2 - sigma^2)
    KLD = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp())
    return BCE + KLD

def train_vae(model, train_data, epochs=50, batch_size=64, lr=1e-3, device=None):
    model.train()
    if device is None:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    loader = DataLoader(TensorDataset(train_data), batch_size=batch_size, shuffle=True)
    for epoch in range(epochs):
        total_loss = 0
        for batch in loader:
            x = batch[0].to(device)
            recon_x, mu, log_var = model(x)
            loss = vae_loss_function(recon_x, x, mu, log_var)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(train_data)
        print(f"Epoch {epoch+1}/{epochs}, Loss: {avg_loss:.6f}")
    return model

def test_vae(model, test_data, device=None):
    if device is None:
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()
    with torch.no_grad():
        recon_x, mu, log_var = model(test_data)
        recon_error_per_sample = nn.functional.mse_loss(recon_x, test_data, reduction='none').mean(dim=1)
        kld_per_sample = -0.5 * torch.sum(1 + log_var - mu.pow(2) - log_var.exp(), dim=1)
        combined_error = recon_error_per_sample + kld_per_sample
    return combined_error, recon_x, mu, log_var
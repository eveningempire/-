"""Adapters for the trained VAE-GAN and RF reflight assets from health-main."""
from functools import lru_cache
from pathlib import Path


ASSET_ROOT = Path(__file__).resolve().parent.parent / "integrations" / "algorithm_assets" / "models"


def asset_status():
    required = ["encoder_best.pt", "decoder_best.pt", "discriminator_best.pt", "rf_health_model.pkl"]
    present = {name: (ASSET_ROOT / name).is_file() for name in required}
    try:
        import torch  # noqa: F401
        runtime = True
        error = None
    except Exception as exc:
        runtime = False
        error = str(exc)
    return {"assets_present": all(present.values()), "files": present, "runtime_available": runtime, "runtime_error": error, "asset_root": str(ASSET_ROOT)}


@lru_cache(maxsize=1)
def _load():
    import joblib
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class Encoder(nn.Module):
        def __init__(self):
            super().__init__(); self.fc1 = nn.Linear(1, 32); self.fc_mu = nn.Linear(32, 2); self.fc_logvar = nn.Linear(32, 2)
        def forward(self, x):
            h = F.relu(self.fc1(x)); return self.fc_mu(h), self.fc_logvar(h)

    class Decoder(nn.Module):
        def __init__(self):
            super().__init__(); self.fc1 = nn.Linear(2, 32); self.fc2 = nn.Linear(32, 1)
        def forward(self, z): return self.fc2(F.relu(self.fc1(z)))

    class Discriminator(nn.Module):
        def __init__(self):
            super().__init__(); self.fc = nn.Sequential(nn.Linear(1, 32), nn.ReLU(), nn.Linear(32, 1), nn.Sigmoid())
        def forward(self, x): return self.fc(x)

    encoder, decoder, discriminator = Encoder(), Decoder(), Discriminator()
    encoder.load_state_dict(torch.load(ASSET_ROOT / "encoder_best.pt", map_location="cpu", weights_only=True))
    decoder.load_state_dict(torch.load(ASSET_ROOT / "decoder_best.pt", map_location="cpu", weights_only=True))
    discriminator.load_state_dict(torch.load(ASSET_ROOT / "discriminator_best.pt", map_location="cpu", weights_only=True))
    encoder.eval(); decoder.eval(); discriminator.eval()
    return torch, encoder, decoder, discriminator, joblib.load(ASSET_ROOT / "rf_health_model.pkl")


def predict(power_health, control_health, *, power_weight=0.633, reconstruction_threshold=0.01):
    import numpy as np
    import pandas as pd
    torch, encoder, decoder, discriminator, rf = _load()
    power_health, control_health = float(power_health), float(control_health)
    if not 0 <= power_health <= 1 or not 0 <= control_health <= 1:
        raise ValueError("再飞模型健康指数必须在 0 到 1 之间")
    weighted = power_weight * power_health + (1 - power_weight) * control_health
    x = torch.tensor([[weighted]], dtype=torch.float32)
    with torch.no_grad():
        mu, _ = encoder(x); recon = decoder(mu)
        reconstruction_error = torch.mean((recon - x) ** 2).item()
        gan_confidence = discriminator(x).item()
    feature_names = list(getattr(rf, "feature_names_in_", ["power", "control"]))
    # The project RF was trained from system.csv whose power/control columns
    # use percentages (0-100), while the platform API consistently uses 0-1.
    rf_inputs = [power_health * 100.0, control_health * 100.0]
    features = pd.DataFrame([rf_inputs], columns=feature_names)
    rf_prediction = int(rf.predict(features)[0])
    rf_probability = float(rf.predict_proba(features)[0][1])
    vae_gan_pass = reconstruction_error < reconstruction_threshold and gan_confidence > 0.5
    # The VAE-GAN training code standardised its scalar input but did not save
    # that scaler. Its raw reconstruction score is therefore evidence only and
    # must not be presented as a calibrated mission-success probability.
    return {"model": "VAE-GAN + RandomForest reflight model", "weighted_health": weighted, "reconstruction_error": reconstruction_error, "reconstruction_threshold": reconstruction_threshold, "gan_confidence": gan_confidence, "rf_prediction": rf_prediction, "rf_probability": rf_probability, "rf_input_scale": "percent_0_100", "vae_gan_pass": vae_gan_pass, "vae_gan_calibrated": False, "mission_success_probability": rf_probability}

import random
import numpy as np
import torch
import os

def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def save_checkpoint(model, optimizer, epoch, score, filepath, scheduler=None):
    checkpoint = {
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict() if optimizer else None,
        'scheduler_state_dict': scheduler.state_dict() if scheduler is not None else None,
        'score': score,
    }
    torch.save(checkpoint, filepath)
    print(f"Checkpoint saved to {filepath}")

def load_checkpoint(model, optimizer, filepath, scheduler=None, map_location=None):
    if map_location is None:
        map_location = next(model.parameters()).device
    checkpoint = torch.load(filepath, map_location=map_location, weights_only=False)
    state = checkpoint['model_state_dict']
    try:
        model.load_state_dict(state)
    except RuntimeError as e:
        missing, unexpected = model.load_state_dict(state, strict=False)
        if missing:
            print(f"  [warn] checkpoint 缺少新层（将随机初始化）: {len(missing)} keys")
        if unexpected:
            print(f"  [warn] checkpoint 多余键: {len(unexpected)} keys")
        if missing and len(missing) > 20:
            raise RuntimeError(
                "checkpoint 与当前模型结构差异过大，请重新训练而非 --resume 旧权重"
            ) from e
    if optimizer is not None and checkpoint.get('optimizer_state_dict'):
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
    if scheduler is not None and checkpoint.get('scheduler_state_dict'):
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
    score = float(checkpoint.get('score', 0.0))
    print(f"Checkpoint loaded from {filepath} (epoch {checkpoint['epoch']}, score {score:.4f})")
    return int(checkpoint['epoch']), score
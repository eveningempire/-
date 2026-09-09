"""
Test the simplified model
"""
import sys
import numpy as np
import torch

sys.path.insert(0, '.')
from model_simple import SimpleGCNModel

# Load data
test_data = np.load('intelligent_sensing/ganzhi/data/015_fusion_test_data.npy')
test_labels = np.load('intelligent_sensing/ganzhi/data/015_test_label.npy')
test_data_base = test_data[:, :3, :]

print(f"Test data shape: {test_data_base.shape}")

# Load model
model = SimpleGCNModel(num_nodes=3, lambda_reg=0.0001)
model.load_state_dict(torch.load('intelligent_sensing/ganzhi/models/GCN_LinearRegression_Base/best_model.pth'))
model.load_scalers('intelligent_sensing/ganzhi/scalers/scalers_base.pkl')
model.eval()

# Predict
with torch.no_grad():
    input_tensor = torch.tensor(test_data_base, dtype=torch.float32)
    predictions = model(input_tensor)
    predictions_denorm = model.denormalize_labels(predictions.numpy())
    
    print(f"\nPredictions shape: {predictions.shape}")
    print(f"Predictions range (raw): [{predictions.min():.4f}, {predictions.max():.4f}]")
    print(f"Predictions range (denorm): [{predictions_denorm.min():.4f}, {predictions_denorm.max():.4f}]")
    
    print(f"\n前10个预测值:")
    print("True:     ", test_labels[:10].flatten())
    print("Predicted:", predictions_denorm[:10].flatten())
    print("\n期望值 (from CSV): [0.704, 0.707, 0.757, 0.697, 0.707, 0.661, 0.653, 0.676, 0.673, 0.622]")

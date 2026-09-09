"""Test script for undersampling APIs"""
import sys
from pathlib import Path

# Add paths
qiancaiyang_dir = Path(r'd:\cmg-platform\cmg_v7.0\intelligent_sensing\qiancaiyang')
ganzhi_dir = Path(r'd:\cmg-platform\cmg_v7.0\intelligent_sensing\ganzhi')
sys.path.insert(0, str(qiancaiyang_dir))
sys.path.insert(0, str(ganzhi_dir))

print("="*50)
print("Testing PHM Undersampling APIs")
print("="*50)

# Test 1: Random Sampling
try:
    from table9 import get_random_sampling_res
    import json
    result = get_random_sampling_res(1)
    data = json.loads(result)
    print("\n鉁?Random Sampling API: PASSED")
    print(f"  - Has 4Hz data: {'4Hz' in data}")
    print(f"  - Has 8Hz data: {'8Hz' in data}")
except Exception as e:
    print(f"\n鉁?Random Sampling API: FAILED - {e}")

# Test 2: Undersampling Reconstruction
try:
    from table9 import get_low_sampling_res
    result = get_low_sampling_res(1)
    data = json.loads(result)
    print("\n鉁?Undersampling Reconstruction API: PASSED")
    print(f"  - Data entries: {len(data)}")
    print(f"  - Has reconstruction metrics: {'recon_metrics' in data[1]}")
except Exception as e:
    print(f"\n鉁?Undersampling Reconstruction API: FAILED - {e}")

# Test 3: Limited Sensing
try:
    from table10 import get_limited_sensing_res
    result = get_limited_sensing_res(1)
    data = json.loads(result)
    print("\n鉁?Limited Sensing API: PASSED")
    print(f"  - Limited channels: {data['limited_channel_num']}")
    print(f"  - Augmented channels: {data['augmented_channel_num']}")
except Exception as e:
    print(f"\n鉁?Limited Sensing API: FAILED - {e}")

# Test 4: Online Learning
try:
    from table11 import get_online_learning_res
    result = get_online_learning_res(1)
    data = json.loads(result)
    print("\n鉁?Online Learning API: PASSED")
    print(f"  - Has original_model: {'original_model' in data}")
    print(f"  - Has sgd_updated_model: {'sgd_updated_model' in data}")
    print(f"  - Has oselm_updated_model: {'oselm_updated_model' in data}")
except Exception as e:
    print(f"\n鉁?Online Learning API: FAILED - {e}")

print("\n" + "="*50)
print("All API tests completed!")
print("="*50)


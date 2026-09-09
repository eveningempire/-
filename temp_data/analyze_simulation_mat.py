"""
分析simulationdata目录中的MAT文件结构 (MATLAB v7.3格式)
"""
import h5py
import numpy as np
from pathlib import Path

# 分析一个MAT文件
mat_file = Path("simulationdata/磨损退化/Mosun_Deg_1_1.mat")

print(f"分析文件: {mat_file}")
print("=" * 60)

# 加载MAT文件 (v7.3格式使用HDF5)
with h5py.File(mat_file, 'r') as f:
    print("\n所有变量名:")
    
    def print_structure(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"  - {name}: shape = {obj.shape}, dtype = {obj.dtype}")
    
    f.visititems(print_structure)
    
    # 详细查看数据
    print("\n" + "=" * 60)
    print("详细数据信息:")
    print("=" * 60)
    
    for key in f.keys():
        dataset = f[key]
        if isinstance(dataset, h5py.Dataset):
            print(f"\n变量: {key}")
            print(f"  形状: {dataset.shape}")
            print(f"  数据类型: {dataset.dtype}")
            
            # 读取数据
            data = dataset[()]
            if data.size > 0:
                print(f"  数据大小: {data.size} 个元素")
                if np.issubdtype(data.dtype, np.number):
                    print(f"  范围: [{np.min(data):.6f}, {np.max(data):.6f}]")
                    print(f"  平均值: {np.mean(data):.6f}")
                    if data.size <= 10:
                        print(f"  全部值: {data.flatten()}")
                    else:
                        print(f"  前10个值: {data.flatten()[:10]}")

print("\n" + "=" * 60)
print("分析完成！")

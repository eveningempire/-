"""
将HI_curves.mat转换为前端可用的JSON格式
从MATLAB v7.3格式读取退化注入HI曲线数据并转换为JSON
"""
import h5py
import numpy as np
import json
from pathlib import Path
import sys
import io

# 设置控制台输出为UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def convert_hi_curves_mat():
    """转换HI曲线MAT数据为JSON格式"""
    base_dir = Path(__file__).parent.parent
    mat_path = base_dir / "pinggu" / "HI_curves.mat"
    output_dir = base_dir / "frontend" / "public" / "simulation-data"
    output_path = output_dir / "HI_curves.json"
    
    print("="*60)
    print("HI曲线数据转换工具 (MAT -> JSON)")
    print("="*60)
    print(f"\n读取MAT文件: {mat_path}")
    
    if not mat_path.exists():
        raise FileNotFoundError(f"MAT文件不存在: {mat_path}")
    
    # 使用h5py读取MATLAB v7.3文件
    with h5py.File(str(mat_path), 'r') as f:
        print(f"\nMAT文件中的变量:")
        for key in f.keys():
            var = f[key]
            if isinstance(var, h5py.Dataset):
                print(f"  - {key}: shape={var.shape}, dtype={var.dtype}")
            else:
                print(f"  - {key}: type={type(var)}")
        
        # 找到数据变量（通常是非井号开头的最大数组）
        data_arrays = {}
        for key in f.keys():
            if isinstance(f[key], h5py.Dataset):
                data_arrays[key] = f[key]
        
        if not data_arrays:
            raise ValueError("MAT文件中未找到有效的数据数组")
        
        # 选择最大的数组作为HI曲线数据
        main_var_name = max(data_arrays.keys(), key=lambda k: data_arrays[k].size)
        hi_curves_dataset = data_arrays[main_var_name]
        
        print(f"\n✓ 使用数据变量: '{main_var_name}'")
        print(f"✓ 数据维度: {hi_curves_dataset.shape}")
        
        # 读取数据到numpy数组
        hi_curves = hi_curves_dataset[()]
        
        # 确定数据结构：MATLAB存储时可能是列优先的
        # h5py读取后可能需要转置
        if hi_curves.ndim == 1:
            # 一维数组，只有一条曲线
            num_curves = 1
            points_per_curve = len(hi_curves)
            hi_curves = hi_curves.reshape(1, -1)
        elif hi_curves.ndim == 2:
            # MATLAB通常是列优先，h5py读取后可能需要转置
            # 假设较小的维度是曲线数量
            if hi_curves.shape[0] > hi_curves.shape[1]:
                # 行数多，每列是一条曲线，需要转置
                hi_curves = hi_curves.T
            # 现在每行是一条曲线
            num_curves = hi_curves.shape[0]
            points_per_curve = hi_curves.shape[1]
        else:
            raise ValueError(f"不支持的数据维度: {hi_curves.ndim}")
        
        print(f"✓ 曲线数量: {num_curves}")
        print(f"✓ 每条曲线数据点: {points_per_curve}")
        
        # 构建JSON数据结构
        result = {
            "metadata": {
                "source": "pinggu/HI_curves.mat",
                "variable_name": main_var_name,
                "total_curves": int(num_curves),
                "points_per_curve": int(points_per_curve),
                "description": "退化注入HI曲线数据"
            },
            "curves": []
        }
        
        # 转换每一行为一条曲线
        print(f"\n正在转换 {num_curves} 条曲线...")
        for idx in range(num_curves):
            curve_values = hi_curves[idx, :]
            
            # 将numpy数组转换为Python list，处理NaN值
            values_list = []
            for v in curve_values:
                if np.isnan(v) or np.isinf(v):
                    values_list.append(None)
                else:
                    values_list.append(float(v))
            
            curve_data = {
                "id": int(idx),
                "name": f"HI曲线 {idx + 1}",
                "values": values_list
            }
            result["curves"].append(curve_data)
            
            # 显示进度
            if (idx + 1) % max(1, num_curves // 10) == 0 or idx == num_curves - 1:
                print(f"  进度: {idx + 1}/{num_curves} 条曲线")
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 写入JSON文件
    print(f"\n保存JSON文件: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 获取文件大小
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    
    print("\n" + "="*60)
    print("✓ 转换完成！")
    print("="*60)
    print(f"输出文件: {output_path}")
    print(f"文件大小: {file_size_mb:.2f} MB")
    print(f"曲线数量: {len(result['curves'])}")
    print(f"每条曲线数据点: {len(result['curves'][0]['values']) if result['curves'] else 0}")
    print(f"\n数据统计:")
    
    # 统计信息
    if result['curves']:
        all_values = []
        for curve in result['curves']:
            all_values.extend([v for v in curve['values'] if v is not None])
        
        if all_values:
            print(f"  - 数值范围: [{min(all_values):.6f}, {max(all_values):.6f}]")
            print(f"  - 平均值: {np.mean(all_values):.6f}")
            print(f"  - 标准差: {np.std(all_values):.6f}")
    
    print("="*60)

if __name__ == "__main__":
    try:
        convert_hi_curves_mat()
    except Exception as e:
        print(f"\n转换失败: {str(e)}")
        import traceback
        traceback.print_exc()


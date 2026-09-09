"""
将HI_curves.csv转换为前端可用的JSON格式
支持降采样以优化前端加载性能
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

def convert_hi_curves():
    """转换HI曲线数据为JSON格式"""
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / "pinggu" / "HI_curves.csv"
    output_dir = base_dir / "frontend" / "public" / "simulation-data"
    output_path = output_dir / "HI_curves.json"
    
    print("="*60)
    print("HI曲线数据转换工具")
    print("="*60)
    print(f"\n读取CSV文件: {csv_path}")
    
    # 读取CSV文件
    df = pd.read_csv(csv_path)
    
    print(f"✓ 原始数据维度: {df.shape[0]} 行 × {df.shape[1]} 列")
    
    # 处理重复列名（添加后缀）
    cols = pd.Series(df.columns)
    duplicated_cols = cols[cols.duplicated()].unique()
    
    if len(duplicated_cols) > 0:
        print(f"⚠ 检测到 {len(duplicated_cols)} 个重复列名，正在处理...")
        for dup in duplicated_cols:
            indices = [i for i, x in enumerate(cols) if x == dup]
            for i, idx in enumerate(indices):
                if i > 0:  # 保留第一个，其他加后缀
                    cols.iloc[idx] = f"{dup}_{i}"
        df.columns = cols
        print("✓ 列名处理完成")
    
    # 构建JSON数据结构
    result = {
        "metadata": {
            "source": "pinggu/HI_curves.csv",
            "total_curves": len(df),
            "points_per_curve": len(df.columns),
            "description": "退化注入HI曲线数据"
        },
        "curves": []
    }
    
    # 转换每一行为一条曲线
    print(f"\n正在转换 {len(df)} 条曲线...")
    for idx, row in df.iterrows():
        curve_data = {
            "id": int(idx),
            "name": f"HI曲线 {idx + 1}",
            "values": [float(v) if pd.notna(v) else None for v in row.values]
        }
        result["curves"].append(curve_data)
        
        # 显示进度
        if (idx + 1) % 20 == 0 or idx == len(df) - 1:
            print(f"  进度: {idx + 1}/{len(df)} 条曲线")
    
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
            print(f"  - 数值范围: [{min(all_values):.4f}, {max(all_values):.4f}]")
            print(f"  - 平均值: {np.mean(all_values):.4f}")
            print(f"  - 标准差: {np.std(all_values):.4f}")
    
    print("="*60)

if __name__ == "__main__":
    try:
        convert_hi_curves()
    except Exception as e:
        print(f"\n❌ 转换失败: {str(e)}")
        import traceback
        traceback.print_exc()

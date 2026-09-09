"""
将tuihua目录下的NPZ文件转换为JSON格式，供前端使用
"""
import numpy as np
import json
from pathlib import Path

# 定义数据文件路径
BASE_DIR = Path(__file__).parent.parent
TUIHUA_DIR = BASE_DIR / "tuihua"
OUTPUT_DIR = BASE_DIR / "frontend" / "public" / "simulation-data"

# 确保输出目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 数据集列表
DATASETS = ['m1', 'm2', 'm3', 'r1', 'r2', 'r3', 'z1', 'z2', 'z3']

def convert_npz_to_json(npz_path, json_path):
    """
    将单个NPZ文件转换为JSON
    
    Args:
        npz_path: NPZ文件路径
        json_path: 输出JSON文件路径
    """
    try:
        # 加载NPZ文件
        data = np.load(npz_path, allow_pickle=True)
        
        # 构建JSON数据结构
        json_data = {}
        
        # 提取所有数组数据
        for key in data.files:
            value = data[key]
            
            # 处理不同类型的数据
            if isinstance(value, np.ndarray):
                if value.dtype.kind in ['i', 'u', 'f']:  # 数值类型
                    json_data[key] = value.tolist()
                elif value.dtype.kind in ['U', 'S', 'O']:  # 字符串类型
                    json_data[key] = str(value)
                else:
                    json_data[key] = str(value)
            else:
                json_data[key] = str(value)
        
        # 写入JSON文件
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"[OK] Converted: {npz_path.name} -> {json_path.name}")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed: {npz_path.name} - {str(e)}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("NPZ to JSON 转换工具")
    print("=" * 60)
    print()
    
    success_count = 0
    total_count = len(DATASETS)
    
    for dataset in DATASETS:
        npz_file = TUIHUA_DIR / f"plot_{dataset}_ds20.npz"
        json_file = OUTPUT_DIR / f"plot_{dataset}_ds20.json"
        
        if not npz_file.exists():
            print(f"[ERROR] File not found: {npz_file}")
            continue
        
        if convert_npz_to_json(npz_file, json_file):
            success_count += 1
    
    print()
    print("=" * 60)
    print(f"转换完成: {success_count}/{total_count} 个文件成功")
    print(f"输出目录: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()

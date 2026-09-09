"""
鍏ㄩ潰鍒嗘瀽simulationdata鐩綍涓殑鎵€鏈塎AT鏂囦欢
"""
import h5py
import numpy as np
from pathlib import Path
import json
import sys

# 璁剧疆杈撳嚭缂栫爜
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 鎵弿鎵€鏈塎AT鏂囦欢
base_dir = Path("simulationdata")
mat_files = list(base_dir.glob("**/*.mat"))

print("=" * 80)
print("PHM浠跨湡鏁版嵁鏂囦欢鍒嗘瀽鎶ュ憡")
print("=" * 80)

print(f"\n鍏辨壘鍒?{len(mat_files)} 涓狹AT鏂囦欢\n")

# 鍒嗙被缁熻
mosun_files = [f for f in mat_files if "Mosun" in f.name or "mosun" in f.name.lower()]
runhua_files = [f for f in mat_files if "RunHua" in f.name or "runhua" in f.name.lower()]

print(f"纾ㄦ崯閫€鍖栨枃浠? {len(mosun_files)} 涓?)
print(f"娑︽粦閫€鍖栨枃浠? {len(runhua_files)} 涓?)

# 鏂囦欢鍛藉悕瑙勫垯鍒嗘瀽
print("\n" + "-" * 80)
print("鏂囦欢鍛藉悕瑙勫垯:")
print("-" * 80)
for f in sorted(mat_files):
    print(f"  {f}")

# 璇︾粏鍒嗘瀽浠ｈ〃鎬ф枃浠?
print("\n" + "=" * 80)
print("浠ｈ〃鎬ф枃浠舵暟鎹粨鏋勫垎鏋?)
print("=" * 80)

sample_files = [
    ("纾ㄦ崯閫€鍖?鏅€氬伐鍐?, "simulationdata/纾ㄦ崯閫€鍖?Mosun_Deg_1_1.mat"),
    ("纾ㄦ崯閫€鍖?姝ｅ鸡宸ュ喌", "simulationdata/纾ㄦ崯閫€鍖?Mosun_Deg_2_1.mat"),
    ("纾ㄦ崯閫€鍖?鐭╁舰宸ュ喌", "simulationdata/纾ㄦ崯閫€鍖?Mosun_Deg_3_1.mat"),
    ("娑︽粦閫€鍖?鏅€氬伐鍐?, "simulationdata/娑︽粦閫€鍖?RunHua_Deg_1_1.mat"),
]

data_summary = {}

for label, filepath in sample_files:
    print(f"\n{label}: {Path(filepath).name}")
    print("-" * 80)
    
    try:
        with h5py.File(filepath, 'r') as f:
            # 鏌ユ壘涓昏鏁版嵁鍙橀噺
            main_vars = []
            
            # 妫€鏌ユ槸鍚︽湁鏃堕棿搴忓垪鏁版嵁
            if 'Friction' in f:
                friction_data = f['Friction']
                print(f"  [OK] 鎵惧埌 'Friction' 鍙橀噺: shape={friction_data.shape}")
                main_vars.append('Friction')
            
            # 鎵弿 #refs# 涓殑澶ф暟鎹暟缁?
            if '#refs#' in f:
                refs = f['#refs#']
                large_arrays = []
                for key in refs.keys():
                    dataset = refs[key]
                    if isinstance(dataset, h5py.Dataset):
                        # 鏌ユ壘澶у瀷鏁版嵁鏁扮粍锛堝彲鑳芥槸鏃堕棿搴忓垪鏁版嵁锛?
                        if dataset.size > 1000 and np.issubdtype(dataset.dtype, np.number):
                            large_arrays.append((key, dataset.shape, dataset.size))
                
                # 鏄剧ず鏈€澶х殑鍑犱釜鏁扮粍
                large_arrays.sort(key=lambda x: x[2], reverse=True)
                for key, shape, size in large_arrays[:3]:
                    dataset = refs[key]
                    data = dataset[()]
                    print(f"  [DATA] #refs#/{key}: shape={shape}, size={size:,}")
                    if size > 100000:
                        print(f"         -> 鏁版嵁鑼冨洿: [{np.min(data):.6f}, {np.max(data):.6f}]")
                        main_vars.append(f"#refs#/{key}")
            
            data_summary[label] = {
                'file': Path(filepath).name,
                'main_vars': main_vars,
                'keys': list(f.keys())
            }
            
    except Exception as e:
        print(f"  [ERROR] 璇诲彇澶辫触: {e}")

# 涓庣幇鏈夋暟鎹姣?
print("\n" + "=" * 80)
print("涓庣幇鏈塉SON鏁版嵁瀵规瘮")
print("=" * 80)

print("\n褰撳墠椤甸潰浣跨敤鐨凧SON鏂囦欢鏍煎紡:")
print("""
{
  "csv": "鍘熷CSV鏂囦欢鍚?,
  "downsample": 20,
  "days_full": [...],    // 鍏ㄥ眬鏃堕棿杞?
  "current": [...],       // 鍏ㄥ眬鐢垫祦
  "days_short": [...],    // 灞€閮ㄦ椂闂磋酱
  "I": [...],            // 灞€閮ㄧ數娴?
  "voltage": [...],       // 鍏ㄥ眬鐢靛帇
  "V": [...]             // 灞€閮ㄧ數鍘?
}
""")

print("\nMAT鏂囦欢涓寘鍚殑鏁版嵁:")
print("  - Friction 鍙橀噺")
print("  - #refs#/p 鍜?#refs#/y (110,000涓暟鎹偣鐨勫ぇ鍨嬫暟缁?")
print("  - 鏃堕棿搴忓垪鐩稿叧鐨勫厓鏁版嵁缁撴瀯")

# 寤鸿
print("\n" + "=" * 80)
print("鍒嗘瀽缁撹涓庡缓璁?)
print("=" * 80)

print("""
1. 鏂囦欢缁勭粐缁撴瀯:
   [OK] 纾ㄦ崯閫€鍖? 9涓枃浠?(Mosun_Deg_X_Y.mat)
   [OK] 娑︽粦閫€鍖? 9涓枃浠?(RunHua_Deg_X_Y.mat)
   - X = 1,2,3 (瀵瑰簲宸ュ喌: 鏅€?姝ｅ鸡/鐭╁舰)
   - Y = 1,2,3 (鍙兘鏄噸澶嶅疄楠?

2. 鏁版嵁鏍煎紡:
   [OK] MATLAB v7.3 (HDF5鏍煎紡)
   [OK] 鍖呭惈澶у瀷鏃堕棿搴忓垪鏁版嵁 (110,000涓暟鎹偣)
   [WARN] 鐩墠缂哄皯"缁煎悎閫€鍖?(z)鏁版嵁

3. 涓庣幇鏈夋暟鎹姣?
   - 鐜版湁鏁版嵁: plot_m1, plot_m2, plot_m3, plot_r1, plot_r2, plot_r3, plot_z1, plot_z2, plot_z3
   - 鏂版暟鎹? Mosun_Deg_X_Y, RunHua_Deg_X_Y
   [WARN] 缂哄皯缁煎悎閫€鍖?z)鐨凪AT鏂囦欢

4. 鎺ㄨ崘鎿嶄綔:
   a) 缂栧啓杞崲鑴氭湰锛屽皢MAT鏂囦欢杞崲涓篔SON鏍煎紡
   b) 鎻愬彇鏃堕棿銆佺數娴併€佺數鍘嬬瓑鍙傛暟
   c) 搴旂敤闄嶉噰鏍?downsample=20)浠ヤ紭鍖栨€ц兘
   d) 鏇挎崲鎴栬ˉ鍏呯幇鏈夌殑JSON鏁版嵁鏂囦欢
   e) 濡傛灉鏈夌患鍚堥€€鍖栫殑鍘熷鏁版嵁锛岃ˉ鍏呰繘鏉?

5. 娼滃湪浠峰€?
   [+] 鍙兘鍖呭惈鏇村畬鏁存垨鏇存柊鐨勪豢鐪熸暟鎹?
   [+] 鍙敤浜庨獙璇佹垨鏇挎崲鐜版湁鐨勯€€鍖栨ā鍨嬫暟鎹?
   [+] 3缁勯噸澶嶅疄楠屾暟鎹彲鐢ㄤ簬缁熻鍒嗘瀽
   [+] 姣忎釜鏂囦欢绾?MB锛屾暟鎹噺閫備腑
""")

print("\n" + "=" * 80)
print("鍒嗘瀽瀹屾垚!")
print("=" * 80)


"""
PHM5鍙傛暟鍚嶇О鏄犲皠琛?
鍘熷CSV鍙傛暟鍚嶏紙鑻辨枃锛夊埌涓枃鏄剧ず鍚嶇О鐨勬槧灏?
"""

# 鍙傛暟鍚嶇О鏄犲皠瀛楀吀
PARAM_NAME_MAP = {
    'HighOmega': '楂橀€熺粍浠惰浆閫?,       # 楂橀€熻浆瀛愯閫熷害
    'LowOmega': '浣庨€熺粍浠惰浆閫?,        # 浣庨€熻浆瀛愯閫熷害
    'LowTheta': '浣庨€熺粍浠惰搴?,        # 浣庨€熺粍浠惰浆瑙?
    'HighV': '楂橀€熺數鏈虹數鍘?,           # 楂橀€熺數鏈虹數鍘?
    'HighI': '楂橀€熺數鏈虹數娴?,           # 楂橀€熺數鏈虹數娴?
    'HighTM': '楂橀€熺數鏈烘俯搴?,          # 楂橀€熺數鏈烘俯搴︼紙涓绘俯搴︿紶鎰熷櫒锛?
    'HighTS': '楂橀€熺數鏈哄壇娓╁害',        # 楂橀€熺數鏈哄壇娓╁害浼犳劅鍣?
    'HighTMC': '楂橀€熺數鏈烘俯搴﹁ˉ鍋?,     # 楂橀€熺數鏈轰富娓╁害琛ュ伩鍊?
    'HighTSC': '楂橀€熺數鏈哄壇娓╁害琛ュ伩',   # 楂橀€熺數鏈哄壇娓╁害琛ュ伩鍊?
    'LowTK': '浣庨€熺粍浠舵俯搴?            # 浣庨€熺粍浠舵俯搴?
}

# 鍙傛暟鍗曚綅鏄犲皠
PARAM_UNIT_MAP = {
    'HighOmega': 'rpm',
    'LowOmega': 'rpm', 
    'LowTheta': '搴?,
    'HighV': 'V',
    'HighI': 'A',
    'HighTM': '掳C',
    'HighTS': '掳C',
    'HighTMC': '掳C',
    'HighTSC': '掳C',
    'LowTK': '掳C'
}

# 鍏抽敭鍙傛暟锛堢敤浜庝富瑕佸睍绀猴級
KEY_PARAMS = ['HighI', 'HighTM', 'HighOmega', 'LowOmega']

if __name__ == "__main__":
    print("PHM5鍙傛暟鏄犲皠琛?")
    print("-" * 60)
    for eng, chn in PARAM_NAME_MAP.items():
        unit = PARAM_UNIT_MAP.get(eng, '')
        print(f"{eng:15} -> {chn:20} ({unit})")
    print("-" * 60)
    print(f"\n鍏抽敭鍙傛暟锛堜富瑕佸睍绀猴級: {', '.join([PARAM_NAME_MAP[p] for p in KEY_PARAMS])}")


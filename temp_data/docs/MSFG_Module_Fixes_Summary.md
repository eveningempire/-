# MSFG澶氫俊鍙锋祦鍥炬ā鍧椾慨澶嶆€荤粨

## 馃幆 淇姒傝堪

缁忚繃鍏ㄩ潰鍒嗘瀽鍜屼慨澶嶏紝MSFG澶氫俊鍙锋祦鍥炬ā鍧楃幇鍦ㄨ兘澶熸纭湴浠庢祴鐐归厤缃€佽瘎鍒嗘帹瀵煎埌绯荤粺鍋ュ悍鎬诲垎鐨勫畬鏁存祦绋嬨€?

## 馃敡 涓昏淇鍐呭

### 1. 鍒涘缓娴嬬偣璇勫垎鏈嶅姟 鉁?

**鏂囦欢**: `msfg_analysis/services/testpoint_scoring.py`

**淇鍐呭**:
- 鍒涘缓浜?`TestPointScoringService` 绫?
- 姝ｇ‘浣跨敤 `TestPointRule` 妯″瀷涓厤缃殑瑙勫垯琛ㄨ揪寮?
- 瀹炵幇浜嗗畨鍏ㄧ殑琛ㄨ揪寮忔墽琛岀幆澧?
- 鏀寔鏅鸿兘鐨勬祴鐐?鏁版嵁鍙傛暟鍖归厤
- 鎻愪緵浜嗗鐢ㄨ瘎鍒嗘満鍒?

**鏍稿績鍔熻兘**:
```python
def calculate_test_scores(self, data_point: PHMData, msfg_definition: MSFGDefinition) -> Dict[str, float]:
    """鍩轰簬娴嬬偣瑙勫垯璁＄畻娴嬬偣鍒嗘暟"""
    # 1. 鑾峰彇璇SFG鐨勬墍鏈夋椿璺冩祴鐐硅鍒?
    # 2. 鎵ц瑙勫垯琛ㄨ揪寮?
    # 3. 搴旂敤鏉冮噸
    # 4. 杩斿洖鏍囧噯鍖栧垎鏁?0-1)
```

### 2. 鍒涘缓閮ㄤ欢鏄犲皠鏈嶅姟 鉁?

**鏂囦欢**: `msfg_analysis/services/component_mapping.py`

**淇鍐呭**:
- 鍒涘缓浜?`ComponentMappingService` 绫?
- 姝ｇ‘浣跨敤 `TestPointComponentMapping` 妯″瀷
- 閫氳繃MSFG鍥剧粨鏋勫缓绔嬫祴鐐?鏁呴殰-閮ㄤ欢鐨勪紶閫掑叧绯?
- 瀹炵幇浜嗘櫤鑳界殑鏁呴殰鍒嗛厤绠楁硶
- 鎻愪緵浜嗗鐢ㄦ槧灏勬満鍒?

**鏍稿績鍔熻兘**:
```python
def build_component_mappings(self, msfg_definition: MSFGDefinition) -> Dict[str, List[str]]:
    """鏋勫缓姝ｇ‘鐨勯儴浠舵槧灏勫叧绯?""
    # 杩斿洖 component_name -> [fault_names] 鐨勬槧灏?
```

### 3. 淇鎵归噺澶勭悊閫昏緫 鉁?

**鏂囦欢**: `data_management/batch_processing.py`

**淇鍐呭**:
- 閲嶅啓浜?`_run_msfg_detection` 鏂规硶
- 闆嗘垚浜嗘柊鐨勬祴鐐硅瘎鍒嗘湇鍔?
- 闆嗘垚浜嗘柊鐨勯儴浠舵槧灏勬湇鍔?
- 淇浜嗘娴嬪埌鐨勬晠闅滃拰鍏抽敭閮ㄤ欢鐨勬彁鍙栭€昏緫
- 娣诲姞浜嗚缁嗙殑閿欒鏃ュ織

**涓昏鏀硅繘**:
```python
# 馃敡 淇1锛氫娇鐢ㄦ纭殑娴嬬偣璇勫垎鏈嶅姟
test_scores_dict = calculate_msfg_test_scores(record, msfg)

# 馃敡 淇2锛氫娇鐢ㄦ纭殑閮ㄤ欢鏄犲皠鏈嶅姟  
component_mappings = build_msfg_component_mappings(msfg)

# 馃敡 淇3锛氭纭彁鍙栨娴嬪埌鐨勬晠闅滃拰鍏抽敭閮ㄤ欢
detected_faults = [fault for fault, data in fault_results.items() 
                  if data.get('fault_probability', 0.0) > 0.7]
```

### 4. 淇鏁版嵁搴撴ā鍨?鉁?

**鏂囦欢**: `msfg_analysis/models.py`

**淇鍐呭**:
- 淇浜?`TestPointComponentMapping` 鐨勫敮涓€绾︽潫
- 浠?`["msfg_definition", "test_point_name"]` 鏀逛负 `["msfg_definition", "test_point_name", "component_name"]`
- 鐜板湪鏀寔涓€涓祴鐐规槧灏勫埌澶氫釜閮ㄤ欢锛堜竴瀵瑰鏄犲皠锛?

### 5. 鍒涘缓绔埌绔祴璇?鉁?

**鏂囦欢**: `msfg_analysis/management/commands/test_msfg_detection.py`

**鍔熻兘**:
- 鍒涘缓娴嬭瘯鏁版嵁
- 娴嬭瘯璇勫垎閫昏緫
- 娴嬭瘯閮ㄤ欢鏄犲皠
- 娴嬭瘯铻嶅悎绠楁硶
- 娴嬭瘯瀹屾暣娴佺▼锛堝寘鎷暟鎹簱瀛樺偍锛?

**浣跨敤鏂规硶**:
```bash
# 鍒涘缓娴嬭瘯鏁版嵁
python manage.py test_msfg_detection --create-test-data

# 娴嬭瘯瀹屾暣娴佺▼
python manage.py test_msfg_detection --test-full-pipeline
```

## 馃搳 淇鍓嶅悗瀵规瘮

### 淇鍓嶇殑闂 鉂?

1. **娴嬬偣璇勫垎閿欒**: 绠€鍗曟寜绱㈠紩鏄犲皠锛屾病鏈変娇鐢ㄩ厤缃殑瑙勫垯
2. **閮ㄤ欢鏄犲皠閿欒**: 蹇界暐浜嗗疄闄呯殑鏄犲皠鍏崇郴锛屾墍鏈夋晠闅滈兘鍒嗛厤缁欐墍鏈夐儴浠?
3. **鏁版嵁搴撶害鏉熼敊璇?*: 涓嶆敮鎸佷竴瀵瑰鏄犲皠
4. **缁撴灉鎻愬彇閿欒**: 浠庨敊璇殑瀛楁鎻愬彇鏁呴殰鍜岄儴浠朵俊鎭?
5. **缂轰箯楠岃瘉鏈哄埗**: 娌℃湁绔埌绔祴璇曢獙璇佸姛鑳?

### 淇鍚庣殑鏀硅繘 鉁?

1. **姝ｇ‘鐨勬祴鐐硅瘎鍒?*: 鍩轰簬 `TestPointRule` 鎵ц瑙勫垯琛ㄨ揪寮?
2. **鍑嗙‘鐨勯儴浠舵槧灏?*: 鍩轰簬 `TestPointComponentMapping` 鍜孧SFG鍥剧粨鏋?
3. **鐏垫椿鐨勬暟鎹簱妯″瀷**: 鏀寔涓€瀵瑰鏄犲皠鍏崇郴
4. **姝ｇ‘鐨勭粨鏋滄彁鍙?*: 浠庢纭殑鍒嗘瀽缁撴灉涓彁鍙栦俊鎭?
5. **瀹屾暣鐨勬祴璇曢獙璇?*: 绔埌绔祴璇曠‘淇濆姛鑳芥纭€?

## 馃攧 鏁版嵁娴佺▼

淇鍚庣殑瀹屾暣鏁版嵁娴佺▼锛?

```
1. 鏁版嵁杈撳叆 (PHMData)
   鈫?
2. 娴嬬偣璇勫垎鏈嶅姟 (TestPointScoringService)
   - 璇诲彇 TestPointRule 
   - 鎵ц瑙勫垯琛ㄨ揪寮?
   - 璁＄畻娴嬬偣鍒嗘暟 (0-1)
   鈫?
3. 閮ㄤ欢鏄犲皠鏈嶅姟 (ComponentMappingService)
   - 璇诲彇 TestPointComponentMapping
   - 鍒嗘瀽MSFG鍥剧粨鏋?
   - 鏋勫缓閮ㄤ欢-鏁呴殰鏄犲皠
   鈫?
4. 楂樼骇铻嶅悎绠楁硶 (AdvancedMSFGFusion)
   - 娴嬬偣鍒嗘暟 鈫?鏁呴殰姒傜巼
   - 鏁呴殰姒傜巼 鈫?閮ㄤ欢鍋ュ悍搴?
   - 閮ㄤ欢鍋ュ悍搴?鈫?绯荤粺鎬诲垎
   鈫?
5. 缁撴灉瀛樺偍 (MSFGAnalysisResult)
   - 淇濆瓨瀹屾暣鍒嗘瀽缁撴灉
   - 鍖呭惈娴嬬偣銆佹晠闅溿€侀儴浠躲€佺郴缁熷悇灞傜粨鏋?
```

## 馃И 楠岃瘉鏂规硶

### 1. 杩愯娴嬭瘯鍛戒护

```bash
# 瀹屾暣娴嬭瘯
python manage.py test_msfg_detection --create-test-data --test-full-pipeline

# 鍒嗘娴嬭瘯
python manage.py test_msfg_detection --test-scoring
python manage.py test_msfg_detection --test-mapping  
python manage.py test_msfg_detection --test-fusion
```

### 2. 妫€鏌ユ棩蹇楄緭鍑?

鏌ョ湅鏃ュ織纭锛?
- 娴嬬偣瑙勫垯琚纭墽琛?
- 閮ㄤ欢鏄犲皠鍏崇郴姝ｇ‘
- 鍒嗘瀽缁撴灉鍚堢悊
- 鏁版嵁搴撳瓨鍌ㄦ垚鍔?

### 3. 楠岃瘉鏁版嵁涓€鑷存€?

妫€鏌ワ細
- `TestPointRule` 琛ㄤ腑鐨勮鍒欐槸鍚﹁浣跨敤
- `TestPointComponentMapping` 琛ㄤ腑鐨勬槧灏勬槸鍚︾敓鏁?
- `MSFGAnalysisResult` 琛ㄤ腑鐨勭粨鏋滄槸鍚﹀畬鏁?

## 鈿狅笍 娉ㄦ剰浜嬮」

### 1. 鏁版嵁搴撹縼绉?

鐢变簬淇敼浜?`TestPointComponentMapping` 鐨勫敮涓€绾︽潫锛岄渶瑕佽繍琛屾暟鎹簱杩佺Щ锛?

```bash
python manage.py makemigrations msfg_analysis
python manage.py migrate
```

### 2. 鐜版湁鏁版嵁鍏煎鎬?

- 鐜版湁鐨?`TestPointComponentMapping` 鏁版嵁鍙兘闇€瑕佹鏌ュ拰娓呯悊
- 纭繚娌℃湁閲嶅鐨勬槧灏勫叧绯?

### 3. 鎬ц兘鑰冭檻

- 娴嬬偣瑙勫垯琛ㄨ揪寮忕殑鎵ц鏈夊畨鍏ㄩ檺鍒?
- 澶嶆潅鐨凪SFG鍥惧彲鑳介渶瑕佹洿澶氳绠楁椂闂?
- 寤鸿鍦ㄧ敓浜х幆澧冧腑鐩戞帶鎬ц兘

## 馃帀 棰勬湡鏁堟灉

淇鍚庣殑MSFG妯″潡搴旇鑳藉锛?

1. **鍑嗙‘璇勫垎**: 鏍规嵁閰嶇疆鐨勮鍒欐纭绠楁祴鐐瑰垎鏁?
2. **绮剧‘鏄犲皠**: 鍩轰簬閰嶇疆鐨勬槧灏勫叧绯诲噯纭帹瀵奸儴浠跺仴搴峰害
3. **鍙潬瀛樺偍**: 纭繚鍒嗘瀽缁撴灉瀹屾暣淇濆瓨鍒版暟鎹簱
4. **绔埌绔竴鑷?*: 浠庢暟鎹緭鍏ュ埌缁撴灉杈撳嚭鐨勫畬鏁存祦绋嬫甯稿伐浣?
5. **鍙祴璇曢獙璇?*: 閫氳繃娴嬭瘯鍛戒护楠岃瘉鎵€鏈夊姛鑳芥纭€?

杩欎簺淇纭繚浜哅SFG妯″潡鑳藉鎻愪緵鍑嗙‘銆佸彲闈犵殑澶氫俊鍙锋祦鍥惧垎鏋愬拰鍋ュ悍璇勪及鍔熻兘銆?


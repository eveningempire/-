# PHM鍨嬪彿鍏煎鎬ц鏄?

## 馃搵 姒傝堪

鏈鏇存柊涓哄鍛介娴嬬郴缁熸坊鍔犱簡**PHM鍨嬪彿鍛藉悕鍏煎鎬у姛鑳?*锛屼娇绯荤粺鑳藉鍚屾椂鏀寔 `NM` 鍜?`NMS` 涓ょ鏍煎紡鐨凜MG鍨嬪彿鍚嶇О銆?

## 鉁?鏀寔鐨凜MG鍨嬪彿鏍煎紡

| 鍩虹鍨嬪彿 | NM鏍煎紡 | NMS鏍煎紡 | 鐘舵€?|
|---------|--------|---------|------|
| 2鐗涚背 | `2NM` | `2NMS` | 鉁?鍏煎 |
| 5鐗涚背 | `5NM` | `5NMS` | 鉁?鍏煎 |
| 15鐗涚背 | `15NM` | `15NMS` | 鉁?鍏煎 |
| 500鐗涚背 | `500NM` | `500NMS` | 鉁?鍏煎 |

## 馃敡 鏍稿績鍔熻兘

### 1. 鏍囧噯鍖栧嚱鏁?`normalize_cmg_type`

鎵€鏈塽tils.py鏂囦欢涓柊澧炰簡`normalize_cmg_type`鍑芥暟锛岀敤浜庢爣鍑嗗寲PHM鍨嬪彿鍚嶇О锛?

```python
def normalize_cmg_type(cmg_type: str) -> str:
    """
    标准化CMG型号名称，兼容NM和NMS两种格式
    
    Args:
        cmg_type: 杈撳叆鐨凜MG鍨嬪彿锛堝 "500NM" 鎴?"500NMS"锛?
        
    Returns:
        鏍囧噯鍖栧悗鐨凜MG鍨嬪彿锛堜紭鍏堣繑鍥濶MS鏍煎紡锛?
        
    Examples:
        >>> normalize_cmg_type("500NM")
        "500NMS"
        >>> normalize_cmg_type("500NMS")
        "500NMS"
        >>> normalize_cmg_type("2nm")
        "2NMS"
    """
```

**鐗规€?*锛?
- 鉁?澶у皬鍐欎笉鏁忔劅锛堣嚜鍔ㄨ浆鎹负澶у啓锛?
- 鉁?鑷姩鍘婚櫎棣栧熬绌烘牸
- 鉁?NM鏍煎紡鑷姩杞崲涓篘MS鏍煎紡
- 鉁?鍙嬪ソ鐨勯敊璇彁绀?

### 2. 鏅鸿兘妯″瀷鏂囦欢鏌ユ壘

`get_model_params` 鍑芥暟宸叉洿鏂帮紝鏀寔鏅鸿兘鏌ユ壘妯″瀷鏂囦欢锛?

**鏌ユ壘椤哄簭**锛?
1. 棣栧厛灏濊瘯 NMS 鏍煎紡鏂囦欢澶癸紙濡?`models/500NMS/`锛?
2. 濡傛灉涓嶅瓨鍦紝灏濊瘯 NM 鏍煎紡鏂囦欢澶癸紙濡?`models/500NM/`锛?
3. 如果都不存在，抛出清晰的错误信息

**绀轰緥**锛?
```python
# 杈撳叆 "500NM" 鎴?"500NMS" 閮藉彲浠?
params = get_model_params("500NM", target_cols)
params = get_model_params("500NMS", target_cols)

# 绯荤粺浼氳嚜鍔ㄦ煡鎵?
# 1. lifetime_prediction/rul_predict_250917_v2/models/500NMS/ae_model.pkl
# 2. lifetime_prediction/rul_predict_250917_v2/models/500NM/ae_model.pkl
```

### 3. 鏄犲皠琛ㄨ嚜鍔ㄧ敓鎴?

`PHM_TYPE_COL_NAME_MAP` 鐜板湪鑷姩鐢熸垚NM鍜孨MS涓ょ鏍煎紡鐨勬槧灏勶細

```python
# 鍐呴儴閰嶇疆锛堝熀纭€锛?
_PHM_TYPE_COL_CONFIG = {
    "2NM": {...},
    "5NM": {...},
    "15NM": {...},
    "500NM": {...}
}

# 鑷姩鐢熸垚鐨勫吋瀹规槧灏勮〃锛堝閮ㄤ娇鐢級
PHM_TYPE_COL_NAME_MAP = {
    "2NM": {...},
    "2NMS": {...},   # 涓?NM閰嶇疆鐩稿悓
    "5NM": {...},
    "5NMS": {...},   # 涓?NM閰嶇疆鐩稿悓
    "15NM": {...},
    "15NMS": {...},  # 涓?5NM閰嶇疆鐩稿悓
    "500NM": {...},
    "500NMS": {...}  # 涓?00NM閰嶇疆鐩稿悓
}
```

## 馃搧 淇敼鐨勬枃浠跺垪琛?

浠ヤ笅鏂囦欢宸叉坊鍔犲吋瀹规€ф敮鎸侊細

### Strategy 0 (默认算法)
- 鉁?`lifetime_prediction/rul_predict_250917_v2/utils.py`

### Strategy 1 (VAE绠楁硶)
- 鉁?`lifetime_prediction/rul_predict_250917_v2/strategy1/utils.py`

### Strategy 2 (孤立森林算法)
- 鉁?`lifetime_prediction/rul_predict_250917_v2/strategy2/utils.py`

### Strategy 3 (SOM绠楁硶)
- 鉁?`lifetime_prediction/rul_predict_250917_v2/strategy3/utils.py`

## 馃挕 浣跨敤绀轰緥

### 绀轰緥1锛氱洿鎺ヤ娇鐢紙鎺ㄨ崘锛?

```python
from lifetime_prediction.rul_predict_250917_v2 import utils

# 鏂瑰紡1锛氫娇鐢∟M鏍煎紡
cmg_type = "500NM"
target_cols = utils.PHM_TYPE_COL_NAME_MAP[cmg_type]["col_names"]
params = utils.get_model_params(cmg_type, target_cols)

# 方式2：使用NMS格式（结果相同）
cmg_type = "500NMS"
target_cols = utils.PHM_TYPE_COL_NAME_MAP[cmg_type]["col_names"]
params = utils.get_model_params(cmg_type, target_cols)
```

### 绀轰緥2锛氭爣鍑嗗寲澶勭悊

```python
from lifetime_prediction.rul_predict_250917_v2.utils import normalize_cmg_type

# 缁熶竴鏍囧噯鍖栬緭鍏?
user_input = "500nm"  # 用户可能输入小写
normalized = normalize_cmg_type(user_input)  # 杩斿洖 "500NMS"

# 浣跨敤鏍囧噯鍖栧悗鐨勫瀷鍙?
target_cols = utils.PHM_TYPE_COL_NAME_MAP[normalized]["col_names"]
```

### 绀轰緥3锛氶敊璇鐞?

```python
from lifetime_prediction.rul_predict_250917_v2.utils import normalize_cmg_type

try:
    cmg_type = normalize_cmg_type("999NM")  # 不支持的型号
except ValueError as e:
    print(e)
    # 输出：不支持的CMG型号: 999NM
    #      鏀寔鐨勫瀷鍙锋牸寮? 2NM, 2NMS, 5NM, 5NMS, 15NM, 15NMS, 500NM, 500NMS
```

## 馃攧 鍚戝悗鍏煎鎬?

### 鉁?瀹屽叏鍏煎鏃т唬鐮?

鎵€鏈変娇鐢∟M鏍煎紡鐨勬棫浠ｇ爜**鏃犻渶淇敼**鍗冲彲缁х画杩愯锛?

```python
# 鏃т唬鐮侊紙NM鏍煎紡锛? 浠嶇劧鏈夋晥
cmg_type = "500NM"
params = utils.get_model_params(cmg_type, target_cols)

# 鏂颁唬鐮侊紙NMS鏍煎紡锛? 鍚屾牱鏈夋晥
cmg_type = "500NMS"
params = utils.get_model_params(cmg_type, target_cols)
```

### 鉁?妯″瀷鏂囦欢鍏煎

绯荤粺浼氳嚜鍔ㄩ€傞厤鐜版湁鐨勬ā鍨嬫枃浠跺す缁撴瀯锛?

- 濡傛灉鍙湁 `models/500NM/` 鏂囦欢澶?鈫?绯荤粺鑷姩浣跨敤璇ユ枃浠跺す
- 濡傛灉鍙湁 `models/500NMS/` 鏂囦欢澶?鈫?绯荤粺鑷姩浣跨敤璇ユ枃浠跺す
- 濡傛灉涓よ€呴兘鏈?鈫?浼樺厛浣跨敤 `500NMS` 鏍煎紡

## 馃幆 鏈€浣冲疄璺?

1. **鏂颁唬鐮佹帹鑽愪娇鐢∟MS鏍煎紡**
   ```python
   cmg_type = "500NMS"  # 鎺ㄨ崘
   ```

2. **鐢ㄦ埛杈撳叆闇€瑕佹爣鍑嗗寲**
   ```python
   user_input = request.data.get('cmg_type')
   cmg_type = normalize_cmg_type(user_input)
   ```

3. **閿欒澶勭悊瑕佸弸濂?*
   ```python
   try:
       params = get_model_params(cmg_type, target_cols)
   except FileNotFoundError as e:
       logger.error(f"妯″瀷鏂囦欢鏈壘鍒? {e}")
   except ValueError as e:
       logger.error(f"PHM型号无效: {e}")
   ```

## 馃摑 娉ㄦ剰浜嬮」

1. **鍨嬪彿澶у皬鍐?*锛氱郴缁熶細鑷姩杞崲涓哄ぇ鍐欙紝浣嗗缓璁粺涓€浣跨敤澶у啓杈撳叆
2. **鏂囦欢澶瑰懡鍚?*锛氭柊妯″瀷寤鸿浣跨敤NMS鏍煎紡鍛藉悕锛堝`500NMS`锛?
3. **日志记录**：建议在日志中记录使用的实际型号格式
4. **测试覆盖**：确保测试用例同时覆盖NM和NMS两种格式

## 🔍 常见问题

### Q1: 濡傛灉鎴戞湁鏃х殑500NM妯″瀷锛岄渶瑕侀噸鏂拌缁冨悧锛?
**A**: 涓嶉渶瑕併€傜郴缁熶細鑷姩鎵惧埌骞朵娇鐢?00NM鏍煎紡鐨勬ā鍨嬫枃浠躲€?

### Q2: NM鍜孨MS鐨勫尯鍒槸浠€涔堬紵
**A**: 鍙槸鍛藉悕鏍煎紡涓嶅悓锛岄厤缃拰鍔熻兘瀹屽叏鐩稿悓銆侼MS鏄柊鐨勬爣鍑嗗懡鍚嶆牸寮忋€?

### Q3: 濡備綍杩佺Щ鍒癗MS鏍煎紡锛?
**A**: 鍙互閫夋嫨锛?
- 鏂规1锛氶噸鍛藉悕鏂囦欢澶癸紙濡?`500NM` 鈫?`500NMS`锛?
- 鏂规2锛氫繚鎸佷笉鍙橈紝绯荤粺浼氳嚜鍔ㄥ吋瀹?

### Q4: 绯荤粺浼氫紭鍏堜娇鐢ㄥ摢绉嶆牸寮忥紵
**A**: 濡傛灉NMS鍜孨M鏂囦欢澶归兘瀛樺湪锛岀郴缁熶紭鍏堜娇鐢∟MS鏍煎紡銆?

---

**鏇存柊鏃ユ湡**: 2024骞?0鏈?5鏃? 
**鐗堟湰**: v1.0  
**缁存姢**: PHM瀵垮懡棰勬祴绯荤粺寮€鍙戝洟闃?



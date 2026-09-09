# MSFG鏁版嵁搴撳瓨鍌ㄦ洿鏂拌鏄?

## 淇敼鏃ユ湡
2025骞?0鏈?0鏃?

## 淇敼鏂囦欢
`data_management/batch_processing.py`

---

## 闂鍒嗘瀽

### 鍘熸湁闂
鎵瑰鐞嗕唬鐮佷粛鍦ㄤ娇鐢?*鏃х殑MSFG鎺ㄧ悊鏂规硶**锛岃櫧鐒舵垜浠凡缁忓疄鐜颁簡鏍囧噯鏂规硶锛屼絾鏁版嵁搴撲腑瀛樺偍鐨勪粛鏄棫鏂规硶鐨勭粨鏋滐細

```python
# 鏃ф柟娉?
component_health = fusion.calculate_component_health(
    fault_probs_array, fuzzy_probs_array, fault_nodes, component_mappings
)
```

鏃ф柟娉曞瓨鍌ㄧ殑鏁版嵁缁撴瀯锛?
```python
{
    'status': 'healthy',
    'health_score': 0.8539,
    'enhanced_impact': 0.1461,      # 鏃х畻娉曠壒鏈?
    'fault_probability': 0.09105,
    'natural_variation': 0.02148    # 鏃х畻娉曠壒鏈?
}
```

---

## 淇敼鍐呭

### 1. 鍒囨崲鍒版爣鍑哅SFG鍒嗘瀽鏂规硶

**淇敼鍓?*锛?
```python
# 鍒嗘璋冪敤搴曞眰鏂规硶
d_matrix, ... = fusion.build_d_matrix(...)
test_scores_array = np.array([...])
fault_probs_array = fusion.calculate_fault_probability(...)
fuzzy_probs_array = fusion.calculate_fuzzy_probability(...)
component_health = fusion.calculate_component_health(...)
system_health = fusion.calculate_system_health(...)
```

**淇敼鍚?*锛?
```python
# 缁熶竴浣跨敤鏍囧噯鍒嗘瀽鏂规硶
analysis_result = fusion.run_standard_analysis(
    test_scores=test_scores_for_analysis,
    test_nodes=test_nodes,
    fault_nodes=fault_nodes,
    edges=edges,
    component_mappings=component_mappings,
    msfg_definition=msfg,
    use_cmatrix=True  # 浣跨敤C鐭╅樀鏂规硶
)
```

### 2. 鏇存柊鏁版嵁搴撳瓨鍌ㄧ粨鏋?

**鏂扮殑閮ㄤ欢缁撴灉缁撴瀯**锛?
```python
component_results = {
    comp_name: {
        'health_score': float,           # 鉁?涓昏鍒嗘暟
        'status': str,                   # 鍋ュ悍鐘舵€?
        'fault_probability': float,      # 鏁呴殰姒傜巼锛堟爣鍑嗘柟娉曪級
        'fuzzy_probability': float,      # 妯＄硦姒傜巼
        'fault_count': int,              # 鏁呴殰鏁伴噺
        'max_fault_prob': float,         # 鏈€澶ф晠闅滄鐜?
        'avg_fault_prob': float,         # 骞冲潎鏁呴殰姒傜巼
        'method': 'standard_cmatrix'     # 鉁?鏍囪瘑浣跨敤鏍囧噯鏂规硶
    }
}
```

**鏂扮殑绯荤粺缁撴灉缁撴瀯**锛?
```python
system_results = {
    'overall_health': float,
    'status': str,
    'method': 'standard_cmatrix',       # 鉁?鏍囪瘑鏂规硶
    'component_count': int,
    'worst_component': str,
    'min_health': float,
    'max_health': float,
    'avg_health': float
}
```

### 3. 鏇存柊鍒嗘瀽璇︽儏

**鏂扮殑鍒嗘瀽璇︽儏**锛?
```python
'analysis_details': {
    "source": "batch_processing_standard_msfg",
    "method": "standard_cmatrix",
    "algorithm": "log_probability_with_cmatrix",  # 鉁?绠楁硶鏍囪瘑
    "total_test_nodes": int,
    "total_fault_nodes": int,
    "total_edges": int,
    "component_mappings_count": int,
    "detection_summary": {...},
    "system_health_details": {...}  # 鉁?鏂板鍋ュ悍搴﹀垎甯?
}
```

---

## 鏁版嵁瀛楁瀵规瘮

### 閮ㄤ欢缁撴灉瀛楁瀵规瘮

| 瀛楁 | 鏃ф柟娉?| 鏂版柟娉?| 璇存槑 |
|------|--------|--------|------|
| `health_score` | 鉁?| 鉁?| **涓昏鍒嗘暟**锛岄兘鏈?|
| `status` | 鉁?| 鉁?| 鍋ュ悍鐘舵€?|
| `fault_probability` | 鉁?| 鉁?| 鏁呴殰姒傜巼 |
| `fuzzy_probability` | 鉂?| 鉁?| 鏂板锛氭ā绯婃鐜?|
| `fault_count` | 鉂?| 鉁?| 鏂板锛氭晠闅滄暟閲?|
| `max_fault_prob` | 鉂?| 鉁?| 鏂板锛氭渶澶ф晠闅滄鐜?|
| `avg_fault_prob` | 鉂?| 鉁?| 鏂板锛氬钩鍧囨晠闅滄鐜?|
| `method` | 鉂?| 鉁?| 鏂板锛氭柟娉曟爣璇?|
| `enhanced_impact` | 鉁?| 鉂?| 绉婚櫎锛氭棫绠楁硶浜х墿 |
| `natural_variation` | 鉁?| 鉂?| 绉婚櫎锛氭棫绠楁硶浜х墿 |

### 绯荤粺缁撴灉瀛楁瀵规瘮

| 瀛楁 | 鏃ф柟娉?| 鏂版柟娉?| 璇存槑 |
|------|--------|--------|------|
| `overall_health` | 鉁?| 鉁?| 鏁翠綋鍋ュ悍搴?|
| `status` | 鉁?| 鉁?| 绯荤粺鐘舵€?|
| `method` | 鉂?| 鉁?| 鏂板锛氭柟娉曟爣璇?|
| `component_count` | 鉂?| 鉁?| 鏂板锛氶儴浠舵暟閲?|
| `worst_component` | 鉂?| 鉁?| 鏂板锛氭渶宸儴浠?|
| `min_health` | 鉂?| 鉁?| 鏂板锛氭渶浣庡仴搴峰害 |
| `max_health` | 鉂?| 鉁?| 鏂板锛氭渶楂樺仴搴峰害 |
| `avg_health` | 鉂?| 鉁?| 鏂板锛氬钩鍧囧仴搴峰害 |

---

## 鍏抽敭鏀硅繘

### 1. 鏁板鏂规硶鏇寸瀛?
- 鉁?浠庡姞鏉冨钩鍧囨敼涓?*瀵规暟姒傜巼鏂规硶**
- 鉁?浣跨敤**C鐭╅樀**杩涜绯荤粺绾ц仛鍚?
- 鉁?浣跨敤**鍑犱綍骞冲潎**璁＄畻鏁翠綋鍋ュ悍搴?

### 2. 鏁版嵁鏇翠赴瀵?
- 鉁?澧炲姞浜嗘晠闅滆鎯咃紙鏁伴噺銆佹渶澶у€笺€佸钩鍧囧€硷級
- 鉁?澧炲姞浜嗙郴缁熷仴搴峰害缁熻淇℃伅
- 鉁?澧炲姞浜嗘柟娉曟爣璇嗭紝渚夸簬杩芥函

### 3. 鍙拷婧€ф洿濂?
- 鉁?`method` 瀛楁鏍囪瘑浣跨敤鐨勭畻娉?
- 鉁?`algorithm` 瀛楁璇存槑鍏蜂綋绠楁硶
- 鉁?`source` 瀛楁鏍囪瘑鏁版嵁鏉ユ簮

---

## 鏁版嵁搴撴煡璇㈢ず渚?

### 璇嗗埆浣跨敤鐨勬柟娉?

```python
# 鏌ヨ浣跨敤鏍囧噯鏂规硶鐨勮褰?
from msfg_analysis.models import MSFGDetectionResult

# 妫€鏌ラ儴浠剁粨鏋滀腑鐨刴ethod瀛楁
results = MSFGDetectionResult.objects.filter(
    component_results__contains={'method': 'standard_cmatrix'}
)

# 鎴栨鏌ュ垎鏋愯鎯?
results = MSFGDetectionResult.objects.filter(
    analysis_details__method='standard_cmatrix'
)
```

### 鎻愬彇閮ㄤ欢鍋ュ悍鍒嗘暟

```python
# 鑾峰彇鏌愭妫€娴嬬殑閮ㄤ欢鍋ュ悍搴?
result = MSFGDetectionResult.objects.get(id=123)

for comp_name, comp_data in result.component_results.items():
    health_score = comp_data['health_score']  # 鉁?涓昏鍒嗘暟
    fault_prob = comp_data.get('fault_probability', 0.0)
    method = comp_data.get('method', 'unknown')
    
    print(f"{comp_name}: {health_score:.2%} (鏂规硶: {method})")
```

### 瀵规瘮鏂版棫鏂规硶缁撴灉

```python
# 鏌ヨ鏃ф柟娉曠粨鏋滐紙鏃爉ethod瀛楁锛?
old_results = MSFGDetectionResult.objects.exclude(
    component_results__contains={'method': 'standard_cmatrix'}
)

# 鏌ヨ鏂版柟娉曠粨鏋滐紙鏈塵ethod瀛楁锛?
new_results = MSFGDetectionResult.objects.filter(
    component_results__contains={'method': 'standard_cmatrix'}
)

print(f"鏃ф柟娉曡褰? {old_results.count()}")
print(f"鏂版柟娉曡褰? {new_results.count()}")
```

---

## 鍓嶇鏄剧ず寤鸿

### 1. 濮嬬粓浣跨敤 `health_score`

```javascript
// 鉁?姝ｇ‘
const healthScore = componentData.health_score;

// 鉂?閿欒
const healthScore = 1 - componentData.fault_probability;
```

### 2. 鏍规嵁 `method` 鏄剧ず涓嶅悓淇℃伅

```javascript
if (componentData.method === 'standard_cmatrix') {
    // 鏂版柟娉曪細鏄剧ず璇︾粏淇℃伅
    console.log('鏁呴殰鏁伴噺:', componentData.fault_count);
    console.log('鏈€澶ф晠闅滄鐜?', componentData.max_fault_prob);
    console.log('骞冲潎鏁呴殰姒傜巼:', componentData.avg_fault_prob);
} else {
    // 鏃ф柟娉曪細鏄剧ず浼犵粺淇℃伅
    console.log('澧炲己褰卞搷:', componentData.enhanced_impact);
    console.log('鑷劧鍙樺寲:', componentData.natural_variation);
}
```

### 3. 鏄剧ず鏂规硶鏍囪瘑

```javascript
// 鍦║I涓婃爣璇嗕娇鐢ㄧ殑鏂规硶
const methodLabel = {
    'standard_cmatrix': '鏍囧噯鏂规硶锛堝鏁版鐜?C鐭╅樀锛?,
    'legacy': '浼犵粺鏂规硶',
    undefined: '鏈煡鏂规硶'
};

const label = methodLabel[componentData.method || undefined];
```

---

## 鍚戝悗鍏煎鎬?

### 淇濇寔鍏煎鐨勫瓧娈?
- 鉁?`health_score` - 閮芥湁锛屼富瑕佸垎鏁?
- 鉁?`status` - 閮芥湁锛屽仴搴风姸鎬?
- 鉁?`fault_probability` - 閮芥湁锛屾晠闅滄鐜?

### 鏂板鐨勫瓧娈碉紙鏃ц褰曚腑涓嶅瓨鍦級
- `fuzzy_probability`
- `fault_count`
- `max_fault_prob`
- `avg_fault_prob`
- `method`

### 绉婚櫎鐨勫瓧娈碉紙鏂拌褰曚腑涓嶅瓨鍦級
- `enhanced_impact` - 浠呮棫鏂规硶鏈?
- `natural_variation` - 浠呮棫鏂规硶鏈?

### 鍏煎浠ｇ爜绀轰緥

```python
# 鍏煎鏂版棫涓ょ鏍煎紡
def get_component_health_score(comp_data):
    """鑾峰彇閮ㄤ欢鍋ュ悍鍒嗘暟锛堝吋瀹规柊鏃ф牸寮忥級"""
    return float(comp_data.get('health_score', 1.0))

def get_fault_probability(comp_data):
    """鑾峰彇鏁呴殰姒傜巼锛堝吋瀹规柊鏃ф牸寮忥級"""
    return float(comp_data.get('fault_probability', 0.0))

def is_standard_method(comp_data):
    """鍒ゆ柇鏄惁浣跨敤鏍囧噯鏂规硶"""
    return comp_data.get('method') == 'standard_cmatrix'

def get_additional_info(comp_data):
    """鑾峰彇棰濆淇℃伅锛堟牴鎹柟娉曪級"""
    if is_standard_method(comp_data):
        return {
            'fault_count': comp_data.get('fault_count', 0),
            'max_fault_prob': comp_data.get('max_fault_prob', 0.0),
            'avg_fault_prob': comp_data.get('avg_fault_prob', 0.0)
        }
    else:
        return {
            'enhanced_impact': comp_data.get('enhanced_impact', 0.0),
            'natural_variation': comp_data.get('natural_variation', 0.0)
        }
```

---

## 楠岃瘉鏂规硶

### 1. 妫€鏌ユ棩蹇?

鎵瑰鐞嗚繍琛屾椂浼氳緭鍑猴細
```
INFO: 浣跨敤鏍囧噯MSFG鎺ㄧ悊鏂规硶锛堝鏁版鐜?+ C鐭╅樀锛?
DEBUG: MSFG妫€娴嬪畬鎴? PHM xxx, 鍋ュ悍鍒嗘暟 x.xxx, ...
```

### 2. 妫€鏌ユ暟鎹簱

```python
# 鏌ヨ鏈€鏂扮殑MSFG妫€娴嬬粨鏋?
result = MSFGDetectionResult.objects.latest('created_at')

# 妫€鏌ユ槸鍚︿娇鐢ㄦ爣鍑嗘柟娉?
print("鍒嗘瀽鏉ユ簮:", result.analysis_details.get('source'))
print("浣跨敤鏂规硶:", result.analysis_details.get('method'))
print("绠楁硶:", result.analysis_details.get('algorithm'))

# 妫€鏌ラ儴浠剁粨鏋?
for comp_name, comp_data in result.component_results.items():
    print(f"{comp_name}:")
    print(f"  鍋ュ悍鍒嗘暟: {comp_data['health_score']}")
    print(f"  鏂规硶: {comp_data.get('method', 'unknown')}")
    print(f"  鏁呴殰鏁伴噺: {comp_data.get('fault_count', 'N/A')}")
```

### 3. 瀵规瘮缁撴灉

鍙互瀵煎叆鐩稿悓鏁版嵁涓ゆ锛堜竴娆＄敤鏃ф柟娉曪紝涓€娆＄敤鏂版柟娉曪級杩涜瀵规瘮锛?
```python
# 瀵规瘮鏂版棫鏂规硶鐨勫仴搴峰垎鏁板樊寮?
old_score = old_result.component_results['閮ㄤ欢A']['health_score']
new_score = new_result.component_results['閮ㄤ欢A']['health_score']
diff = new_score - old_score

print(f"鏃ф柟娉? {old_score:.4f}")
print(f"鏂版柟娉? {new_score:.4f}")
print(f"宸紓: {diff:+.4f} ({diff/old_score*100:+.1f}%)")
```

---

## 鎬荤粨

鉁?**淇敼瀹屾垚**锛氭壒澶勭悊鐜板湪浣跨敤鏍囧噯MSFG鎺ㄧ悊鏂规硶

鉁?**鏁版嵁搴撳瓨鍌?*锛氭柊鐨勬娴嬬粨鏋滃寘鍚畬鏁寸殑鏍囧噯鏂规硶杈撳嚭

鉁?**鍚戝悗鍏煎**锛氫繚鐣欎簡鍏抽敭瀛楁锛坄health_score`, `status`, `fault_probability`锛?

鉁?**鍙拷婧€?*锛氶€氳繃 `method` 瀛楁鍙互璇嗗埆浣跨敤鐨勭畻娉?

鉁?**鏁版嵁涓板瘜**锛氭柊澧炰簡鏇村鏈夌敤鐨勭粺璁′俊鎭?

**鍏抽敭瑕佺偣**锛?
- **`health_score`** 鏄富瑕佺殑閮ㄤ欢鍒嗘暟锛?-1鑼冨洿锛?
- **`method`** 瀛楁鏍囪瘑浣跨敤鐨勭畻娉?
- 鏂版柟娉曟彁渚涗簡鏇村璇婃柇淇℃伅
- 鍓嶇浠ｇ爜闇€瑕佹牴鎹?`method` 瀛楁閫傞厤鏄剧ず



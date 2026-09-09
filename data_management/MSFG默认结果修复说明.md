# MSFG榛樿缁撴灉淇璇存槑

## 馃敡 鍙戠幇鐨勯棶棰?

鐢ㄦ埛鍙嶉锛?*姝ｅ父甯х殑MSFG缁撴灉涓己灏戜簡涓€浜涙祴鐐瑰垎鏁板拰鏁呴殰鍒嗘暟**

## 馃幆 鏍规湰鍘熷洜

### 闂1锛氭祬鎷疯礉瀵艰嚧鏁版嵁鍏变韩 鉂?

**鍘熶唬鐮?*锛堢2503-2506琛岋級锛?
```python
'test_results': default_test_results.copy(),      # 鉂?娴呮嫹璐?
'fault_results': default_fault_results.copy(),    # 鉂?娴呮嫹璐?
'system_results': default_system_results.copy(),  # 鉂?娴呮嫹璐?
'component_results': default_component_results.copy(),  # 鉂?娴呮嫹璐?
```

**闂璇存槑**锛?
- `.copy()` 鍙槸**娴呮嫹璐?*锛屽鍒跺灞傚瓧鍏?
- 鍐呭眰瀛楀吀瀵硅薄浠嶇劧琚涓褰曞叡浜?
- 褰撴煇涓褰曚慨鏀规暟鎹椂锛屼細褰卞搷鍏朵粬鎵€鏈夎褰?

**绀轰緥璇存槑**锛?
```python
# 娴呮嫹璐濈殑闂
default_test_results = {
    '娴嬬偣1': {'test_score': 0.0, 'status': 'normal'},
    '娴嬬偣2': {'test_score': 0.0, 'status': 'normal'}
}

record1_result = default_test_results.copy()
record2_result = default_test_results.copy()

# 淇敼record1鐨勬祴鐐?
record1_result['娴嬬偣1']['test_score'] = 0.5

# 鉂?record2鐨勬祴鐐?涔熻淇敼浜嗭紒
print(record2_result['娴嬬偣1']['test_score'])  # 杈撳嚭: 0.5 (閿欒锛?
```

## 鉁?淇鏂规

### 淇1锛氫娇鐢ㄦ繁鎷疯礉

**淇鍚庝唬鐮?*锛堢2515-2518琛岋級锛?
```python
import copy

'test_results': copy.deepcopy(default_test_results),      # 鉁?娣辨嫹璐?
'fault_results': copy.deepcopy(default_fault_results),    # 鉁?娣辨嫹璐?
'system_results': copy.deepcopy(default_system_results),  # 鉁?娣辨嫹璐?
'component_results': copy.deepcopy(default_component_results),  # 鉁?娣辨嫹璐?
```

**浼樺娍**锛?
- 鉁?瀹屽叏鐙珛鐨勬暟鎹壇鏈?
- 鉁?姣忎釜璁板綍淇敼鏁版嵁涓嶄細褰卞搷鍏朵粬璁板綍
- 鉁?淇濊瘉鏁版嵁瀹屾暣鎬?

**绀轰緥璇存槑**锛?
```python
# 娣辨嫹璐濈殑姝ｇ‘琛屼负
import copy

record1_result = copy.deepcopy(default_test_results)
record2_result = copy.deepcopy(default_test_results)

# 淇敼record1鐨勬祴鐐?
record1_result['娴嬬偣1']['test_score'] = 0.5

# 鉁?record2鐨勬祴鐐?涓嶅彈褰卞搷
print(record2_result['娴嬬偣1']['test_score'])  # 杈撳嚭: 0.0 (姝ｇ‘锛?
```

### 淇2锛氭坊鍔犺缁嗘棩蹇楅獙璇?

**鏂板鏃ュ織**锛堢2443-2558琛岋級锛?

#### 2.1 鑺傜偣淇℃伅楠岃瘉
```python
logger.info(f"MSFG鑺傜偣淇℃伅: 娴嬬偣鏁?{len(test_nodes)}, 鏁呴殰鏁?{len(fault_nodes)}, 閮ㄤ欢鏁?{len(component_nodes)}")
logger.info(f"娴嬬偣鍒楄〃: {[node.name for node in test_nodes]}")
logger.info(f"鏁呴殰鍒楄〃: {[node.name for node in fault_nodes]}")
```

**杈撳嚭绀轰緥**锛?
```
[INFO] MSFG鑺傜偣淇℃伅: 娴嬬偣鏁?12, 鏁呴殰鏁?8, 閮ㄤ欢鏁?5
[INFO] 娴嬬偣鍒楄〃: ['杞瓙娓╁害', '妗嗘灦娓╁害', '杞瓙鐢垫祦', '杞瓙杞€?, ...]
[INFO] 鏁呴殰鍒楄〃: ['杞存壙纾ㄦ崯', '鐢垫満鏁呴殰', '鐢靛帇寮傚父', ...]
```

#### 2.2 鏋勫缓楠岃瘉
```python
logger.info(f"鉁?宸叉瀯寤?{len(default_test_results)} 涓祴鐐圭殑榛樿缁撴灉")
logger.info(f"鉁?宸叉瀯寤?{len(default_fault_results)} 涓晠闅滅殑榛樿缁撴灉")
```

**杈撳嚭绀轰緥**锛?
```
[INFO] 鉁?宸叉瀯寤?12 涓祴鐐圭殑榛樿缁撴灉
[INFO] 鉁?宸叉瀯寤?8 涓晠闅滅殑榛樿缁撴灉
```

#### 2.3 缁撴灉楠岃瘉
```python
logger.info(f"鉁?鎴愬姛鐢熸垚 {len(default_results)} 涓粯璁SFG缁撴灉")
logger.info(f"姣忎釜缁撴灉鍖呭惈: 娴嬬偣鏁?{len(sample_result['test_results'])}, "
          f"鏁呴殰鏁?{len(sample_result['fault_results'])}, "
          f"閮ㄤ欢鏁?{len(sample_result['component_results'])}")
```

**杈撳嚭绀轰緥**锛?
```
[INFO] 鉁?鎴愬姛鐢熸垚 800 涓粯璁SFG缁撴灉
[INFO] 姣忎釜缁撴灉鍖呭惈: 娴嬬偣鏁?12, 鏁呴殰鏁?8, 閮ㄤ欢鏁?5
```

#### 2.4 鏁版嵁鐙珛鎬ч獙璇?
```python
if len(default_results) > 1:
    first_test_results = default_results[0]['test_results']
    second_test_results = default_results[1]['test_results']
    if first_test_results is second_test_results:
        logger.warning("鈿狅笍 璀﹀憡锛氭娴嬪埌娴呮嫹璐濋棶棰橈紝澶氫釜璁板綍鍏变韩鍚屼竴涓瓧鍏稿璞?)
    else:
        logger.info("鉁?鏁版嵁鐙珛鎬ч獙璇侀€氳繃锛屾瘡涓褰曢兘鏈夌嫭绔嬬殑鏁版嵁鍓湰")
```

**杈撳嚭绀轰緥**锛?
```
[INFO] 鉁?鏁版嵁鐙珛鎬ч獙璇侀€氳繃锛屾瘡涓褰曢兘鏈夌嫭绔嬬殑鏁版嵁鍓湰
```

## 馃攳 楠岃瘉涓€鑷存€?

### 寮傚父甯?vs 姝ｅ父甯х殑鑺傜偣鑾峰彇鏂规硶

#### 寮傚父甯э紙瀹為檯妫€娴嬶級- `_run_msfg_detection()` 绗?114琛?
```python
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

fusion = AdvancedMSFGFusion()
test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg)
```

#### 姝ｅ父甯э紙榛樿鍊硷級- `_generate_default_msfg_results()` 绗?441琛?
```python
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

fusion = AdvancedMSFGFusion()
test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg_definition)
```

**缁撹**锛氣渽 **瀹屽叏涓€鑷?*锛屼娇鐢ㄧ浉鍚岀殑鏂规硶鑾峰彇鑺傜偣

## 馃搳 濡備綍楠岃瘉淇鏁堟灉

### 姝ラ1锛氭煡鐪嬫棩蹇楄緭鍑?

涓婁紶鏂囦欢鍚庯紝妫€鏌ョ粓绔棩蹇椾腑鐨勪互涓嬩俊鎭細

```
[INFO] 涓?800 涓甯稿抚鐢熸垚榛樿MSFG缁撴灉
[INFO] MSFG鑺傜偣淇℃伅: 娴嬬偣鏁?12, 鏁呴殰鏁?8, 閮ㄤ欢鏁?5
[INFO] 娴嬬偣鍒楄〃: ['杞瓙娓╁害', '妗嗘灦娓╁害', '杞瓙鐢垫祦', ...]
[INFO] 鏁呴殰鍒楄〃: ['杞存壙纾ㄦ崯', '鐢垫満鏁呴殰', '鐢靛帇寮傚父', ...]
[INFO] 鉁?宸叉瀯寤?12 涓祴鐐圭殑榛樿缁撴灉
[INFO] 鉁?宸叉瀯寤?8 涓晠闅滅殑榛樿缁撴灉
[INFO] 鉁?鎴愬姛鐢熸垚 800 涓粯璁SFG缁撴灉
[INFO] 姣忎釜缁撴灉鍖呭惈: 娴嬬偣鏁?12, 鏁呴殰鏁?8, 閮ㄤ欢鏁?5
[INFO] 鉁?鏁版嵁鐙珛鎬ч獙璇侀€氳繃锛屾瘡涓褰曢兘鏈夌嫭绔嬬殑鏁版嵁鍓湰
```

### 姝ラ2锛氭鏌ユ暟鎹簱

```python
from msfg_analysis.models import MSFGAnalysisResult

# 鏌ヨ涓€涓甯稿抚鐨凪SFG缁撴灉
normal_frame = PHMData.objects.filter(
    ims_detectionresult__is_anomaly=False
).first()

msfg_result = MSFGAnalysisResult.objects.get(data_point=normal_frame)

# 楠岃瘉娴嬬偣鏁伴噺
test_count = len(msfg_result.test_results)
print(f"娴嬬偣鏁伴噺: {test_count}")
print(f"娴嬬偣鍒楄〃: {list(msfg_result.test_results.keys())}")

# 楠岃瘉鏁呴殰鏁伴噺
fault_count = len(msfg_result.fault_results)
print(f"鏁呴殰鏁伴噺: {fault_count}")
print(f"鏁呴殰鍒楄〃: {list(msfg_result.fault_results.keys())}")

# 楠岃瘉娴嬬偣鍒嗘暟閮戒负0
test_scores = [v['test_score'] for v in msfg_result.test_results.values()]
print(f"娴嬬偣鍒嗘暟: {test_scores}")  # 搴旇閮芥槸 0.0

# 楠岃瘉鏁呴殰姒傜巼閮戒负0
fault_probs = [v['fault_probability'] for v in msfg_result.fault_results.values()]
print(f"鏁呴殰姒傜巼: {fault_probs}")  # 搴旇閮芥槸 0.0

# 楠岃瘉鍋ュ悍鍒嗘暟涓?.0
print(f"鏁翠綋鍋ュ悍鍒嗘暟: {msfg_result.overall_health_score}")  # 搴旇鏄?1.0
```

### 姝ラ3锛氬姣斿紓甯稿抚鍜屾甯稿抚

```python
# 鑾峰彇涓€涓紓甯稿抚鐨凪SFG缁撴灉
anomaly_frame = PHMData.objects.filter(
    ims_detectionresult__is_anomaly=True
).first()

anomaly_msfg = MSFGAnalysisResult.objects.get(data_point=anomaly_frame)
normal_msfg = MSFGAnalysisResult.objects.get(data_point=normal_frame)

# 瀵规瘮娴嬬偣鏁伴噺
print(f"寮傚父甯ф祴鐐规暟: {len(anomaly_msfg.test_results)}")
print(f"姝ｅ父甯ф祴鐐规暟: {len(normal_msfg.test_results)}")
# 搴旇鐩哥瓑锛?

# 瀵规瘮鏁呴殰鏁伴噺
print(f"寮傚父甯ф晠闅滄暟: {len(anomaly_msfg.fault_results)}")
print(f"姝ｅ父甯ф晠闅滄暟: {len(normal_msfg.fault_results)}")
# 搴旇鐩哥瓑锛?

# 瀵规瘮娴嬬偣鍒楄〃
anomaly_tests = set(anomaly_msfg.test_results.keys())
normal_tests = set(normal_msfg.test_results.keys())
print(f"娴嬬偣鍒楄〃鏄惁鐩稿悓: {anomaly_tests == normal_tests}")
# 搴旇涓?True锛?

# 瀵规瘮鏁呴殰鍒楄〃
anomaly_faults = set(anomaly_msfg.fault_results.keys())
normal_faults = set(normal_msfg.fault_results.keys())
print(f"鏁呴殰鍒楄〃鏄惁鐩稿悓: {anomaly_faults == normal_faults}")
# 搴旇涓?True锛?
```

## 馃幆 棰勬湡缁撴灉

淇鍚庯紝姝ｅ父甯х殑MSFG缁撴灉搴旇锛?

### 鉁?鍖呭惈瀹屾暣鐨勬祴鐐瑰垎鏁?
```json
{
  "test_results": {
    "杞瓙娓╁害": {"test_score": 0.0, "status": "normal"},
    "妗嗘灦娓╁害": {"test_score": 0.0, "status": "normal"},
    "杞瓙鐢垫祦": {"test_score": 0.0, "status": "normal"},
    "杞瓙杞€?: {"test_score": 0.0, "status": "normal"},
    ... // 鎵€鏈夋祴鐐归兘鍖呭惈
  }
}
```

### 鉁?鍖呭惈瀹屾暣鐨勬晠闅滄鐜?
```json
{
  "fault_results": {
    "杞存壙纾ㄦ崯": {"fault_probability": 0.0, "severity": "none"},
    "鐢垫満鏁呴殰": {"fault_probability": 0.0, "severity": "none"},
    "鐢靛帇寮傚父": {"fault_probability": 0.0, "severity": "none"},
    ... // 鎵€鏈夋晠闅滈兘鍖呭惈
  }
}
```

### 鉁?姣忎釜璁板綍閮芥湁鐙珛鐨勬暟鎹壇鏈?
```python
# 淇敼绗竴涓褰曚笉浼氬奖鍝嶇浜屼釜璁板綍
result1['test_results']['杞瓙娓╁害']['test_score'] = 0.5
result2['test_results']['杞瓙娓╁害']['test_score']  # 浠嶇劧鏄?0.0
```

## 馃毃 鍙兘鐨勫叾浠栭棶棰?

濡傛灉淇鍚庝粛鐒剁己灏戞祴鐐规垨鏁呴殰锛屽彲鑳芥槸锛?

### 闂1锛歁SFG瀹氫箟涓嶅畬鏁?
- 妫€鏌SFG瀹氫箟涓殑娴嬬偣鑺傜偣鍜屾晠闅滆妭鐐规槸鍚﹀畬鏁?
- 浣跨敤Django绠＄悊鍚庡彴鏌ョ湅MSFG瀹氫箟

### 闂2锛氳妭鐐圭被鍨嬩笉鍖归厤
- 妫€鏌ヨ妭鐐圭被鍨嬫槸鍚︽纭紙TestNode vs FaultNode锛?
- 浣跨敤鏃ュ織杈撳嚭鐨勮妭鐐瑰垪琛ㄩ獙璇?

### 闂3锛氭暟鎹簱鏌ヨ杩囨护
- 妫€鏌ユ槸鍚︽湁棰濆鐨勮繃婊ゆ潯浠跺鑷撮儴鍒嗚妭鐐硅鎺掗櫎
- 浣跨敤 `fusion.get_unified_nodes()` 杩斿洖鐨勫師濮嬭妭鐐瑰垪琛?

## 馃摑 鎬荤粨

鏈淇鐨勬牳蹇冩敼杩涳細

1. 鉁?**浣跨敤娣辨嫹璐?*锛氱‘淇濇瘡涓褰曢兘鏈夊畬鍏ㄧ嫭绔嬬殑鏁版嵁鍓湰
2. 鉁?**娣诲姞璇︾粏鏃ュ織**锛氬府鍔╅獙璇佽妭鐐逛俊鎭€佹瀯寤鸿繃绋嬪拰鏁版嵁瀹屾暣鎬?
3. 鉁?**鏁版嵁鐙珛鎬ч獙璇?*锛氳繍琛屾椂鑷姩妫€娴嬫祬鎷疯礉闂
4. 鉁?**鏂规硶涓€鑷存€?*锛氬紓甯稿抚鍜屾甯稿抚浣跨敤瀹屽叏鐩稿悓鐨勮妭鐐硅幏鍙栨柟娉?

杩欐牱鍙互纭繚锛?
- 鎵€鏈夋祴鐐瑰垎鏁伴兘琚纭啓鍏?
- 鎵€鏈夋晠闅滄鐜囬兘琚纭啓鍏?
- 姣忎釜璁板綍鐨勬暟鎹兘鏄嫭绔嬬殑
- 渚夸簬璇婃柇鍜岄獙璇?

濡傛灉浠嶇劧鍙戠幇缂哄皯鏁版嵁锛岃鏌ョ湅鏃ュ織杈撳嚭鐨勮妭鐐瑰垪琛紝纭MSFG瀹氫箟涓槸鍚﹀寘鍚墍鏈夋湡鏈涚殑娴嬬偣鍜屾晠闅溿€?



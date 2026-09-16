# 妯″瀷瀛楁鍚嶇О淇

## 馃悰 閿欒淇℃伅

```
AttributeError: 'IMSDetectionResult' object has no attribute 'scores'
```

**鍙戠敓浣嶇疆**锛歚data_management/batch_processing.py` 绗?60琛? 
**鍙戠敓闃舵**锛氭敹闆嗘娴嬬粨鏋?

---

## 🔍 问题分析

### IMSDetectionResult妯″瀷鐨勫疄闄呭瓧娈?

```python
class IMSDetectionResult(models.Model):
    data_point = models.OneToOneField(PHMData, ...)
    ims_model = models.ForeignKey(IMSModel, ...)
    is_anomaly = models.BooleanField(...)
    anomaly_score = models.FloatField(...)
    parameter_scores = models.JSONField(...)  # 鉁?姝ｇ‘瀛楁鍚?
    detection_details = models.JSONField(...)
    created_at = models.DateTimeField(...)
```

**鍏抽敭瀛楁**锛?
- 鉁?`parameter_scores` - 鍚勫弬鏁板紓甯稿垎鏁?
- 鉁?`detection_details` - 妫€娴嬭缁嗕俊鎭?
- 鉂?`scores` - 涓嶅瓨鍦ㄦ瀛楁

---

## 鉁?淇鏂规

### 淇鍓?
```python
'ims_result': {
    'is_anomaly': ims_res.is_anomaly,
    'anomaly_score': float(ims_res.anomaly_score),
    'scores': ims_res.scores  # 鉂?閿欒瀛楁鍚?
} if ims_res else None
```

### 淇鍚?
```python
'ims_result': {
    'is_anomaly': ims_res.is_anomaly,
    'anomaly_score': float(ims_res.anomaly_score) if ims_res.anomaly_score else 0.0,
    'parameter_scores': ims_res.parameter_scores if ims_res else {},  # 鉁?姝ｇ‘
    'detection_details': ims_res.detection_details if ims_res else {}  # 鉁?鏂板
} if ims_res else None
```

---

## 馃敡 棰濆鏀硅繘

鍦ㄤ慨澶嶅瓧娈靛悕鐨勫悓鏃讹紝鎴戜篃瀹屽杽浜嗗叾浠栨娴嬬粨鏋滅殑瀛楁锛?

### 瑙勫垯妫€娴嬬粨鏋?
```python
'rule_result': {
    'has_violation': True if rule_res else False,
    'triggered_rules': rule_res.triggered_rules if rule_res else [],
    'violation_details': rule_res.violation_details if ... else []  # 鉁?鏂板
}
```

### MSFG妫€娴嬬粨鏋?
```python
'msfg_result': {
    'component_health': msfg_res.component_results if msfg_res else {},
    'overall_health': msfg_res.system_results.get('overall_health') if ... else None,
    'test_results': msfg_res.test_results if ... else {},    # 鉁?鏂板
    'fault_results': msfg_res.fault_results if ... else {}   # 鉁?鏂板
}
```

浣跨敤`hasattr`杩涜瀹夊叏妫€鏌ワ紝閬垮厤瀛楁涓嶅瓨鍦ㄦ椂鎶ラ敊銆?

---

## 馃搳 妫€娴嬫垚鍔熺殑璇佹嵁

从您的日志可以看到：
```
INFO: [娓呯悊] 鍒犻櫎妫€娴嬬粨鏋? IMS=51, 瑙勫垯=306, MSFG=51
INFO: [娓呯悊] 鍒犻櫎鍘熷鏁版嵁: 1000 鏉¤褰?
```

**璇存槑**锛?
- 鉁?鎴愬姛澶勭悊浜?000鏉℃暟鎹紙max_rows鐢熸晥锛侊級
- 鉁?IMS妫€娴嬫垚鍔燂細51涓粨鏋?
- 鉁?瑙勫垯妫€娴嬫垚鍔燂細306涓粨鏋?
- 鉁?MSFG妫€娴嬫垚鍔燂細51涓粨鏋?
- 鉁?妫€娴嬪畬鎴愬苟姝ｇ‘娓呯悊

**鍙槸鍦ㄦ敹闆嗙粨鏋滈樁娈靛瓧娈靛悕閿欒锛岀幇鍦ㄥ凡淇锛?*

---

## 📝 修改总结

**修改文件**：`data_management/batch_processing.py`

**淇敼浣嶇疆**锛氱453-474琛岋紙`_collect_detection_results`鏂规硶锛?

**淇敼鍐呭**锛?
1. `scores` 鈫?`parameter_scores`
2. 娣诲姞`detection_details`瀛楁
3. 娣诲姞`violation_details`瀛楁锛堣鍒欐娴嬶級
4. 娣诲姞`test_results`鍜宍fault_results`瀛楁锛圡SFG妫€娴嬶級
5. 浣跨敤`hasattr`杩涜瀹夊叏妫€鏌?

**璇硶妫€鏌?*锛氣渽 閫氳繃

---

## 馃帀 妫€娴嬪姛鑳藉凡瀹屽叏姝ｅ父锛?

鏍规嵁鏃ュ織鏄剧ず锛?
- 鉁?1000鏉℃暟鎹垚鍔熷鐞?
- 鉁?鎵€鏈夋娴嬫ā鍧楁甯歌繍琛?
- 鉁?妫€娴嬬粨鏋滄纭繚瀛?
- 鉁?涓存椂鏁版嵁姝ｇ‘娓呯悊

**鐜板湪鍐嶆娴嬭瘯锛屽簲璇ヨ兘鎴愬姛鑾峰彇妫€娴嬬粨鏋滃苟鏄剧ず鍦ㄩ〉闈笂浜嗭紒** 馃殌

---

**淇鏃堕棿**锛?025-10-10  
**淇绫诲瀷**锛氬瓧娈靛悕绉扮籂姝? 
**娴嬭瘯鐘舵€?*锛氣渽 妫€娴嬪凡鎴愬姛鎵ц



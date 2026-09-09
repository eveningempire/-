# 鏁版嵁搴撴ā鍨嬪瓧娈靛畬鏁村弬鑰?

## 馃摎 鎵€鏈夋娴嬬浉鍏虫ā鍨嬬殑瀛楁娓呭崟

### 1锔忊儯 IMSDetectionResult
**鏂囦欢**锛歚health_management/models.py`  
**鍏崇郴**锛歄neToOneField(PHMData)

| 瀛楁鍚?| 绫诲瀷 | 璇存槑 |
|--------|------|------|
| `data_point` | OneToOneField | 鍏宠仈鐨凜MGData |
| `ims_model` | ForeignKey | 浣跨敤鐨処MS妯″瀷 |
| `is_anomaly` | BooleanField | 鏄惁寮傚父 鉁?|
| `anomaly_score` | FloatField | 寮傚父鍒嗘暟 鉁?|
| `parameter_scores` | JSONField | 鍚勫弬鏁板垎鏁?鉁?|
| `detection_details` | JSONField | 妫€娴嬭鎯?鉁?|
| `created_at` | DateTimeField | 鍒涘缓鏃堕棿 |

**璁块棶绀轰緥**锛?
```python
ims_res = IMSDetectionResult.objects.filter(data_point=record).first()
is_anomaly = ims_res.is_anomaly
score = ims_res.anomaly_score
params = ims_res.parameter_scores  # 鉁?涓嶆槸 scores
details = ims_res.detection_details
```

---

### 2锔忊儯 RuleDefinition
**鏂囦欢**锛歚rule_detection/models.py`  
**璇存槑**锛氳鍒欏畾涔夛紙涓嶆槸妫€娴嬬粨鏋滐級

| 瀛楁鍚?| 绫诲瀷 | 璇存槑 |
|--------|------|------|
| `cmg_model` | ForeignKey | 鍏宠仈鐨凜MG妯″瀷 |
| `fault_definition` | ForeignKey | 鍏宠仈鐨勬晠闅滃畾涔?|
| `rule_id` | CharField | 瑙勫垯ID 鉁?|
| `rule_expression` | TextField | 瑙勫垯琛ㄨ揪寮?鉁?|
| `source` | CharField | 瑙勫垯鏉ユ簮 |
| `plan_description` | TextField | 棰勬鎻忚堪 |
| `is_online` | BooleanField | 鏄惁鍦ㄧ嚎鍚敤 |
| `is_new` | BooleanField | 鏄惁涓烘柊瑙勫垯 |
| `is_editable` | BooleanField | 鏄惁鍙紪杈?|
| `related_parameters` | JSONField | 娑夊強鐨勫弬鏁板垪琛?|
| `compiled_rule` | JSONField | 缂栬瘧鍚庣殑瑙勫垯 |

**鉂?娌℃湁 `name` 瀛楁锛屼娇鐢?`rule_id`**

---

### 3锔忊儯 FaultDefinition
**鏂囦欢**锛歚rule_detection/models.py`  
**璇存槑**锛氭晠闅滃畾涔?

| 瀛楁鍚?| 绫诲瀷 | 璇存槑 |
|--------|------|------|
| `cmg_model` | ForeignKey | 鍏宠仈鐨凜MG妯″瀷 |
| `fault_name` | CharField | 鏁呴殰鍚嶇О 鉁?|
| `fault_level` | IntegerField | 鏁呴殰绛夌骇 |
| `component` | CharField | 娑夊強閮ㄤ欢 |
| `description` | TextField | 鏁呴殰鎻忚堪 |

**鉂?娌℃湁 `name` 瀛楁锛屼娇鐢?`fault_name`**

---

### 4锔忊儯 RuleDetectionResult
**鏂囦欢**锛歚rule_detection/models.py`  
**鍏崇郴**锛欶oreignKey(PHMData) - 涓€瀵瑰

| 瀛楁鍚?| 绫诲瀷 | 璇存槑 |
|--------|------|------|
| `data_point` | ForeignKey | 鍏宠仈鐨凜MGData |
| `rule_definition` | ForeignKey | 瑙﹀彂鐨勮鍒?鉁?|
| `fault_definition` | ForeignKey | 妫€娴嬪埌鐨勬晠闅?鉁?|
| `is_triggered` | BooleanField | 瑙勫垯鏄惁瑙﹀彂 鉁?|
| `confidence_score` | FloatField | 缃俊搴﹀垎鏁?鉁?|
| `detection_details` | JSONField | 妫€娴嬭鎯?鉁?|
| `created_at` | DateTimeField | 鍒涘缓鏃堕棿 |

**璁块棶绀轰緥**锛?
```python
rule_res_list = RuleDetectionResult.objects.filter(data_point=record)
for rule_res in rule_res_list:
    rule_id = rule_res.rule_definition.rule_id       # 鉁?涓嶆槸 name
    fault_name = rule_res.fault_definition.fault_name  # 鉁?涓嶆槸 name
    is_triggered = rule_res.is_triggered
    score = rule_res.confidence_score
```

---

### 5锔忊儯 MSFGAnalysisResult
**鏂囦欢**锛歚msfg_analysis/models.py`  
**鍏崇郴**锛欶oreignKey(PHMData) - 涓€瀵瑰

| 瀛楁鍚?| 绫诲瀷 | 璇存槑 |
|--------|------|------|
| `data_point` | ForeignKey | 鍏宠仈鐨凜MGData |
| `msfg_definition` | ForeignKey | 浣跨敤鐨凪SFG瀹氫箟 |
| `test_results` | JSONField | 娴嬭瘯鐐圭粨鏋?鉁?|
| `fault_results` | JSONField | 鏁呴殰鐐圭粨鏋?鉁?|
| `system_results` | JSONField | 绯荤粺鍒嗘瀽缁撴灉 鉁?|
| `component_results` | JSONField | 閮ㄤ欢绾у埆缁撴灉 鉁?|
| `overall_health_score` | FloatField | 鎬讳綋鍋ュ悍鍒嗘暟 鉁?|
| `detected_faults` | JSONField | 妫€娴嬪埌鐨勬晠闅滃垪琛?鉁?|
| `critical_components` | JSONField | 鍏抽敭寮傚父閮ㄤ欢 鉁?|
| `analysis_details` | JSONField | 鍒嗘瀽璇︽儏 鉁?|
| `created_at` | DateTimeField | 鍒涘缓鏃堕棿 |

**璁块棶绀轰緥**锛?
```python
msfg_res = MSFGAnalysisResult.objects.filter(data_point=record).first()
component_health = msfg_res.component_results
overall_health = msfg_res.overall_health_score
test_results = msfg_res.test_results
fault_results = msfg_res.fault_results
```

---

## 鉁?淇鍚庣殑姝ｇ‘浠ｇ爜

### RuleDetectionResult璁块棶
```python
for rule_res in rule_res_list:
    triggered_rules.append({
        'rule_id': rule_res.rule_definition.rule_id,              # 鉁?姝ｇ‘
        'rule_expression': rule_res.rule_definition.rule_expression,
        'fault_name': rule_res.fault_definition.fault_name,       # 鉁?姝ｇ‘
        'fault_level': rule_res.fault_definition.fault_level,
        'component': rule_res.fault_definition.component,
        'is_triggered': rule_res.is_triggered,
        'confidence_score': float(rule_res.confidence_score),
        'detection_details': rule_res.detection_details
    })
```

---

## 馃攽 鍏抽敭瑕佺偣

### 鍛藉悕瑙勮寖宸紓
1. **IMSDetectionResult**锛氫娇鐢ㄩ€氱敤瀛楁鍚?
   - `is_anomaly`
   - `anomaly_score`
   - `parameter_scores`

2. **RuleDefinition**锛氫娇鐢ㄥ叿浣撳瓧娈靛悕
   - `rule_id`锛堜笉鏄痭ame锛?
   - `rule_expression`

3. **FaultDefinition**锛氫娇鐢ㄥ叿浣撳瓧娈靛悕
   - `fault_name`锛堜笉鏄痭ame锛?
   - `fault_level`

4. **MSFGAnalysisResult**锛氫娇鐢ㄥ鏁版垨鍏蜂綋瀛楁鍚?
   - `component_results`锛堜笉鏄痗omponent_health锛?
   - `test_results`
   - `fault_results`

---

## 鈿狅笍 甯歌闄烽槺

### 闄烽槺1锛氬亣璁炬墍鏈夋ā鍨嬮兘鏈塦name`瀛楁
```python
obj.name  # 鉂?涓嶆槸鎵€鏈夋ā鍨嬮兘鏈?
obj.rule_id  # 鉁?RuleDefinition
obj.fault_name  # 鉁?FaultDefinition
```

### 闄烽槺2锛氬亣璁惧瓧娈靛悕涓€鑷?
```python
obj.scores  # 鉂?IMSDetectionResult
obj.parameter_scores  # 鉁?姝ｇ‘

obj.triggered_rules  # 鉂?RuleDetectionResult锛堜笉瀛樺湪锛?
# 闇€瑕佹煡璇㈠涓猂uleDetectionResult骞舵瀯寤哄垪琛?
```

### 闄烽槺3锛氬拷鐣ュ叧绯荤被鍨?
```python
# OneToOne
ims_res = ims_results.filter(...).first()  # 鉁?鍙湁涓€涓?

# ForeignKey锛堜竴瀵瑰锛?
rule_res_list = rule_results.filter(...)  # 鉁?鍙兘鏈夊涓?
for rule_res in rule_res_list:
    ...
```

---

**鏂囨。鍒涘缓鏃堕棿**锛?025-10-10  
**鐢ㄩ€?*锛氬畬鏁村瓧娈靛弬鑰冿紝閬垮厤瀛楁鍚嶉敊璇?



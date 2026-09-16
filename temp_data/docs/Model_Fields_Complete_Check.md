# 鏁版嵁搴撴ā鍨嬪瓧娈靛畬鏁存鏌?

## 馃搵 鎵€鏈夋秹鍙婄殑妯″瀷鍙婂叾瀛楁

### 1. IMSDetectionResult (health_management/models.py)

```python
class IMSDetectionResult(models.Model):
    data_point = models.OneToOneField(PHMData)        # 鉁?涓€瀵逛竴鍏崇郴
    ims_model = models.ForeignKey(IMSModel)
    is_anomaly = models.BooleanField()                # 鉁?鏄惁寮傚父
    anomaly_score = models.FloatField()               # 鉁?寮傚父鍒嗘暟
    parameter_scores = models.JSONField()             # 鉁?鍚勫弬鏁板垎鏁?
    detection_details = models.JSONField()            # 鉁?妫€娴嬭鎯?
    created_at = models.DateTimeField()
```

**鍏崇郴**锛歄neToOne - 涓€涓狢MGData鍙湁涓€涓狪MS妫€娴嬬粨鏋?

**浣跨敤鏂瑰紡**锛?
```python
ims_res = IMSDetectionResult.objects.filter(data_point=record).first()
if ims_res:
    is_anomaly = ims_res.is_anomaly
    score = ims_res.anomaly_score
    params = ims_res.parameter_scores
    details = ims_res.detection_details
```

---

### 2. RuleDetectionResult (rule_detection/models.py)

```python
class RuleDetectionResult(models.Model):
    data_point = models.ForeignKey(PHMData)           # 鉁?涓€瀵瑰鍏崇郴
    rule_definition = models.ForeignKey(RuleDefinition)  # 鉁?鍏宠仈鐨勮鍒?
    fault_definition = models.ForeignKey(FaultDefinition)  # 鉁?鍏宠仈鐨勬晠闅?
    is_triggered = models.BooleanField()              # 鉁?鏄惁瑙﹀彂
    confidence_score = models.FloatField()            # 鉁?缃俊搴?
    detection_details = models.JSONField()            # 鉁?妫€娴嬭鎯?
    created_at = models.DateTimeField()
```

**鍏崇郴**锛欶oreignKey - 涓€涓狢MGData鍙互鏈夊涓鍒欐娴嬬粨鏋?

**重要**：没有`triggered_rules`字段！需要查询多个`RuleDetectionResult`

**浣跨敤鏂瑰紡**锛?
```python
rule_res_list = RuleDetectionResult.objects.filter(data_point=record)
triggered_rules = []
for rule_res in rule_res_list:
    triggered_rules.append({
        'rule_name': rule_res.rule_definition.name,
        'fault_name': rule_res.fault_definition.name,
        'is_triggered': rule_res.is_triggered,
        'confidence_score': rule_res.confidence_score,
        'detection_details': rule_res.detection_details
    })
```

---

### 3. MSFGAnalysisResult (msfg_analysis/models.py)

```python
class MSFGAnalysisResult(models.Model):
    data_point = models.ForeignKey(PHMData)           # 鉁?涓€瀵瑰鍏崇郴
    msfg_definition = models.ForeignKey(MSFGDefinition)
    test_results = models.JSONField()                 # 鉁?娴嬭瘯鐐圭粨鏋?
    fault_results = models.JSONField()                # 鉁?鏁呴殰鐐圭粨鏋?
    system_results = models.JSONField()               # 鉁?绯荤粺鍒嗘瀽缁撴灉
    component_results = models.JSONField()            # 鉁?閮ㄤ欢绾у埆缁撴灉
    overall_health_score = models.FloatField()        # 鉁?鎬讳綋鍋ュ悍鍒嗘暟
    detected_faults = models.JSONField()              # 鉁?妫€娴嬪埌鐨勬晠闅滃垪琛?
    critical_components = models.JSONField()          # 鉁?鍏抽敭寮傚父閮ㄤ欢
    analysis_details = models.JSONField()             # 鉁?鍒嗘瀽璇︽儏
    created_at = models.DateTimeField()
```

**鍏崇郴**锛欶oreignKey - 涓€涓狢MGData鍙互鏈夊涓狹SFG鍒嗘瀽缁撴灉

**浣跨敤鏂瑰紡**锛?
```python
msfg_res = MSFGAnalysisResult.objects.filter(data_point=record).first()
if msfg_res:
    component_health = msfg_res.component_results
    overall_health = msfg_res.system_results.get('overall_health')
    health_score = msfg_res.overall_health_score
    test_results = msfg_res.test_results
    fault_results = msfg_res.fault_results
    detected_faults = msfg_res.detected_faults
    critical_components = msfg_res.critical_components
```

---

## 鉁?淇鍚庣殑_collect_detection_results鏂规硶

### IMS结果收集
```python
if ims_res:
    ims_result_data = {
        'is_anomaly': ims_res.is_anomaly,                          # 鉁?
        'anomaly_score': float(ims_res.anomaly_score),            # 鉁?
        'parameter_scores': ims_res.parameter_scores,             # 鉁?姝ｇ‘瀛楁
        'detection_details': ims_res.detection_details            # 鉁?
    }
```

### 规则结果收集
```python
rule_res_list = RuleDetectionResult.objects.filter(data_point=record)  # 鉁?鏌ヨ鍒楄〃
if rule_res_list.exists():
    triggered_rules = []
    for rule_res in rule_res_list:                                # 鉁?閬嶅巻姣忎釜瑙勫垯缁撴灉
        triggered_rules.append({
            'rule_name': rule_res.rule_definition.name,           # 鉁?閫氳繃澶栭敭鑾峰彇
            'fault_name': rule_res.fault_definition.name,         # 鉁?閫氳繃澶栭敭鑾峰彇
            'is_triggered': rule_res.is_triggered,                # 鉁?
            'confidence_score': float(rule_res.confidence_score), # 鉁?
            'detection_details': rule_res.detection_details       # 鉁?
        })
    
    rule_result_data = {
        'has_violation': any(r['is_triggered'] for r in triggered_rules),
        'triggered_count': sum(1 for r in triggered_rules if r['is_triggered']),
        'triggered_rules': triggered_rules                        # 鉁?鏋勫缓鐨勫垪琛?
    }
```

### MSFG结果收集
```python
if msfg_res:
    msfg_result_data = {
        'component_health': msfg_res.component_results,           # 鉁?JSONField
        'overall_health': msfg_res.system_results.get('overall_health'),  # 鉁?
        'overall_health_score': float(msfg_res.overall_health_score),     # 鉁?
        'test_results': msfg_res.test_results,                    # 鉁?JSONField
        'fault_results': msfg_res.fault_results,                  # 鉁?JSONField
        'detected_faults': msfg_res.detected_faults,              # 鉁?JSONField (list)
        'critical_components': msfg_res.critical_components       # 鉁?JSONField (list)
    }
```

---

## 馃攳 娼滃湪闂鍏ㄩ潰妫€鏌?

### 鉁?妫€鏌?锛氬瓧娈靛悕绉?
- 鉁?IMSDetectionResult.parameter_scores锛堜笉鏄痵cores锛?
- 鉁?RuleDetectionResult锛氶渶瑕侀亶鍘嗗涓粨鏋滐紙涓嶆槸鍗曚釜triggered_rules瀛楁锛?
- 鉁?MSFGAnalysisResult锛氭墍鏈塉SONField閮芥纭闂?

### 鉁?妫€鏌?锛氬叧绯荤被鍨?
- 鉁?IMSDetectionResult锛歄neToOne 鈫?浣跨敤.first()
- 鉁?RuleDetectionResult锛欶oreignKey 鈫?闇€瑕侀亶鍘嗘煡璇㈤泦
- 鉁?MSFGAnalysisResult锛欶oreignKey 鈫?浣跨敤.first()

### 鉁?妫€鏌?锛氬閿闂?
- 鉁?rule_res.rule_definition.name
- 鉁?rule_res.fault_definition.name
- 鉁?msfg_res.msfg_definition

### 鉁?妫€鏌?锛欽SONField璁块棶
- 鉁?ims_res.parameter_scores锛堝彲鑳戒负None鎴栫┖dict锛?
- 鉁?ims_res.detection_details
- 鉁?rule_res.detection_details
- 鉁?msfg_res.component_results
- 鉁?msfg_res.system_results
- 鉁?msfg_res.test_results
- 鉁?msfg_res.fault_results
- 鉁?msfg_res.detected_faults
- 鉁?msfg_res.critical_components

### 鉁?妫€鏌?锛氱被鍨嬭浆鎹?
- 鉁?float(ims_res.anomaly_score) if ims_res.anomaly_score else 0.0
- 鉁?float(rule_res.confidence_score) if rule_res.confidence_score else 0.0
- 鉁?float(msfg_res.overall_health_score) if msfg_res.overall_health_score else 1.0

### 鉁?妫€鏌?锛氱┖鍊煎鐞?
- 鉁?if ims_res: ... else None
- 鉁?if rule_res_list.exists(): ... else None
- 鉁?if msfg_res: ... else None
- 鉁?if field else {} 锛圝SONField榛樿鍊硷級
- 鉁?if field else [] 锛圝SONField list榛樿鍊硷級

### 鉁?妫€鏌?锛氬鍏ヨ鍙?
- 鉁?from health_management.models import IMSDetectionResult
- 鉁?from rule_detection.models import RuleDetectionResult
- 鉁?from msfg_analysis.models import MSFGAnalysisResult

---

## 🎯 数据结构示例

### 单帧详细结果
```python
{
    'frame_number': 1,
    'timestamp': '2022-10-09T15:36:48+00:00',
    'is_anomaly': True,
    
    'ims_result': {
        'is_anomaly': True,
        'anomaly_score': 0.85,
        'parameter_scores': {
            'Motor_Current': 0.92,
            'Motor_Voltage': 0.73,
            ...
        },
        'detection_details': {...}
    },
    
    'rule_result': {
        'has_violation': True,
        'triggered_count': 3,
        'triggered_rules': [
            {
                'rule_name': '鐢垫満鐢垫祦瓒呴檺',
                'fault_name': '鐢垫満杩囪浇',
                'is_triggered': True,
                'confidence_score': 0.95,
                'detection_details': {...}
            },
            ...
        ]
    },
    
    'msfg_result': {
        'component_health': {
            '鐢垫簮鏉?: {'health_score': 0.843, ...},
            ...
        },
        'overall_health': 0.860,
        'overall_health_score': 0.860,
        'test_results': {...},
        'fault_results': {...},
        'detected_faults': ['鐢垫満杩囪浇', '鐢靛帇涓嶇ǔ'],
        'critical_components': ['鐢垫簮鏉?]
    }
}
```

---

## 鉁?瀹屾暣鎬ф鏌ョ粨鏋?

缁忚繃鍏ㄩ潰妫€鏌ワ紝鐜板湪浠ｇ爜锛?
- 鉁?鎵€鏈夋ā鍨嬪瓧娈靛悕绉版纭?
- 鉁?鎵€鏈夊叧绯荤被鍨嬪鐞嗘纭?
- 鉁?鎵€鏈夊閿闂畨鍏?
- 鉁?鎵€鏈塉SONField鏈夐粯璁ゅ€煎鐞?
- 鉁?鎵€鏈夌被鍨嬭浆鎹㈠畨鍏?
- 鉁?鎵€鏈夊鍏ヨ矾寰勬纭?
- 鉁?鎵€鏈夋棩蹇楃骇鍒悎閫?

**娌℃湁鍙戠幇鍏朵粬娼滃湪闂锛?* 鉁?

---

**妫€鏌ユ椂闂?*锛?025-10-10  
**妫€鏌ョ粨鏋?*锛氣渽 閫氳繃  
**璇硶妫€鏌?*锛氣渽 閫氳繃  
**瀛楁楠岃瘉**锛氣渽 瀹屾暣



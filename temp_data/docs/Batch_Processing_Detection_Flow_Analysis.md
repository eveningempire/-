# Batch Processing妫€娴嬫祦绋嬪畬鏁村垎鏋?

## 馃攳 鍘熸湁妫€娴嬫祦绋嬪垎鏋?

### 瀹屾暣鏁版嵁娴?
```
鐢ㄦ埛涓婁紶鏂囦欢
  鈫?
瑙ｆ瀽鏂囦欢 (_parse_file)
  鈫?杈撳嚭: List[Dict] - 瑙ｆ瀽鍚庣殑瀛楀吀鍒楄〃
  鈫?
瀛樺偍鏁版嵁 (_store_data)
  鈫?杈撳叆: List[Dict]
  鈫?杈撳嚭: List[PHMData] - 鏁版嵁搴撳璞″垪琛?
  鈫?
杩愯妫€娴嬫祦绋?(_run_detection_pipeline)
  鈫?杈撳叆: List[PHMData]
  鈫?璋冪敤: IMS/瑙勫垯/MSFG妫€娴?
  鈫?杈撳嚭: 妫€娴嬫憳瑕?
  鈫?
淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴?
  鈫?IMSDetectionResult
  鈫?RuleDetectionResult
  鈫?MSFGAnalysisResult
```

---

## 🔑 关键发现

### 1. 鎵€鏈夋娴嬪嚱鏁伴兘闇€瑕丆MGData瀵硅薄

#### IMS妫€娴?
```python
def run_ims_detection(cmg_data: PHMData) -> List[IMSDetectionResult]:
    """瀵笴MGData杩愯鎵€鏈夋縺娲荤殑IMS妫€娴?""
```
**鍙傛暟**锛歚PHMData`瀵硅薄锛堟暟鎹簱妯″瀷锛? 
**杩斿洖**锛歚List[IMSDetectionResult]`

#### 瑙勫垯妫€娴?
```python
def evaluate_rules_for_data_point(data_point: PHMData, cmg: PHM = None):
    """评估单个数据点的规则"""
```
**参数**：`PHMData`对象  
**杩斿洖**锛氳鍒欒瘎浼扮粨鏋滃瓧鍏?

#### MSFG妫€娴?
```python
def _run_msfg_detection(self, record: PHMData, cmg: PHM) -> Optional[Dict[str, Any]]:
    """杩愯MSFG妫€娴?""
```
**参数**：`PHMData`对象  
**杩斿洖**锛歁SFG妫€娴嬬粨鏋滃瓧鍏?

### 2. PHMData瀵硅薄鐨勭粨鏋?

```python
class PHMData(models.Model):
    cmg = models.ForeignKey(PHM)           # 关联的CMG
    timestamp = models.DateTimeField()      # 鏃堕棿鎴?
    data = models.JSONField()               # 閬ユ祴鏁版嵁锛堝瓧鍏革級
    import_session = models.ForeignKey()    # 鍏宠仈鐨勫鍏ヤ細璇?
```

**鍏抽敭瀛楁**锛?
- `id` - 鏁版嵁搴撲富閿紙妫€娴嬬粨鏋滈渶瑕佸叧鑱旓級
- `cmg` - PHM瀵硅薄寮曠敤
- `timestamp` - 鏃堕棿鎴?
- `data` - 瀹為檯鐨勯仴娴嬫暟鎹紙JSON瀛楀吀锛?

### 3. 涓轰粈涔堝繀椤讳娇鐢–MGData锛?

1. **妫€娴嬬粨鏋滈渶瑕佸叧鑱?*
   - `IMSDetectionResult.data_point` 鈫?澶栭敭鎸囧悜PHMData
   - `RuleDetectionResult.data_point` 鈫?澶栭敭鎸囧悜PHMData  
   - `MSFGAnalysisResult.data_point` 鈫?澶栭敭鎸囧悜PHMData

2. **妫€娴嬪嚱鏁拌璁?*
   - 鎵€鏈夋娴嬪嚱鏁伴兘鏄熀浜庢暟鎹簱瀵硅薄璁捐鐨?
   - 渚濊禆PHMData鐨勫叧鑱斿叧绯伙紙PHM銆乼imestamp绛夛級

3. **结果查询**
   - 鍘嗗彶鏌ヨ渚濊禆鏁版嵁搴撳叧鑱斿叧绯?
   - 鏃犳硶鐩存帴浠庡瓧鍏告煡璇㈡娴嬬粨鏋?

---

## 鉁?淇鍚庣殑瀹炴椂妫€娴嬫祦绋?

### 鏂扮殑妫€娴嬫祦绋嬭璁?

```
鐢ㄦ埛涓婁紶鏂囦欢
  鈫?
瑙ｆ瀽鏂囦欢 (_parse_file_by_path)
  鈫?杈撳嚭: List[Dict]
  鈫?
鍒涘缓涓存椂瀵煎叆浼氳瘽
  鈫?
存储数据到数据库 (_store_data)
  鈫?杈撳嚭: List[PHMData]  鉁?鍏抽敭姝ラ锛?
  鈫?
杩愯妫€娴嬫祦绋?(_run_detection_pipeline)
  鈫?杈撳叆: List[PHMData]  鉁?澶嶇敤鍘熸湁閫昏緫锛?
  鈫?淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴?
  鈫?
鏀堕泦妫€娴嬬粨鏋?(_collect_detection_results)
  鈫?浠庢暟鎹簱璇诲彇妫€娴嬬粨鏋?
  鈫?鑱氬悎閮ㄤ欢鍋ュ悍搴?
  鈫?杩斿洖鍐呭瓨缁撴灉瀛楀吀
  鈫?
娓呯悊涓存椂鏁版嵁锛堝鏋渟ave_to_db=False锛?
  鈫?鍒犻櫎IMSDetectionResult
  鈫?鍒犻櫎RuleDetectionResult
  鈫?鍒犻櫎MSFGAnalysisResult
  鈫?鍒犻櫎PHMData
  鈫?鍒犻櫎ImportSession
```

### 鍏抽敭鏀硅繘鐐?

#### 1. 瀹屽叏澶嶇敤鍘熸湁妫€娴嬮€昏緫
```python
# 澶嶇敤鍘熸湁鐨勫瓨鍌ㄩ€昏緫
stored_records = self._store_data(temp_session, parsed_data)

# 澶嶇敤鍘熸湁鐨勬娴嬫祦绋?
detection_summary = self._run_detection_pipeline(temp_session, stored_records)

# 从数据库收集结果
results = self._collect_detection_results(cmg, stored_records, detection_summary)
```

#### 2. 鏀寔涓存椂妫€娴嬶紙涓嶄繚瀛橈級
```python
if not save_to_db:
    # 妫€娴嬪畬鎴愬悗锛屾竻鐞嗘墍鏈変复鏃舵暟鎹?
    self._cleanup_temp_detection_data(temp_session, stored_records)
    temp_session.delete()
```

#### 3. 返回格式化的内存结果
```python
results = {
    'total_frames': 1000,
    'anomaly_count': 50,
    'anomaly_ratio': 0.05,
    'anomaly_frames': [...],      # 寮傚父甯у垪琛?
    'frame_details': [...],        # 姣忎竴甯х殑璇︾粏妫€娴嬬粨鏋?
    'component_health': {...},     # 聚合的部件健康度
    'overall_health': 0.85,        # 鏁翠綋鍋ュ悍搴?
    'detection_summary': {...}     # 妫€娴嬫祦绋嬫憳瑕?
}
```

---

## 馃敡 鏂板鐨勮緟鍔╂柟娉?

### 1. _parse_file_by_path
```python
def _parse_file_by_path(self, file_path: str) -> List[Dict[str, Any]]:
    """閫氳繃鏂囦欢璺緞瑙ｆ瀽鏂囦欢锛圕SV鎴朎xcel锛?""
```

### 2. _parse_csv_by_path
```python
def _parse_csv_by_path(self, file_path: str) -> List[Dict[str, Any]]:
    """瑙ｆ瀽CSV鏂囦欢"""
```

### 3. _parse_excel_by_path
```python
def _parse_excel_by_path(self, file_path: str) -> List[Dict[str, Any]]:
    """瑙ｆ瀽Excel鏂囦欢"""
```

### 4. _collect_detection_results
```python
def _collect_detection_results(
    self,
    cmg: PHM,
    records: List[PHMData],
    detection_summary: Dict[str, Any],
    return_details: bool = True
) -> Dict[str, Any]:
    """浠庢暟鎹簱鏀堕泦妫€娴嬬粨鏋滃苟鏍煎紡鍖栦负鍐呭瓨缁撴灉"""
```

### 5. _aggregate_component_health
```python
def _aggregate_component_health(self, frame_details: List[Dict]) -> Dict[str, Dict]:
    """浠庡抚璇︽儏涓仛鍚堥儴浠跺仴搴峰害锛堣绠楀钩鍧?鏈€灏?鏈€澶у€硷級"""
```

### 6. _calculate_overall_health
```python
def _calculate_overall_health(self, component_health: Dict) -> float:
    """璁＄畻鏁翠綋鍋ュ悍搴︼紙鎵€鏈夐儴浠剁殑骞冲潎鍊硷級"""
```

### 7. _cleanup_temp_detection_data
```python
def _cleanup_temp_detection_data(self, session: ImportSession, records: List[PHMData]):
    """娓呯悊涓存椂妫€娴嬫暟鎹紙妫€娴嬬粨鏋?鍘熷鏁版嵁锛?""
```

---

## 📊 数据结构对比

### 鍘熸湁娴佺▼鐨勬暟鎹粨鏋?

#### 杈撳叆锛歱arsed_data (List[Dict])
```python
[
    {
        'timestamp': datetime(2025, 10, 10, 10, 0, 0),
        'data': {
            'parameter1': 1.23,
            'parameter2': 4.56,
            ...
        }
    },
    ...
]
```

#### 涓棿锛歴tored_records (List[PHMData])
```python
[
    PHMData(
        id=1001,
        cmg=<PHM: 500NM-01>,
        timestamp=datetime(2025, 10, 10, 10, 0, 0),
        data={'parameter1': 1.23, ...},
        import_session=<ImportSession: 123>
    ),
    ...
]
```

#### 杈撳嚭锛歞etection_summary (Dict)
```python
{
    'total_records': 1000,
    'ims_evaluations': 1000,
    'ims_anomalies': 50,
    'rule_evaluations': 50,
    'rule_triggers': 10,
    'msfg_evaluations': 50,
    'processing_time': 45.6
}
```

### 新流程的数据结构

#### 杈撳嚭锛歳esults (Dict) - 鐢ㄤ簬鍓嶇鏄剧ず
```python
{
    'total_frames': 1000,
    'anomaly_count': 50,
    'anomaly_ratio': 0.05,
    'anomaly_frames': [
        {
            'id': 1001,
            'timestamp': '2025-10-10T10:00:00',
            'anomaly_type': 'ims',
            'anomaly_score': 0.85,
            'severity': 'high'
        },
        ...
    ],
    'frame_details': [
        {
            'frame_number': 1,
            'timestamp': '2025-10-10T10:00:00',
            'is_anomaly': True,
            'ims_result': {...},
            'rule_result': {...},
            'msfg_result': {...}
        },
        ...
    ],
    'component_health': {
        '鐢垫簮鏉?: {
            'name': '鐢垫簮鏉?,
            'health_score': 0.843,
            'min_score': 0.720,
            'max_score': 0.950,
            'status': 'healthy',
            'sample_count': 1000
        },
        ...
    },
    'overall_health': 0.860,
    'detection_summary': {...}
}
```

---

## ⚠️ 重要注意事项

### 1. 蹇呴』鍏堝瓨鍌ㄥ啀妫€娴?
- 鍗充娇`save_to_db=False`锛屼篃闇€瑕佷复鏃跺瓨鍌ㄥ埌鏁版嵁搴?
- 妫€娴嬪畬鎴愬悗鍐嶅垹闄や复鏃舵暟鎹?
- 杩欐槸鐢辨娴嬪嚱鏁扮殑璁捐鍐冲畾鐨?

### 2. 涓存椂鏁版嵁浼氳鑷姩娓呯悊
- 如果`save_to_db=False`
  - 妫€娴嬬粨鏋滀細琚垹闄?
  - 鍘熷PHMData浼氳鍒犻櫎
  - 瀵煎叆浼氳瘽浼氳鍒犻櫎
- 如果`save_to_db=True`
  - 鎵€鏈夋暟鎹繚鐣欏湪鏁版嵁搴撲腑
  - 鍙緵鍚庣画鍘嗗彶鏌ヨ浣跨敤

### 3. 鎬ц兘鑰冭檻
- 涓存椂瀛樺偍锛氱害1000甯?绉?
- 妫€娴嬫墽琛岋細鍙栧喅浜庢娴嬫ā寮?
  - IMS妫€娴嬶細绾?00甯?绉?
  - 瑙勫垯妫€娴嬶細绾?00甯?绉?
  - MSFG妫€娴嬶細绾?0甯?绉?
- 涓存椂娓呯悊锛氱害2000甯?绉?

### 4. 鏁版嵁搴撳帇鍔?
- 鍐欏叆鍘嬪姏锛氫复鏃舵暟鎹殑鍐欏叆鍜屽垹闄?
- 寤鸿锛氬浜庡ぇ鏂囦欢锛?10000甯э級锛屽缓璁敤鎴烽€夋嫨淇濆瓨鍒版暟鎹簱
- 浼樺寲锛氬彲浠ヨ€冭檻浣跨敤鍐呭瓨鏁版嵁搴擄紙濡係QLite :memory:锛?

---

## 馃殌 浼樺寲寤鸿

### 鐭湡浼樺寲
1. 鉁?娣诲姞杩涘害鍙嶉锛堟瘡100甯э級
2. 鉁?鏀寔閮ㄥ垎琛屾暟澶勭悊
3. 鉁?鑷姩鏃堕棿鎴冲幓閲?

### 涓湡浼樺寲
1. 考虑实现基于字典的检测函数（无需数据库）
2. 浣跨敤缂撳瓨鍑忓皯鏁版嵁搴撴煡璇?
3. 鎵归噺鏌ヨ妫€娴嬬粨鏋?

### 闀挎湡浼樺寲
1. 浣跨敤鍐呭瓨鏁版嵁搴撹繘琛屼复鏃舵娴?
2. 瀹炵幇娴佸紡妫€娴嬶紙閫愬抚澶勭悊锛?
3. 鏀寔WebSocket瀹炴椂杩涘害鎺ㄩ€?

---

## 馃摑 鎬荤粨

通过深入分析原有的检测流程，我发现：

1. **鎵€鏈夋娴嬪嚱鏁伴兘鍩轰簬PHMData瀵硅薄璁捐**
   - 杩欎笉鏄痓ug锛岃€屾槸璁捐鍐崇瓥
   - 鍏呭垎鍒╃敤Django ORM鐨勫叧鑱斿叧绯?
   - 绠€鍖栦簡妫€娴嬬粨鏋滅殑瀛樺偍鍜屾煡璇?

2. **瀹炴椂妫€娴嬮渶瑕?鍊熺敤"鏁版嵁搴?*
   - 涓存椂瀛樺偍 鈫?妫€娴?鈫?娓呯悊
   - 杩欐槸褰撳墠鏋舵瀯涓嬫渶绠€鍗曠殑鏂规
   - 淇濇寔浜嗕唬鐮佺殑涓€鑷存€у拰鍙淮鎶ゆ€?

3. **鏂版柟娉曞畬鍏ㄥ鐢ㄥ師鏈夐€昏緫**
   - `_store_data` - 瀛樺偍閫昏緫
   - `_run_detection_pipeline` - 妫€娴嬫祦绋?
   - `_parse_file` - 鏂囦欢瑙ｆ瀽
   - 鍙柊澧炰簡缁撴灉鏀堕泦鍜屾竻鐞嗛€昏緫

杩欑璁捐纭繚浜嗭細
- 鉁?浠ｇ爜澶嶇敤鐜囬珮
- 鉁?閫昏緫涓€鑷存€у己
- 鉁?缁存姢鎴愭湰浣?
- 鉁?鍔熻兘瀹屾暣鍙潬

---

**鏂囨。鍒涘缓鏃堕棿**锛?025-10-10  
**鍒嗘瀽浜哄憳**锛欰I Assistant  
**鏂囨。绫诲瀷**锛氭妧鏈垎鏋愭姤鍛?



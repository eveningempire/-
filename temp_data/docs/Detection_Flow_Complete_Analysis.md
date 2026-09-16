# Batch Processing瀹屾暣妫€娴嬫祦绋嬪鐓у垎鏋?

## 馃搳 鍘熸湁娴佺▼ vs 瀹炴椂妫€娴嬫祦绋?

### 鍘熸湁娴佺▼锛堟枃浠跺鍏?妫€娴嬶級

```
鐢ㄦ埛涓婁紶鏂囦欢鍒板墠绔?
  鈫?
鍓嶇璋冪敤 /api/v1/data/import-sessions/ (POST)
  鈫?
鍒涘缓ImportSession锛坒ile瀛楁淇濆瓨鍒癿edia鐩綍锛?
  session.file = FileField锛圖jango鎵樼锛?
  鈫?
寮傛澶勭悊锛歱rocess_import_session_async(session_id)
  鈫?
_process_import_session(session_id)
  鈹溾攢 _parse_file(session)
  鈹?  鈹斺攢 file_path = session.file.path  鉁?Django FileField
  鈹?  鈹斺攢 瑙ｆ瀽CSV/Excel 鈫?List[Dict{'timestamp', 'data'}]
  鈹溾攢 _store_data(session, parsed_data)
  鈹?  鈹斺攢 鎵归噺鍒涘缓PHMData瀵硅薄
  鈹?  鈹斺攢 杩斿洖 List[PHMData]
  鈹斺攢 _run_detection_pipeline(session, records)
      鈹溾攢 IMS妫€娴嬶紙闇€瑕丆MGData瀵硅薄锛?
      鈹溾攢 瑙勫垯妫€娴嬶紙闇€瑕丆MGData瀵硅薄锛?
      鈹斺攢 MSFG妫€娴嬶紙闇€瑕丆MGData瀵硅薄锛?
  鈫?
淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴?
  鈹溾攢 IMSDetectionResult
  鈹溾攢 RuleDetectionResult
  鈹斺攢 MSFGAnalysisResult
```

---

### 瀹炴椂妫€娴嬫祦绋嬶紙鏂拌璁★級

```
鐢ㄦ埛涓婁紶鏂囦欢鍒板墠绔?
  鈫?
鍓嶇璋冪敤 /api/v1/data/realtime-detection/ (POST)
  鈫?
淇濆瓨鍒扮郴缁熶复鏃剁洰褰?
  tmp_file = tempfile.NamedTemporaryFile()
  file_path = 'C:\Users\...\Temp\tmpXXX.xlsx'  鈿狅笍 涓嶅湪media鐩綍
  鈫?
process_file_for_detection(file_path, cmg, ...)
  鈹溾攢 _parse_file_direct(file_path)  鉁?鐩存帴瑙ｆ瀽锛屼笉渚濊禆FileField
  鈹?  鈹斺攢 瑙ｆ瀽CSV/Excel 鈫?List[Dict{'timestamp', 'data'}]
  鈹溾攢 鍒涘缓涓存椂ImportSession锛堟棤file瀛楁锛?
  鈹溾攢 _create_cmg_data_batch(cmg, parsed_data, session)
  鈹?  鈹斺攢 鎵归噺鍒涘缓PHMData瀵硅薄
  鈹?  鈹斺攢 杩斿洖 List[PHMData]
  鈹斺攢 _run_detection_pipeline(session, records)  鉁?瀹屽叏澶嶇敤
      鈹溾攢 IMS妫€娴?
      鈹溾攢 瑙勫垯妫€娴?
      鈹斺攢 MSFG妫€娴?
  鈫?
_collect_detection_results(cmg, records, ...)
  鈹斺攢 浠庢暟鎹簱璇诲彇妫€娴嬬粨鏋?
  鈹斺攢 鑱氬悎閮ㄤ欢鍋ュ悍搴?
  └─ 返回内存结果
  鈫?
_cleanup_temp_detection_data(session, records)  ⚠️ 如果save_to_db=False
  鈹溾攢 鍒犻櫎鎵€鏈夋娴嬬粨鏋?
  鈹溾攢 鍒犻櫎鎵€鏈塁MGData
  鈹斺攢 鍒犻櫎ImportSession
  鈫?
杩斿洖缁撴灉鍒板墠绔紙JSON锛?
```

---

## 馃攽 鍏抽敭宸紓涓庤В鍐虫柟妗?

### 宸紓1锛氭枃浠惰矾寰勯棶棰?

**鍘熸湁娴佺▼**锛?
```python
session.file = FileField  # Django鎵樼锛屼繚瀛樺湪media/imports/鐩綍
file_path = session.file.path  # 瀹夊叏璺緞锛屽湪MEDIA_ROOT涓?
```

**瀹炴椂妫€娴?*锛?
```python
file_path = 'C:\Users\...\Temp\tmpXXX.xlsx'  # 系统临时目录
session.file.path  # 鉂?鎶ラ敊锛氳矾寰勫湪media鐩綍澶?
```

**瑙ｅ喅鏂规**锛?
```python
# 创建新方法：_parse_file_direct(file_path)
# 涓嶄緷璧杝ession.file锛岀洿鎺ヨ鍙栨枃浠惰矾寰?
def _parse_file_direct(self, file_path: str, max_rows=None):
    # 鐩存帴鎵撳紑鏂囦欢锛屼笉閫氳繃Django FileField
    with open(file_path, 'r') as f:
        # ... 瑙ｆ瀽閫昏緫
```

---

### 宸紓2锛欼mportSession鐨勪綔鐢?

**鍘熸湁娴佺▼**锛?
- 瀛樺偍涓婁紶鐨勬枃浠讹紙FileField锛?
- 璺熻釜澶勭悊杩涘害
- 关联创建的CMGData记录

**瀹炴椂妫€娴?*锛?
- 鉂?涓嶉渶瑕佸瓨鍌ㄦ枃浠讹紙宸插湪涓存椂鐩綍锛?
- 鉁?闇€瑕佹爣璇嗚繖鎵规暟鎹紙import_session澶栭敭锛?
- 鉁?闇€瑕佽窡韪娴嬬姸鎬?

**瑙ｅ喅鏂规**锛?
```python
# 鍒涘缓鏈€灏忓寲鐨処mportSession锛堜笉璁剧疆file瀛楁锛?
temp_session = ImportSession.objects.create(
    cmg=cmg,
    method=ImportSession.Method.FILE,
    import_mode=ImportSession.ImportMode.IMPORT_AND_DETECT,
    # file=None  # 涓嶈缃甪ile瀛楁
)
```

---

### 宸紓3锛氭暟鎹垱寤烘祦绋?

**鍘熸湁娴佺▼**锛?
```python
_store_data(session, parsed_data)
  鈫?浣跨敤session.id鏍囪瘑
  鈫?鎵归噺鍒涘缓PHMData
  鈫?鏇存柊session杩涘害
  鈫?杩斿洖List[PHMData]
```

**瀹炴椂妫€娴?*锛?
```python
_create_cmg_data_batch(cmg, parsed_data, session)
  鈫?绠€鍖栫増鐨刜store_data
  鈫?涓嶆洿鏂拌繘搴︼紙鍚屾澶勭悊锛?
  鈫?杩斿洖List[PHMData]
```

---

## 馃洜锔?瀹屾暣鐨勫疄鏃舵娴嬪疄鐜?

### 鏂板鐨?涓牳蹇冩柟娉?

#### 1. process_file_for_detection锛堜富娴佺▼锛?
```python
def process_file_for_detection(file_path, cmg, save_to_db=False):
    """
    瀹屾暣鐨勫疄鏃舵娴嬫祦绋?
    """
    # 姝ラ1锛氳В鏋愭枃浠讹紙涓嶄緷璧朏ileField锛?
    parsed_data = self._parse_file_direct(file_path)
    
    # 姝ラ2锛氬垱寤轰复鏃朵細璇?
    temp_session = ImportSession.objects.create(cmg=cmg, ...)
    
    # 姝ラ3锛氬垱寤篊MGData瀵硅薄
    stored_records = self._create_cmg_data_batch(cmg, parsed_data, temp_session)
    
    # 姝ラ4锛氳繍琛屾娴嬶紙瀹屽叏澶嶇敤锛?
    detection_summary = self._run_detection_pipeline(temp_session, stored_records)
    
    # 姝ラ5锛氭敹闆嗙粨鏋?
    results = self._collect_detection_results(cmg, stored_records, ...)
    
    # 姝ラ6锛氭竻鐞嗭紙濡傛灉涓嶄繚瀛橈級
    if not save_to_db:
        self._cleanup_temp_detection_data(temp_session, stored_records)
        temp_session.delete()
    
    return results
```

#### 2. _parse_file_direct（文件解析）
```python
def _parse_file_direct(file_path, max_rows=None):
    """
    鐩存帴瑙ｆ瀽鏂囦欢锛屼笉渚濊禆Django FileField
    
    澶嶅埗鍘熸湁_parse_file鐨勬牳蹇冮€昏緫锛?
    - 鏃堕棿鎴宠В鏋愶紙parse_ts锛?
    - CSV/Excel鏍煎紡鏀寔
    - 鏁版嵁绫诲瀷杞崲
    """
    # 内嵌parse_ts函数
    def parse_ts(value):
        # 鏀寔澶氱鏃堕棿鏍煎紡
        # ISO, Unix timestamp, 甯歌鏍煎紡绛?
        ...
    
    # 鏍规嵁鏂囦欢鎵╁睍鍚嶈В鏋?
    if suffix == ".csv":
        # CSV瑙ｆ瀽閫昏緫
        ...
    elif suffix in {".xlsx", ".xls"}:
        # Excel瑙ｆ瀽閫昏緫
        ...
    
    return parsed_data  # List[Dict{'timestamp', 'data'}]
```

#### 3. _create_cmg_data_batch（数据创建）
```python
def _create_cmg_data_batch(cmg, parsed_data, session):
    """
    鎵归噺鍒涘缓PHMData瀵硅薄
    
    绠€鍖栫増鐨刜store_data锛?
    - 鍒嗘壒鍒涘缓锛堥伩鍏嶅唴瀛樻孩鍑猴級
    - 事务保护
    - 杩斿洖鍒涘缓鐨勫璞″垪琛?
    """
    # 鍒嗘壒鍒涘缓
    for batch in batches:
        PHMData.objects.bulk_create(batch_to_create)
    
    # 鏌ヨ杩斿洖
    created_records = PHMData.objects.filter(
        cmg=cmg, 
        import_session=session
    )
    
    return list(created_records)
```

---

## 📋 数据结构完整对照

### 闃舵1锛氭枃浠惰В鏋愬悗
```python
parsed_data = [
    {
        'timestamp': datetime(2025, 10, 10, 10, 0, 0, tzinfo=UTC),
        'data': {
            'Motor_Current': 1.23,
            'Motor_Voltage': 24.5,
            'Temperature': 35.2,
            ...  # 鎵€鏈夐仴娴嬪弬鏁?
        }
    },
    ...  # 109,511 鏉¤褰?
]
```

### 闃舵2锛氬垱寤篊MGData鍚?
```python
stored_records = [
    PHMData(
        id=1001,  # 鏁版嵁搴撲富閿?
        cmg=<PHM: 500-02>,
        timestamp=datetime(2025, 10, 10, 10, 0, 0),
        data={'Motor_Current': 1.23, ...},
        import_session=<ImportSession: 涓存椂浼氳瘽>
    ),
    ...
]
```

### 闃舵3锛氭娴嬫墽琛屽悗锛堟暟鎹簱锛?
```python
# IMS妫€娴嬬粨鏋?
IMSDetectionResult(
    data_point=<PHMData: 1001>,  # 澶栭敭鍏宠仈
    ims_model=<IMSModel: IMS_500NM>,
    is_anomaly=True,
    anomaly_score=0.85,
    scores={'Motor_Current': 0.92, ...}
)

# 瑙勫垯妫€娴嬬粨鏋?
RuleDetectionResult(
    data_point=<PHMData: 1001>,
    triggered_rules=[...],
    ...
)

# MSFG妫€娴嬬粨鏋?
MSFGAnalysisResult(
    data_point=<PHMData: 1001>,
    component_results={'鐢垫簮鏉?: {'health_score': 0.843, ...}, ...},
    system_results={'overall_health': 0.860, ...}
)
```

### 阶段4：收集结果后（内存）
```python
results = {
    'total_frames': 109511,
    'anomaly_count': 5234,
    'anomaly_ratio': 0.0478,
    'anomaly_frames': [
        {
            'id': 1001,
            'timestamp': '2025-10-10T10:00:00+00:00',
            'anomaly_type': 'ims',
            'anomaly_score': 0.85,
            'severity': 'high'
        },
        ...
    ],
    'frame_details': [
        {
            'frame_number': 1,
            'timestamp': '2025-10-10T10:00:00+00:00',
            'is_anomaly': True,
            'ims_result': {...},
            'rule_result': {...},
            'msfg_result': {...}
        },
        ...
    ],
    'component_health': {
        '鐢垫簮鏉?: {
            'health_score': 0.843,
            'min_score': 0.720,
            'max_score': 0.950,
            'status': 'healthy',
            'sample_count': 109511
        },
        ...
    },
    'overall_health': 0.860
}
```

---

## 鉁?鍏抽敭淇鐐?

### 淇1锛氭枃浠惰矾寰勮闂?
```python
# 閿欒鏂瑰紡
file_path = session.file.path  # 鉂?闇€瑕丗ileField

# 姝ｇ‘鏂瑰紡
parsed_data = self._parse_file_direct(file_path)  # 鉁?鐩存帴璇诲彇
```

### 修复2：ImportSession创建
```python
# 閿欒鏂瑰紡
ImportSession.objects.create(
    file=file_path,  # 鉂?瀛楃涓蹭笉鑳借祴鍊肩粰FileField
)

# 姝ｇ‘鏂瑰紡
ImportSession.objects.create(
    # 涓嶈缃甪ile瀛楁
    method=ImportSession.Method.FILE,
    import_mode=ImportSession.ImportMode.IMPORT_AND_DETECT,
)
```

### 淇3锛氭暟鎹垱寤?
```python
# 澶嶇敤閫昏緫锛屼絾涓嶆洿鏂皊ession.file
stored_records = self._create_cmg_data_batch(cmg, parsed_data, temp_session)
```

---

## 馃幆 瀹屾暣鐨勬柟娉曟竻鍗?

### 鏂板鏂规硶锛?涓級
1. **`process_file_for_detection`** - 涓绘祦绋嬪叆鍙?
2. **`_parse_file_direct`** - 鐩存帴瑙ｆ瀽鏂囦欢锛堜笉渚濊禆FileField锛?
3. **`_create_cmg_data_batch`** - 鎵归噺鍒涘缓PHMData

### 澶嶇敤鏂规硶锛?涓級
1. **`_run_detection_pipeline`** - 妫€娴嬫祦绋嬶紙瀹屽叏澶嶇敤锛?
2. **`_collect_detection_results`** - 收集结果（新增）
3. **`_aggregate_component_health`** - 鑱氬悎鍋ュ悍搴︼紙鏂板锛?
4. **`_calculate_overall_health`** - 璁＄畻鏁翠綋鍋ュ悍搴︼紙鏂板锛?
5. **`_cleanup_temp_detection_data`** - 清理临时数据（新增）

### 渚濊禆鐨勫師鏈夋柟娉?
- `_run_detection_pipeline` 鈫?瀹屾暣鐨勬娴嬫祦绋?
  - `_preload_detection_models` 鈫?棰勫姞杞芥ā鍨?
  - `_run_batch_ims_detection_optimized` 鈫?鎵归噺IMS妫€娴?
  - `_run_batch_rule_detection_optimized` 鈫?鎵归噺瑙勫垯妫€娴?
  - `_run_batch_msfg_detection_optimized` 鈫?鎵归噺MSFG妫€娴?
  - `_run_msfg_detection` 鈫?鍗曟潯MSFG妫€娴?

---

## 馃摑 鏁版嵁渚濊禆鍏崇郴鍥?

```
PHM (鏁版嵁搴?
  鈫?澶栭敭
ImportSession (涓存椂鍒涘缓)
  鈫?澶栭敭
PHMData (鎵归噺鍒涘缓)
  鈹溾攢 澶栭敭 鈫?IMSDetectionResult
  鈹溾攢 澶栭敭 鈫?RuleDetectionResult
  鈹斺攢 澶栭敭 鈫?MSFGAnalysisResult
```

**娓呯悊椤哄簭**锛堝鏋渟ave_to_db=False锛夛細
```
1. 鍒犻櫎妫€娴嬬粨鏋滐紙IMSDetectionResult, RuleDetectionResult, MSFGAnalysisResult锛?
2. 鍒犻櫎鍘熷鏁版嵁锛圕MGData锛?
3. 鍒犻櫎瀵煎叆浼氳瘽锛圛mportSession锛?
```

---

## 鈿狅笍 閲嶈璁捐绾︽潫

### 1. 蹇呴』浣跨敤鏁版嵁搴?
鍗充娇鏄复鏃舵娴嬶紝涔熷繀椤伙細
- 创建PHMData对象（检测函数需要）
- 淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴擄紙鍏宠仈鍏崇郴锛?
- 从数据库读取结果（收集阶段）
- 鏈€鍚庢竻鐞嗭紙濡傛灉涓嶄繚瀛橈級

### 2. 不能绕过PHMData
鎵€鏈夋娴嬪嚱鏁扮殑璁捐閮戒緷璧朇MGData锛?
```python
run_ims_detection(cmg_data: PHMData)
evaluate_rules_for_data_point(data_point: PHMData)
_run_msfg_detection(record: PHMData, cmg: PHM)
```

### 3. 澶栭敭鍏崇郴蹇呴』瀛樺湪
```python
IMSDetectionResult.data_point = ForeignKey(PHMData)
# 濡傛灉PHMData涓嶅湪鏁版嵁搴擄紝鏃犳硶淇濆瓨妫€娴嬬粨鏋?
```

---

## 馃殌 鎬ц兘鑰冭檻

### 瀵逛簬澶ф枃浠讹紙109,511鏉¤褰曪級

**棰勮鑰楁椂**锛?
1. 瑙ｆ瀽鏂囦欢锛殈10绉?
2. 鍒涘缓PHMData锛殈30绉掞紙鎵归噺鍒涘缓锛?
3. IMS妫€娴嬶細~5鍒嗛挓锛堥鐜囨帶鍒跺悗绾?涓囨潯锛?
4. 瑙勫垯妫€娴嬶細~1鍒嗛挓锛堜粎寮傚父甯э級
5. MSFG妫€娴嬶細~2鍒嗛挓锛堜粎寮傚父甯э級
6. 鏀堕泦缁撴灉锛殈5绉?
7. 娓呯悊鏁版嵁锛殈20绉掞紙濡傛灉涓嶄繚瀛橈級

**鎬昏**锛氱害8-10鍒嗛挓

### 浼樺寲寤鸿
1. 鉁?鏀寔max_rows闄愬埗锛堟祴璇曠敤锛?
2. 鉁?浣跨敤妫€娴嬮鐜囨帶鍒讹紙鍑忓皯妫€娴嬮噺锛?
3. 鉁?鎵归噺鏁版嵁搴撴搷浣?
4. 鈴?鍙€冭檻WebSocket杩涘害鎺ㄩ€?

---

## 📊 修改总结

### 淇鐨勬墍鏈夐敊璇?

1. **ImportSession瀛楁閿欒**
   - `status` 鈫?`processing_status`
   - `processing_options` 鈫?`detection_summary`
   - 娣诲姞 `method` 瀛楁

2. **鏂囦欢璺緞閿欒**
   - 涓嶈兘灏嗕复鏃舵枃浠惰矾寰勮祴鍊肩粰FileField
   - 鍒涘缓`_parse_file_direct`鐩存帴瑙ｆ瀽

3. **鏃堕棿鎴宠В鏋愮己澶?*
   - 鍒犻櫎绠€鍖栫殑瑙ｆ瀽鏂规硶
   - 澶嶅埗鍘熸湁鐨勫畬鏁磋В鏋愰€昏緫

### 鏂板浠ｇ爜缁熻
- `process_file_for_detection`锛氱害100琛?
- `_parse_file_direct`锛氱害130琛?
- `_create_cmg_data_batch`锛氱害50琛?
- `_collect_detection_results`锛氱害90琛?
- `_aggregate_component_health`锛氱害40琛?
- `_calculate_overall_health`锛氱害10琛?
- `_cleanup_temp_detection_data`锛氱害20琛?

**鎬昏**锛氱害440琛屾柊澧炰唬鐮?

---

## 鉁?褰撳墠鐘舵€?

- 鉁?鎵€鏈夎娉曢敊璇凡淇
- 鉁?鏂囦欢瑙ｆ瀽閫昏緫瀹屾暣
- 鉁?鏁版嵁鍒涘缓娴佺▼姝ｇ‘
- 鉁?妫€娴嬫祦绋嬪畬鍏ㄥ鐢?
- 鉁?缁撴灉鏀堕泦鍜岃仛鍚堝疄鐜?
- 鉁?涓存椂鏁版嵁娓呯悊鏈哄埗

**鐜板湪搴旇鍙互姝ｅ父鎵ц瀹屾暣鐨勫疄鏃舵娴嬩簡锛?* 馃帀

---

**鏂囨。鍒涘缓鏃堕棿**锛?025-10-10  
**鍒嗘瀽娣卞害**锛氬畬鏁存祦绋嬪鐓? 
**浠ｇ爜璐ㄩ噺**锛氣渽 閫氳繃璇硶妫€鏌?



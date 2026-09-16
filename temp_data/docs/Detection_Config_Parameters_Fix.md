# 妫€娴嬮厤缃弬鏁颁娇鐢ㄤ慨澶?

## 🐛 问题描述

**鐢ㄦ埛鍙嶉**锛氬墠绔坊鍔犱簡`鏁版嵁澶勭悊妯″紡`鍜宍鏃堕棿鎴冲鐞哷閫夐」锛屼絾鍚庣娌℃湁鐪熸浣跨敤杩欎簺鍙傛暟銆?

**鐜拌薄**锛?
- 鐢ㄦ埛閫夋嫨"鎸囧畾澶勭悊琛屾暟锛?000"
- 瀹為檯澶勭悊浜嗘暣涓枃浠讹紙109,511鏉★級

---

## 🔍 问题分析

### 鍓嶇鍙戦€佺殑鍙傛暟
```javascript
formData.append('max_rows', detectionConfig.value.maxRows);
formData.append('add_milliseconds', detectionConfig.value.addMilliseconds);
```

### 鍚庣鎺ユ敹鎯呭喌

**淇鍓?*锛?
```python
# views.py - 鏈帴鏀跺弬鏁?
detection_mode = request.data.get('detection_mode', 'full')
save_results = request.data.get('save_results', 'false')
# 鉂?娌℃湁鎺ユ敹 max_rows
# 鉂?娌℃湁鎺ユ敹 add_milliseconds

# batch_processing.py - 鏈娇鐢ㄥ弬鏁?
def process_file_for_detection(...):
    parsed_data = self._parse_file_direct(file_path, max_rows=None)  # 鉂?濮嬬粓涓篘one
    # 鉂?娌℃湁鏃堕棿鎴冲幓閲嶅鐞?
```

---

## 鉁?淇鏂规

### 淇1锛氬悗绔帴鏀跺弬鏁帮紙views.py锛?

```python
# 获取数据处理参数
max_rows = request.data.get('max_rows')
if max_rows:
    try:
        max_rows = int(max_rows)
        logger.info(f"璁剧疆鏈€澶у鐞嗚鏁? {max_rows}")
    except (ValueError, TypeError):
        max_rows = None

add_milliseconds = request.data.get('add_milliseconds', 'false').lower() == 'true'
```

### 淇2锛氫紶閫掑弬鏁板埌澶勭悊鍣紙views.py锛?

```python
results = processor.process_file_for_detection(
    file_path=tmp_file_path,
    cmg=cmg,
    detection_mode=detection_mode,
    save_to_db=save_results,
    return_details=return_memory_results,
    max_rows=max_rows,                    # 鉁?浼犻€掑弬鏁?
    add_milliseconds=add_milliseconds     # 鉁?浼犻€掑弬鏁?
)
```

### 淇3锛氭洿鏂板嚱鏁扮鍚嶏紙batch_processing.py锛?

```python
def process_file_for_detection(
    self, 
    file_path: str, 
    cmg: PHM, 
    detection_mode: str = 'full',
    save_to_db: bool = False,
    return_details: bool = True,
    max_rows: Optional[int] = None,       # 鉁?鏂板鍙傛暟
    add_milliseconds: bool = False        # 鉁?鏂板鍙傛暟
) -> Dict[str, Any]:
```

### 修复4：使用max_rows参数

```python
# 瑙ｆ瀽鏂囦欢鏃朵娇鐢╩ax_rows
parsed_data = self._parse_file_direct(file_path, max_rows=max_rows)  # 鉁?浼犻€掑弬鏁?
```

**鏁堟灉**锛?
```python
# 鐢ㄦ埛閫夋嫨1000琛?
max_rows = 1000
# 瑙ｆ瀽鏃跺彧璇诲彇鍓?000琛?
for row_num, r in enumerate(rows[1:], 2):
    if max_rows and len(parsed_data) >= max_rows:
        break  # 鉁?鍦?000琛屾椂鍋滄
```

### 修复5：使用add_milliseconds参数

```python
# 鏃堕棿鎴冲幓閲嶅鐞?
if add_milliseconds:
    parsed_data = self._add_milliseconds_to_duplicate_timestamps(parsed_data)
    logger.info(f"[瀹炴椂妫€娴媇 鏃堕棿鎴冲幓閲嶅畬鎴?)
```

**鏁堟灉**锛?
```python
# 重复时间戳：
2022-10-09 15:36:48
2022-10-09 15:36:48
2022-10-09 15:36:48

# 鍘婚噸鍚庯細
2022-10-09 15:36:48.000000
2022-10-09 15:36:48.001000
2022-10-09 15:36:48.002000
```

### 淇6锛氬湪ImportSession涓褰曞弬鏁?

```python
temp_session = ImportSession.objects.create(
    cmg=cmg,
    method=ImportSession.Method.FILE,
    import_mode=ImportSession.ImportMode.IMPORT_AND_DETECT,
    processing_status=ImportSession.ProcessingStatus.STORING,
    total_records=total_frames,
    max_rows=max_rows,              # 鉁?璁板綍鍦╯ession涓?
    add_milliseconds=add_milliseconds,  # 鉁?璁板綍鍦╯ession涓?
    detection_summary={'is_realtime': True, 'save_to_db': save_to_db}
)
```

---

## 📊 参数流转完整路径

### max_rows参数
```
鍓嶇UI
  鈫?detectionConfig.maxRows = 1000
FormData
  鈫?formData.append('max_rows', 1000)
鍚庣API锛坴iews.py锛?
  鈫?max_rows = int(request.data.get('max_rows'))
澶勭悊鍣紙batch_processing.py锛?
  鈫?process_file_for_detection(max_rows=1000)
鏂囦欢瑙ｆ瀽
  鈫?_parse_file_direct(file_path, max_rows=1000)
瑙ｆ瀽寰幆
  鈫?if max_rows and len(parsed_data) >= max_rows: break
结果
  鉁?鍙В鏋?000琛?
```

### add_milliseconds参数
```
鍓嶇UI
  鈫?detectionConfig.addMilliseconds = true
FormData
  鈫?formData.append('add_milliseconds', true)
鍚庣API锛坴iews.py锛?
  鈫?add_milliseconds = request.data.get(...) == 'true'
澶勭悊鍣紙batch_processing.py锛?
  鈫?process_file_for_detection(add_milliseconds=True)
鏃堕棿鎴冲鐞?
  鈫?if add_milliseconds: _add_milliseconds_to_duplicate_timestamps()
结果
  鉁?涓洪噸澶嶆椂闂存埑娣诲姞姣
```

---

## 🧪 测试验证

### 娴嬭瘯鐢ㄤ緥1锛氶檺鍒惰鏁?
**閰嶇疆**锛?
- 鏁版嵁澶勭悊妯″紡锛氭寚瀹氬鐞嗚鏁?
- 澶勭悊琛屾暟锛?000

**棰勬湡缁撴灉**锛?
```
INFO: [瀹炴椂妫€娴媇 瑙ｆ瀽瀹屾垚锛屽叡 1000 鏉℃暟鎹?
INFO: [瀹炴椂妫€娴媇 鏁版嵁鍒涘缓瀹屾垚锛屽叡 1000 鏉MGData璁板綍
鉁?鍙鐞?000鏉★紝涓嶆槸鍏ㄩ儴109,511鏉?
```

### 测试用例2：时间戳去重
**閰嶇疆**锛?
- 鏃堕棿鎴冲鐞嗭細鉁?鑷姩娣诲姞姣

**棰勬湡缁撴灉**锛?
```
INFO: [瀹炴椂妫€娴媇 鏃堕棿鎴冲幓閲嶅畬鎴?
鉁?閲嶅鐨勬椂闂存埑琚嚜鍔ㄦ坊鍔犳绉掔骇宸紓
```

---

## 📝 修改总结

**淇敼鏂囦欢**锛?
1. `data_management/views.py` - 3澶勪慨鏀?
   - 接收max_rows参数
   - 接收add_milliseconds参数
   - 浼犻€掑弬鏁板埌澶勭悊鍣?

2. `data_management/batch_processing.py` - 5澶勪慨鏀?
   - 鏇存柊鍑芥暟绛惧悕锛堟坊鍔?涓弬鏁帮級
   - 使用max_rows参数
   - 使用add_milliseconds参数
   - 鍦↖mportSession涓褰曞弬鏁?
   - 修正方法调用名称

**鎬昏**锛?澶勪慨鏀?

---

## 鉁?淇鐘舵€?

- 鉁?max_rows鍙傛暟锛氬畬鏁存祦杞苟鐢熸晥
- 鉁?add_milliseconds鍙傛暟锛氬畬鏁存祦杞苟鐢熸晥
- 鉁?鍙傛暟鍦↖mportSession涓褰曪紙渚夸簬杩芥函锛?
- 鉁?璇硶妫€鏌ラ€氳繃

---

## 馃幆 浣跨敤绀轰緥

### 蹇€熸祴璇曪紙澶勭悊1000琛岋級
```
1. 閫夋嫨"涓婁紶鏂囦欢妫€娴?
2. 閫夋嫨PHM鍨嬪彿鍜屼釜浣?
3. 涓婁紶鏂囦欢
4. 鏁版嵁澶勭悊妯″紡锛氭寚瀹氬鐞嗚鏁?
5. 澶勭悊琛屾暟锛?000
6. 鏃堕棿鎴冲鐞嗭細鉁?鍕鹃€?
7. 寮€濮嬫娴?
鈫?鍙鐞嗗墠1000琛岋紝绾?0绉掑畬鎴?
```

### 瀹屾暣妫€娴嬶紙澶勭悊鍏ㄩ儴锛?
```
1. 閫夋嫨"涓婁紶鏂囦欢妫€娴?
2. 閫夋嫨PHM鍨嬪彿鍜屼釜浣?
3. 涓婁紶鏂囦欢
4. 鏁版嵁澶勭悊妯″紡锛氬鐞嗘暣涓枃浠?
5. 鏃堕棿鎴冲鐞嗭細鉁?鍕鹃€?
6. 寮€濮嬫娴?
鈫?澶勭悊鎵€鏈夋暟鎹紝绾?-10鍒嗛挓瀹屾垚
```

---

**淇鏃堕棿**锛?025-10-10  
**修复类型**：参数传递和使用  
**娴嬭瘯鐘舵€?*锛氣渽 灏辩华



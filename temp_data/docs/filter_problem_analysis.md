# 鏁版嵁杩囨护闂鍒嗘瀽

## 闂鐜拌薄
- 鏂囦欢瑙ｆ瀽锛?6000鏉¤褰?鉁?
- 鏁版嵁瀛樺偍锛?025鏉¤褰?鉂?
- 鏁版嵁涓㈠け锛?4975鏉¤褰?鉂?

## 鍘熷杩囨护閫昏緫鍒嗘瀽

### 1. 閿欒鐨勮繃婊ら€昏緫
```python
# 鍘熷浠ｇ爜锛堟湁闂鐨勭増鏈級
existing_records = set(
    PHMData.objects.filter(
        cmg=session.cmg, 
        timestamp__in=[item['timestamp'] for item in parsed_data]
    ).values_list("timestamp", "data")
)

for item in parsed_data:
    record_key = (item['timestamp'], str(item['data']))
    if record_key not in existing_records:  # 杩欓噷杩囨护鎺変簡澶ч噺璁板綍
        data_to_create.append(PHMData(...))
```

### 2. 闂鏍规簮

#### **闂1锛氭椂闂存埑绮惧害闂**
```python
# 绀轰緥鏁版嵁
鏃堕棿鎴?: "2025-08-17 10:00:00"  # 绮剧‘鍒扮
鏃堕棿鎴?: "2025-08-17 10:00:00"  # 鐩稿悓鏃堕棿鎴?
鏃堕棿鎴?: "2025-08-17 10:00:00"  # 鐩稿悓鏃堕棿鎴?
```

**闂**锛氬綋鏃堕棿鎴冲彧绮剧‘鍒扮鏃讹紝鍚屼竴绉掑唴鐨勫甯ф暟鎹細琚璁や负鏄噸澶嶇殑銆?

#### **闂2锛氭暟鎹簭鍒楀寲闂**
```python
record_key = (item['timestamp'], str(item['data']))
```

**闂**锛?
- `str(item['data'])` 鍙兘浜х敓涓嶅悓鐨勫瓧绗︿覆琛ㄧず
- 娴偣鏁扮簿搴﹂棶棰橈細`1.0` vs `1.0000000000000001`
- 瀛楀吀閿『搴忛棶棰橈細`{'a':1, 'b':2}` vs `{'b':2, 'a':1}`

#### **闂3锛氭暟鎹簱鏌ヨ鑼冨洿杩囧ぇ**
```python
PHMData.objects.filter(
    cmg=session.cmg, 
    timestamp__in=[item['timestamp'] for item in parsed_data]  # 16000涓椂闂存埑
)
```

**闂**锛?
- 鏌ヨ16000涓椂闂存埑锛屾€ц兘鏋佸樊
- 鍙兘瑙﹀彂鏁版嵁搴撴煡璇㈤檺鍒?
- 鍐呭瓨鍗犵敤杩囧ぇ

## 鍏蜂綋妗堜緥鍒嗘瀽

### 鍦烘櫙锛?6k琛屾暟鎹紝鏃堕棿鎴崇簿纭埌绉?

```python
# 鍋囪鏁版嵁鍒嗗竷
鏃堕棿鎴?"2025-08-17 10:00:00": 1000琛屾暟鎹?
鏃堕棿鎴?"2025-08-17 10:00:01": 1000琛屾暟鎹?
...
鏃堕棿鎴?"2025-08-17 10:00:15": 1000琛屾暟鎹?
```

### 鍘熷閫昏緫鎵ц杩囩▼

1. **鏌ヨ宸插瓨鍦ㄨ褰?*锛?
   ```python
   # 鏌ヨ鎵€鏈?6k涓椂闂存埑鐨勮褰?
   existing_records = PHMData.objects.filter(
       cmg=session.cmg, 
       timestamp__in=[16000涓椂闂存埑]
   ).values_list("timestamp", "data")
   ```

2. **杩囨护閫昏緫**锛?
   ```python
   for item in parsed_data:  # 16000鏉¤褰?
       record_key = (item['timestamp'], str(item['data']))
       if record_key not in existing_records:  # 澶ч儴鍒嗚杩囨护鎺?
           data_to_create.append(...)
   ```

3. **缁撴灉**锛?
   - 鐢变簬鏃堕棿鎴崇浉鍚岋紝澶ч儴鍒嗚褰曠殑`record_key`琚涓烘槸閲嶅鐨?
   - 鍙湁1025鏉¤褰曢€氳繃杩囨护
   - 14975鏉¤褰曡閿欒杩囨护鎺?

## 淇鏂规

### 1. 绉婚櫎涓嶅繀瑕佺殑杩囨护
```python
# 淇鍚庣殑浠ｇ爜
for item in parsed_data:  # 16000鏉¤褰?
    data_to_create.append(PHMData(  # 鎵€鏈夎褰曢兘鍒涘缓
        cmg=session.cmg,
        timestamp=item['timestamp'],
        data=item['data'],
        import_session=session
    ))
```

### 2. 浣跨敤鏁版嵁搴撶骇鍒殑鍘婚噸
```python
PHMData.objects.bulk_create(data_to_create, ignore_conflicts=True)
```

**浼樺娍**锛?
- 璁╂暟鎹簱澶勭悊鐪熸鐨勯噸澶?
- 閬垮厤搴旂敤灞傜殑澶嶆潅閫昏緫
- 鎬ц兘鏇村ソ

### 3. 姝ｇ‘鐨勬暟鎹ā鍨嬭璁?

濡傛灉纭疄闇€瑕佸幓閲嶏紝搴旇锛?

```python
# 鍦ㄦā鍨嬪眰闈㈠畾涔夊敮涓€绾︽潫
class PHMData(models.Model):
    cmg = models.ForeignKey(PHM, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    data = models.JSONField()
    import_session = models.ForeignKey(ImportSession, on_delete=models.CASCADE)
    
    class Meta:
        # 鍙湪鐪熸闇€瑕佸敮涓€鎬х殑瀛楁涓婅缃害鏉?
        unique_together = ['cmg', 'timestamp', 'data']  # 濡傛灉纭疄闇€瑕?
```

## 缁忛獙鏁欒

### 1. 閬垮厤杩囧害杩囨护
- 鍦ㄦ暟鎹鍏ラ樁娈碉紝搴旇灏介噺淇濈暀鎵€鏈夋暟鎹?
- 璁╂暟鎹簱澶勭悊鐪熸鐨勯噸澶嶉棶棰?
- 搴旂敤灞傝繃婊ゅ鏄撳嚭閿?

### 2. 鐞嗚В涓氬姟閫昏緫
- 姣忚鏁版嵁 = 涓€甯?= 涓€涓娴嬪崟鍏?
- 鏃堕棿鎴崇浉鍚屼絾鏁版嵁涓嶅悓锛屽簲璇ヤ繚鐣?
- 鍙湁瀹屽叏鐩稿悓鐨勮褰曟墠鑰冭檻鍘婚噸

### 3. 鎬ц兘鑰冭檻
- 閬垮厤鍦ㄥ簲鐢ㄥ眰杩涜澶ч噺鏁版嵁鐨勮繃婊?
- 浣跨敤鏁版嵁搴撶殑鎵归噺鎿嶄綔
- 鑰冭檻浣跨敤`ignore_conflicts=True`

### 4. 娴嬭瘯楠岃瘉
- 濮嬬粓楠岃瘉瑙ｆ瀽鏁伴噺 = 瀛樺偍鏁伴噺
- 妫€鏌ユ槸鍚︽湁鎰忓鐨勬暟鎹涪澶?
- 鐩戞帶澶勭悊鎬ц兘

## 鎬荤粨

杩囨护闂鐨勪富瑕佸師鍥犳槸锛?
1. **閿欒鐞嗚В浜嗕笟鍔￠渶姹?*锛氳涓烘椂闂存埑鐩稿悓灏辨槸閲嶅
2. **杩囧害澶嶆潅鐨勫簲鐢ㄥ眰杩囨护**锛氬簲璇ュ湪鏁版嵁搴撳眰澶勭悊
3. **鎬ц兘闂**锛氬ぇ閲忔暟鎹煡璇㈠拰杩囨护瀵艰嚧鎬ц兘涓嬮檷
4. **鏁版嵁绮惧害闂**锛氬瓧绗︿覆姣旇緝鐨勪笉纭畾鎬?

淇鍚庣殑鏂规绠€鍗曘€侀珮鏁堛€佹纭細
- 淇濈暀鎵€鏈夎В鏋愮殑鏁版嵁
- 浣跨敤鏁版嵁搴撶殑`ignore_conflicts=True`澶勭悊鐪熸鐨勯噸澶?
- 纭繚姣忓抚鏁版嵁閮借兘琚纭娴?


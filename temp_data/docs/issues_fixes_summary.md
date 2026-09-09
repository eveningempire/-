# 闂淇鍜屾敼杩涙€荤粨

## 1. IMS妫€娴嬬粨鏋滈〉闈㈡煡璇㈤棶棰?

### 闂鎻忚堪
- IMS妫€娴嬬粨鏋滈〉闈㈡棤娉曟煡璇㈠埌缁撴灉
- 妫€娴嬪畬鎴愬悗鏈塈MS缁撴灉锛屼絾椤甸潰鏄剧ず涓虹┖

### 淇鍐呭
1. **鍓嶇鍒嗛〉浼樺寲**锛?
   - 淇敼榛樿姣忛〉鏄剧ず100鏉¤褰?
   - 鍒濆鍔犺浇鏃跺彧鍔犺浇绗竴椤垫暟鎹紝鎻愰珮鍔犺浇閫熷害
   - 閬垮厤涓€娆℃€у姞杞芥墍鏈夋暟鎹鑷寸殑闀挎椂闂寸瓑寰?

2. **鍒嗛〉鍔犺浇浼樺寲**锛?
   ```javascript
   // 淇鍓嶏細涓€娆℃€у姞杞芥墍鏈夋暟鎹?
   onMounted(async () => {
     await loadCmgs();
     await loadResults();
   });
   
   // 淇鍚庯細鍙姞杞界涓€椤?
   onMounted(async () => {
     await loadCmgs();
     currentPage.value = 1;  // 纭繚浠庣涓€椤靛紑濮?
     await loadResults();
   });
   ```

3. **API璋冪敤纭**锛?
   - 纭鍓嶇璋冪敤 `/health/ims-results/` 鏄纭殑
   - 鍚庣API鏀寔鍒嗛〉鍙傛暟 `limit` 鍜?`offset`
   - 杩斿洖鏍煎紡锛歚{results: [], count: 鎬绘暟}`

## 2. 鍒嗛〉鏄剧ず浼樺寲

### 淇鐨勯〉闈?
1. **IMS妫€娴嬬粨鏋滈〉闈?* (`IMSResults.vue`)
   - 榛樿姣忛〉100鏉?
   - 鏀寔50, 100, 200, 500, 1000鏉?椤?
   - 鍒濆鍙姞杞界涓€椤?

2. **瑙勫垯妫€娴嬬粨鏋滈〉闈?* (`RuleResults.vue`)
   - 榛樿姣忛〉100鏉?
   - 鏀寔50, 100, 200, 500, 1000鏉?椤?
   - 鍒濆鍙姞杞界涓€椤?

3. **MSFG妫€娴嬬粨鏋滈〉闈?* (`MSFGResults.vue`)
   - 榛樿姣忛〉100鏉?
   - 鏀寔50, 100, 200, 500, 1000鏉?椤?
   - 鍒濆鍙姞杞界涓€椤?

### 鎬ц兘鏀硅繘
- **鍔犺浇鏃堕棿**锛氫粠鍔犺浇鍏ㄩ儴鏁版嵁鏀逛负鍙姞杞界涓€椤碉紝澶у箙鎻愬崌椤甸潰鍝嶅簲閫熷害
- **鍐呭瓨浣跨敤**锛氬噺灏戝墠绔唴瀛樺崰鐢?
- **鐢ㄦ埛浣撻獙**锛氱敤鎴峰彲浠ュ揩閫熺湅鍒扮粨鏋滐紝鐒跺悗鏍规嵁闇€瑕佹煡鐪嬫洿澶?

## 3. 鏁版嵁搴撶粺璁¤〃

### 鏂板鍔熻兘
鍒涘缓浜?`DatabaseStatistics` 妯″瀷鏉ョ淮鎶ゅ悇绉嶆暟鎹殑鎬绘暟锛?

```python
class DatabaseStatistics(models.Model):
    stat_type = models.CharField(max_length=20, choices=STAT_TYPE_CHOICES)
    cmg = models.ForeignKey(PHM, on_delete=models.CASCADE, null=True, blank=True)
    count = models.BigIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
```

### 缁熻绫诲瀷
- `cmg_data`: PHM閬ユ祴鏁版嵁
- `ims_results`: IMS妫€娴嬬粨鏋?
- `rule_results`: 瑙勫垯妫€娴嬬粨鏋?
- `msfg_results`: MSFG妫€娴嬬粨鏋?
- `anomaly_frames`: 寮傚父甯?
- `total_frames`: 鎬诲抚鏁?

### API绔偣
1. **鑾峰彇缁熻淇℃伅**锛歚GET /api/v1/data/data/statistics/`
   - 鏀寔鎸塁MG鏌ヨ锛歚?cmg_id=xxx`
   - 杩斿洖鎵€鏈夌粺璁＄被鍨嬬殑鏁版嵁

2. **鍒锋柊缁熻淇℃伅**锛歚POST /api/v1/data/data/refresh-statistics/`
   - 閲嶆柊璁＄畻鎵€鏈夌粺璁℃暟鎹?
   - 鏀寔鍏ㄥ眬鍜屾寜PHM缁熻

### 浣跨敤鍦烘櫙
1. **Dashboard椤甸潰**锛氬揩閫熸樉绀哄悇绉嶆暟鎹殑鎬绘暟
2. **缁撴灉椤甸潰**锛氭樉绀?鍏辨壘鍒?X 鏉¤褰?
3. **绯荤粺鐩戞帶**锛氱洃鎺ф暟鎹闀胯秼鍔?
4. **鎬ц兘浼樺寲**锛氶伩鍏嶉绻佺殑COUNT鏌ヨ

## 4. 姣鏃堕棿鎴冲鐞?

### 闂鑳屾櫙
- 鏃堕棿鎴冲彧绮剧‘鍒扮锛屽鑷村悓涓€绉掑唴鐨勫甯ф暟鎹璇涓烘槸閲嶅鐨?
- 鏁版嵁瀛樺偍鏃跺ぇ閲忚褰曡杩囨护鎺?

### 瑙ｅ喅鏂规
鍦ㄦ枃浠惰В鏋愬畬鎴愬悗鑷姩娣诲姞姣鏃堕棿鎴筹細

```python
def _add_milliseconds_to_duplicate_timestamps(self, parsed_data):
    """涓洪噸澶嶇殑鏃堕棿鎴虫坊鍔犳绉掞紝纭繚姣忓抚閮芥湁鍞竴鐨勬椂闂存埑"""
    # 鎸夋椂闂存埑鍒嗙粍
    timestamp_groups = {}
    for item in parsed_data:
        ts = item['timestamp']
        ts_key = ts.replace(microsecond=0)  # 绮剧‘鍒扮
        if ts_key not in timestamp_groups:
            timestamp_groups[ts_key] = []
        timestamp_groups[ts_key].append(item)
    
    # 澶勭悊閲嶅鏃堕棿鎴?
    for ts_key, items in timestamp_groups.items():
        if len(items) > 1:
            # 涓烘瘡缁勯噸澶嶆椂闂存埑娣诲姞閫掑姣
            for i, item in enumerate(items):
                new_ts = ts_key.replace(microsecond=i * 1000)
                item['timestamp'] = new_ts
```

### 澶勭悊鏁堟灉
- **鏁版嵁瀹屾暣鎬?*锛氱‘淇濇墍鏈夎В鏋愮殑璁板綍閮借瀛樺偍
- **鏃堕棿鎴冲敮涓€鎬?*锛氭瘡甯ч兘鏈夊敮涓€鐨勬椂闂存埑
- **鍚戝悗鍏煎**锛氫笉褰卞搷宸叉湁鍔熻兘

## 5. 娴佸紡澶勭悊浼樺寲

### 闂鑳屾櫙
- 澶ф暟鎹噺澶勭悊鏃剁敤鎴风瓑寰呮椂闂磋繃闀?
- 111绉掑鐞嗘椂闂达紝鐢ㄦ埛鏃犳硶鐪嬪埌瀹炴椂杩涘害

### 瑙ｅ喅鏂规
瀹炵幇鏅鸿兘娴佸紡澶勭悊锛?

```python
# 鍒ゆ柇鏄惁闇€瑕佹祦寮忓鐞嗭紙瓒呰繃1000甯э級
STREAMING_THRESHOLD = 1000
use_streaming = len(records) > STREAMING_THRESHOLD

if use_streaming:
    return self._run_streaming_detection_pipeline(...)
else:
    return self._run_batch_detection_pipeline(...)
```

### 娴佸紡澶勭悊鐗圭偣
- **鎵规澶у皬**锛?00甯?鎵?
- **瀹炴椂淇濆瓨**锛氭瘡鎵瑰畬鎴愬悗绔嬪嵆淇濆瓨缁撴灉
- **杩涘害鏇存柊**锛氭瘡鎵瑰畬鎴愬悗骞挎挱杩涘害
- **鏃╂湡缁撴灉鍙**锛氱涓€鎵圭粨鏋滃湪28绉掑悗鍗冲彲鏌ョ湅

## 6. 娴嬭瘯鑴氭湰

### 鍒涘缓鐨勬祴璇曡剼鏈?
1. `test_ims_results.py` - 娴嬭瘯IMS妫€娴嬬粨鏋滄煡璇?
2. `test_timestamp_fix.py` - 娴嬭瘯姣鏃堕棿鎴冲鐞?
3. `test_streaming_processing.py` - 娴嬭瘯娴佸紡澶勭悊
4. `test_broadcast_fix.py` - 娴嬭瘯杩涘害骞挎挱淇

### 娴嬭瘯瑕嗙洊
- 鏁版嵁瀛樺偍瀹屾暣鎬?
- 妫€娴嬬粨鏋滄纭€?
- API绔偣鍔熻兘
- 鎬ц兘鎸囨爣楠岃瘉

## 鎬荤粨

### 涓昏鏀硅繘
1. 鉁?**瑙ｅ喅IMS缁撴灉鏌ヨ闂**锛氫慨澶嶅墠绔垎椤靛拰API璋冪敤
2. 鉁?**浼樺寲椤甸潰鍔犺浇閫熷害**锛氭墍鏈夌粨鏋滈〉闈㈤兘鏀寔鍒嗛〉鍔犺浇
3. 鉁?**娣诲姞鏁版嵁搴撶粺璁″姛鑳?*锛氭彁渚涘揩閫熺殑鏁版嵁鎬绘暟鏌ヨ
4. 鉁?**淇鏃堕棿鎴崇簿搴﹂棶棰?*锛氱‘淇濇暟鎹畬鏁存€?
5. 鉁?**瀹炵幇娴佸紡澶勭悊**锛氭彁鍗囧ぇ鏁版嵁閲忓鐞嗕綋楠?
6. 鉁?**瀹屽杽娴嬭瘯瑕嗙洊**锛氱‘淇濆姛鑳界ǔ瀹氭€?

### 鎬ц兘鎻愬崌
- **椤甸潰鍔犺浇閫熷害**锛氫粠鍔犺浇鍏ㄩ儴鏁版嵁鏀逛负鍒嗛〉鍔犺浇
- **鏁版嵁澶勭悊鏁堢巼**锛氭祦寮忓鐞嗗噺灏戠敤鎴风瓑寰呮椂闂?
- **鏌ヨ鎬ц兘**锛氱粺璁¤〃閬垮厤棰戠箒COUNT鏌ヨ
- **鏁版嵁瀹屾暣鎬?*锛氭绉掓椂闂存埑纭繚鎵€鏈夋暟鎹兘琚鐞?

### 鐢ㄦ埛浣撻獙鏀硅繘
- **瀹炴椂杩涘害鍙**锛氭祦寮忓鐞嗘彁渚涘疄鏃惰繘搴︽洿鏂?
- **鏃╂湡缁撴灉鍙**锛氭棤闇€绛夊緟鍏ㄩ儴澶勭悊瀹屾垚
- **蹇€熷搷搴?*锛氬垎椤靛姞杞芥彁鍗囬〉闈㈠搷搴旈€熷害
- **鏁版嵁閫忔槑**锛氱粺璁′俊鎭彁渚涙竻鏅扮殑鏁版嵁姒傝


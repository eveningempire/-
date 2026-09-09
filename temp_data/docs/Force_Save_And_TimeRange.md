# 寮哄埗淇濆瓨缁撴灉涓庤嚜鍔ㄦ椂闂磋寖鍥磋缃?

## 馃幆 鏀硅繘鐩爣

鍩轰簬鐢ㄦ埛鍙嶉锛屽疄鏂戒袱涓噸瑕佹敼杩涳細
1. **寮哄埗淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴?*锛堜緵鍏朵粬妯″潡浣跨敤锛?
2. **鑷姩璁剧疆鏃堕棿娈典负鏂囦欢鐨勬椂闂磋寖鍥?*锛堜緵鍚庣画妯″潡浣跨敤锛?

---

## 馃搵 鏀硅繘鐞嗙敱

### 涓轰粈涔堣寮哄埗淇濆瓨锛?

#### 鍘熻璁＄殑闂
```
鐢ㄦ埛閫夋嫨"涓嶄繚瀛樼粨鏋?
  鈫?
妫€娴嬪畬鎴愬悗娓呯悊鎵€鏈夋暟鎹?
  鈫?
鍏朵粬妯″潡闇€瑕佹暟鎹椂锛?
  - 瀵垮懡棰勬祴妯″潡 鉂?鏃犳硶鑾峰彇妫€娴嬬粨鏋?
  - 閬ユ祴鍒嗘瀽妯″潡 鉂?鏃犳硶鍏宠仈鏁版嵁
  - 瑙勫垯璇︽儏鏌ョ湅 鉂?鏁版嵁宸叉竻鐞?
  - 鍘嗗彶鏌ヨ鍔熻兘 鉂?鏃犳暟鎹彲鏌?
```

#### 鏀硅繘鍚庣殑浼樺娍
```
妫€娴嬬粨鏋滃缁堜繚瀛樺埌鏁版嵁搴?
  鈫?
鍏朵粬妯″潡姝ｅ父宸ヤ綔锛?
  - 瀵垮懡棰勬祴妯″潡 鉁?鍙互鍩轰簬妫€娴嬬粨鏋滈娴?
  - 閬ユ祴鍒嗘瀽妯″潡 鉁?鍙互鍒嗘瀽鍙傛暟瓒嬪娍
  - 瑙勫垯璇︽儏鏌ョ湅 鉁?鍙互鏌ョ湅瑙﹀彂鐨勮鍒?
  - 鍘嗗彶鏌ヨ鍔熻兘 鉁?鍙互鍥炴函鏌ョ湅
```

### 涓轰粈涔堥渶瑕佽嚜鍔ㄨ缃椂闂存锛?

#### 鍘熻璁＄殑闂
```
瀹炴椂妫€娴嬫ā寮忥細
  - 鐢ㄦ埛涓婁紶鏂囦欢
  - 鎵ц妫€娴?
  - 鏄剧ず缁撴灉
  
鐢ㄦ埛鎯虫煡鐪嬪叾浠栨ā鍧楋細
  - 鐐瑰嚮"鍓╀綑瀵垮懡"鎸夐挳
  - 闇€瑕乼imeRange鍙傛暟 鉂?鏈缃?
  - 妯″潡鏃犳硶姝ｅ父宸ヤ綔
```

#### 鏀硅繘鍚庣殑浼樺娍
```
瀹炴椂妫€娴嬪畬鎴愬悗锛?
  - 鑷姩鎻愬彇鏂囦欢鐨勬椂闂磋寖鍥?
  - 璁剧疆timeRange = [绗竴甯ф椂闂? 鏈€鍚庝竴甯ф椂闂碷
  - 鎵€鏈変緷璧杢imeRange鐨勬ā鍧楁甯稿伐浣?鉁?
```

---

## 鉁?瀹炴柦鏂规

### 鏀硅繘1锛氬墠绔己鍒朵繚瀛橈紙UI灞傞潰锛?

#### 淇敼閰嶇疆鍒濆鍊?
```javascript
const detectionConfig = ref({
  mode: 'full',
  uploadMode: 'all',
  maxRows: 1000,
  addMilliseconds: true,
  saveResults: true  // 鉁?寮哄埗涓簍rue
});
```

#### 绂佺敤淇濆瓨寮€鍏?
```vue
<el-form-item label="淇濆瓨鍒版暟鎹簱">
  <el-switch 
    v-model="detectionConfig.saveResults" 
    disabled 
    :model-value="true"  <!-- 鉁?濮嬬粓鏄剧ず涓哄紑鍚?-->
  />
  <span style="margin-left: 10px; color: #909399; font-size: 12px;">
    妫€娴嬬粨鏋滃皢鑷姩淇濆瓨鍒版暟鎹簱锛堝繀闇€锛屼緵鍏朵粬妯″潡浣跨敤锛?
  </span>
</el-form-item>
```

**鏁堟灉**锛氱敤鎴风湅鍒板紑鍏虫槸鐏拌壊涓斿紑鍚姸鎬侊紝鏃犳硶鍏抽棴

---

### 鏀硅繘2锛氬悗绔己鍒朵繚瀛橈紙閫昏緫灞傞潰锛?

```python
# views.py
detection_mode = request.data.get('detection_mode', 'full')
save_results = True  # 鉁?寮哄埗淇濆瓨锛屽拷鐣ュ墠绔紶閫掔殑鍊?
return_memory_results = request.data.get('return_memory_results', 'false').lower() == 'true'

logger.info(f"瀹炴椂妫€娴嬶細寮哄埗淇濆瓨缁撴灉鍒版暟鎹簱锛堜緵鍚庣画妯″潡浣跨敤锛?)
```

**鍙岄噸淇濊瘉**锛氬嵆浣垮墠绔紶浜哷saveResults=false`锛屽悗绔篃浼氬己鍒朵繚瀛?

---

### 鏀硅繘3锛氳繑鍥炴椂闂磋寖鍥?

```python
# batch_processing.py

# 6. 娣诲姞鏃堕棿鑼冨洿淇℃伅
if stored_records:
    first_record = stored_records[0]
    last_record = stored_records[-1]
    
    results['time_range'] = {
        'start': first_record.timestamp.isoformat(),
        'end': last_record.timestamp.isoformat()
    }
    
    logger.debug(f"鏃堕棿鑼冨洿: {results['time_range']['start']} 鑷?{results['time_range']['end']}")

# 7. 鏍囪浼氳瘽涓哄畬鎴愶紙寮哄埗淇濆瓨锛?
temp_session.processing_status = ImportSession.ProcessingStatus.COMPLETED
temp_session.completed_at = timezone.now()
temp_session.save()
```

**杩斿洖鏍煎紡**锛?
```json
{
  "total_frames": 1000,
  "anomaly_count": 51,
  "time_range": {
    "start": "2022-10-09T15:36:48+00:00",
    "end": "2022-10-09T15:53:25+00:00"
  },
  ...
}
```

---

### 鏀硅繘4锛氬墠绔嚜鍔ㄨ缃椂闂存

```javascript
// startDetection鍑芥暟涓?
if (data.results.time_range) {
  timeRange.value = [
    new Date(data.results.time_range.start),
    new Date(data.results.time_range.end)
  ];
  console.log('鑷姩璁剧疆鏃堕棿娈?', timeRange.value);
}
```

**鏁堟灉**锛氭娴嬪畬鎴愬悗锛宍timeRange`鑷姩璁剧疆锛屽叾浠栨ā鍧楀彲浠ョ洿鎺ヤ娇鐢?

---

## 馃搳 鐗规畩鎯呭喌澶勭悊

### 鎯呭喌1锛氱敤鎴峰彧澶勭悊閮ㄥ垎琛屾暟

**鍦烘櫙**锛?
- 鏂囦欢鎬诲叡109,511鏉?
- 鐢ㄦ埛閫夋嫨鍙鐞?000鏉?

**澶勭悊**锛?
```python
# 鏃堕棿鑼冨洿 = 鍓?000鏉＄殑鏃堕棿鑼冨洿
first_record = stored_records[0]      # 绗?鏉?
last_record = stored_records[-1]      # 绗?000鏉?

time_range = {
  'start': first_record.timestamp,     # 鏂囦欢寮€濮嬫椂闂?
  'end': last_record.timestamp         # 绗?000鏉＄殑鏃堕棿锛堜笉鏄枃浠剁粨鏉熸椂闂达級
}
```

**鍚堢悊鎬?*锛?
- 鉁?timeRange鍑嗙‘鍙嶆槧浜嗗疄闄呮娴嬬殑鏁版嵁鑼冨洿
- 鉁?鍏朵粬妯″潡浣跨敤杩欎釜鑼冨洿鏌ヨ锛岃兘鑾峰彇鍒板搴旂殑鏁版嵁
- 鉁?閬垮厤浜嗘椂闂磋寖鍥翠笌鏁版嵁涓嶅尮閰嶇殑闂

---

## 馃幆 鐜板湪鐨勫畬鏁存祦绋?

### 瀹炴椂妫€娴嬫祦绋嬶紙鏀硅繘鍚庯級

```
鐢ㄦ埛涓婁紶鏂囦欢锛?09,511鏉★級
  鈫?
閰嶇疆锛氬鐞?000琛?
  鈫?
鎵ц妫€娴?
  鈹溾攢 瑙ｆ瀽鍓?000琛?
  鈹溾攢 鍒涘缓PHMData锛?000鏉★級
  鈹溾攢 鎵ц妫€娴嬶紙IMS+瑙勫垯+MSFG锛?
  鈹斺攢 淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴?鉁?寮哄埗淇濆瓨
  鈫?
杩斿洖缁撴灉锛堝寘鍚玹ime_range锛?
  {
    total_frames: 1000,
    time_range: {
      start: "2022-10-09T15:36:48",
      end: "2022-10-09T15:40:12"  鈫?绗?000鏉＄殑鏃堕棿
    },
    ...
  }
  鈫?
鍓嶇鏇存柊鏄剧ず
  鈹溾攢 鏇存柊寮傚父妫€娴嬫暟鎹?
  鈹溾攢 鏇存柊閮ㄤ欢鍋ュ悍鐘舵€?
  鈹斺攢 璁剧疆timeRange = [start, end] 鉁?鑷姩璁剧疆
  鈫?
鐢ㄦ埛鍙互浣跨敤鎵€鏈夊姛鑳斤細
  鉁?鏌ョ湅寮傚父璇︽儏锛堜粠鏁版嵁搴擄級
  鉁?鐐瑰嚮"鍓╀綑瀵垮懡"锛堟湁timeRange锛?
  鉁?鏌ョ湅閬ユ祴鏁版嵁锛堟湁timeRange锛?
  鉁?鍚庣画鍘嗗彶鏌ヨ锛堟暟鎹凡淇濆瓨锛?
```

---

## 馃敡 浠ｇ爜淇敼鎬荤粨

### 鍓嶇淇敼锛圖etectionOverview.vue锛?

1. **閰嶇疆鍒濆鍊?*锛?
   ```javascript
   saveResults: true  // 鏀逛负true
   ```

2. **UI绂佺敤**锛?
   ```vue
   <el-switch disabled :model-value="true" />
   ```

3. **鑷姩璁剧疆鏃堕棿娈?*锛?
   ```javascript
   if (data.results.time_range) {
     timeRange.value = [
       new Date(data.results.time_range.start),
       new Date(data.results.time_range.end)
     ];
   }
   ```

### 鍚庣淇敼锛坴iews.py锛?

```python
save_results = True  # 寮哄埗淇濆瓨
logger.info(f"瀹炴椂妫€娴嬶細寮哄埗淇濆瓨缁撴灉鍒版暟鎹簱锛堜緵鍚庣画妯″潡浣跨敤锛?)
```

### 鍚庣淇敼锛坆atch_processing.py锛?

1. **娣诲姞鏃堕棿鑼冨洿**锛?
   ```python
   results['time_range'] = {
       'start': first_record.timestamp.isoformat(),
       'end': last_record.timestamp.isoformat()
   }
   ```

2. **绉婚櫎娓呯悊閫昏緫**锛?
   ```python
   # 鍒犻櫎浜?_cleanup_temp_detection_data 璋冪敤
   # 鍒犻櫎浜?temp_session.delete() 璋冪敤
   ```

3. **鏍囪浼氳瘽瀹屾垚**锛?
   ```python
   temp_session.processing_status = ImportSession.ProcessingStatus.COMPLETED
   temp_session.save()
   ```

---

## 鉁?淇敼浼樺娍

### 1. 鏁版嵁瀹屾暣鎬?
- 鉁?鎵€鏈夋娴嬬粨鏋滄寔涔呭寲
- 鉁?鍙緵鍚庣画鏌ヨ鍜屽垎鏋?
- 鉁?鏁版嵁涓嶄細涓㈠け

### 2. 妯″潡鍏煎鎬?
- 鉁?瀵垮懡棰勬祴妯″潡鍙互姝ｅ父宸ヤ綔
- 鉁?閬ユ祴鍒嗘瀽妯″潡鍙互姝ｅ父宸ヤ綔
- 鉁?鎵€鏈変緷璧杢imeRange鐨勫姛鑳芥甯?

### 3. 鐢ㄦ埛浣撻獙
- 鉁?妫€娴嬪悗鍙互绔嬪嵆浣跨敤鎵€鏈夊姛鑳?
- 鉁?涓嶉渶瑕侀噸鏂版煡璇㈡垨涓婁紶
- 鉁?宸ヤ綔娴佺▼鏇存祦鐣?

### 4. 绯荤粺璁捐
- 鉁?鍘嗗彶鏌ヨ鍜屽疄鏃舵娴嬪畬鍏ㄧ粺涓€
- 鉁?鏁版嵁娴佷竴鑷?
- 鉁?缁存姢鎴愭湰浣?

---

## 馃帀 鏈€缁堟晥鏋?

### 鐢ㄦ埛鎿嶄綔
```
1. 涓婁紶鏂囦欢妫€娴嬶紙1000琛岋級
2. 妫€娴嬪畬鎴?
3. 椤甸潰鏄剧ず瀹屾暣缁撴灉
4. timeRange鑷姩璁剧疆涓猴細
   [2022-10-09 15:36:48, 2022-10-09 15:40:12]
```

### 鍚庣画鍙敤鍔熻兘
```
鉁?鐐瑰嚮寮傚父甯?鈫?鏌ョ湅璇︽儏锛堜粠鏁版嵁搴擄級
鉁?鐐瑰嚮閮ㄤ欢 鈫?鏌ョ湅閮ㄤ欢璇︽儏
鉁?鐐瑰嚮"鍓╀綑瀵垮懡" 鈫?瀵垮懡棰勬祴锛堟湁timeRange锛?
鉁?鏌ョ湅閬ユ祴鏁版嵁 鈫?閬ユ祴鍒嗘瀽锛堟湁timeRange锛?
鉁?鍒囨崲鍒板巻鍙叉ā寮?鈫?鍙互鏌ヨ鍒氭墠鐨勭粨鏋?
```

---

**瀹炴柦鏃堕棿**锛?025-10-10  
**鏀硅繘绫诲瀷**锛氭灦鏋勪紭鍖? 
**鐢ㄦ埛浣撻獙**锛氣渽 鏄捐憲鎻愬崌  
**绯荤粺瀹屾暣鎬?*锛氣渽 澧炲己



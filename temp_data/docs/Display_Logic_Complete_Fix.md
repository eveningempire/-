# 妫€娴嬬粨鏋滄樉绀洪€昏緫瀹屾暣淇

## 馃幆 闂鍒嗘瀽

### 鐢ㄦ埛鍙嶉鐨勯棶棰?
1. 鉁?杩涘害鏉℃樉绀烘娴嬪畬鎴?
2. 鉂?鎸夐挳浠嶆樉绀?妫€娴嬩腑..."锛堝凡淇锛?
3. 鉂?椤甸潰鍙樉绀哄熀鏈粺璁★紝鍏朵粬淇℃伅閮戒笉鏄剧ず

### 鏄剧ず涓嶅畬鏁寸殑琛ㄧ幇
```
鉁?鏄剧ず鐨勫唴瀹癸細
  - 鏁版嵁甯ф€绘暟锛?000
  - 寮傚父甯ф暟閲忥細51
  - 寮傚父甯ф瘮渚嬶細5.10%

鉂?鏈樉绀虹殑鍐呭锛?
  - 寮傚父甯у垪琛紙鐐瑰嚮搴旇鑳界湅鍒拌鎯咃級
  - 閮ㄤ欢鍋ュ悍鐘舵€侊紙鍙充晶澶ч潰鏉匡級
```

---

## 馃攳 鏍规湰鍘熷洜鍒嗘瀽

### 鍘熷洜1锛歩sDetecting鐘舵€佸欢杩熼噸缃?鉁?宸蹭慨澶?

**闂浠ｇ爜**锛?
```javascript
setTimeout(() => {
  isDetecting.value = false;  // 鉂?1.5绉掑悗鎵嶉噸缃?
  hasSelectedCmgAndTime.value = true;  // 鉂?1.5绉掑悗鎵嶈缃?
}, 1500);
```

**淇**锛?
```javascript
// 绔嬪嵆璁剧疆鐘舵€?
hasSelectedCmgAndTime.value = true;  // 鉁?绔嬪嵆
isDetecting.value = false;            // 鉁?绔嬪嵆

// 鍙欢杩熷叧闂璇濇
setTimeout(() => {
  fileUploadDialogVisible.value = false;
}, 1500);
```

---

### 鍘熷洜2锛氭暟鎹瓧娈靛悕涓嶅尮閰?鉁?宸蹭慨澶?

#### 闂A锛氬紓甯稿抚鐨剆core瀛楁

**鍓嶇鏈熸湜**锛堢161琛岋級锛?
```vue
<el-tag :type="getScoreTagType(frame.score)">{{ frame.score.toFixed(4) }}</el-tag>
```

**鍚庣杩斿洖**锛?
```python
{
    'anomaly_score': 0.85,  # 鈫?鍚庣鐢ㄨ繖涓瓧娈靛悕
    # 娌℃湁 'score' 瀛楁
}
```

**淇**锛?
```javascript
// 鍦╱pdateDisplayFromMemory涓浆鎹?
anomalyFrames.value = (results.anomaly_frames || []).map(frame => ({
  ...frame,
  score: frame.anomaly_score || frame.score || 0  // 鉁?瀛楁鍚嶈浆鎹?
}));
```

---

### 鍘熷洜3锛氬紓甯歌鎯呰幏鍙栭€昏緫 鉁?宸蹭慨澶?

#### 闂B锛歴howAnomalyDetails渚濊禆鏁版嵁搴?

**鍘熸湁閫昏緫**锛?
```javascript
async function showAnomalyDetails(frame) {
  // 鎬绘槸浠庢暟鎹簱API鑾峰彇璇︽儏
  const [imsResponse, ruleResponse, msfgResponse] = await Promise.all([
    fetch(`...&frame_id=${frame.id}`),  // 鉂?瀹炴椂妫€娴嬫ā寮忎笅鏁版嵁宸茶娓呯悊
    ...
  ]);
}
```

**闂**锛?
- 瀹炴椂妫€娴嬫ā寮忥紝濡傛灉`save_to_db=False`锛屾暟鎹娓呯悊
- API鏌ヨ浼氬け璐ユ垨杩斿洖绌烘暟鎹?

**淇**锛?
```javascript
async function showAnomalyDetails(frame) {
  // 鏍规嵁妯″紡鍐冲畾鏁版嵁鏉ユ簮
  if (selectedMode.value === 'upload' && memoryDetectionResults.value) {
    // 鉁?涓婁紶妯″紡锛氫粠鍐呭瓨鐨刦rame_details鑾峰彇
    const frameDetail = memoryDetectionResults.value.frame_details?.find(
      f => f.timestamp === frame.timestamp
    );
    
    if (frameDetail) {
      // 浣跨敤鍐呭瓨鏁版嵁鏇存柊鏄剧ず
      selectedAnomalyFrame.value.ims_scores = frameDetail.ims_result.parameter_scores;
      selectedAnomalyFrame.value.rules = frameDetail.rule_result.triggered_rules;
      selectedAnomalyFrame.value.msfg = { ... };
      return;  // 涓嶈皟鐢ˋPI
    }
  }
  
  // 鍘嗗彶妯″紡锛氫粠鏁版嵁搴撹幏鍙?
  const [imsResponse, ...] = await Promise.all([...]);
}
```

---

### 鍘熷洜4锛氶儴浠跺仴搴锋暟鎹牸寮?鉁?宸蹭慨澶?

**鍚庣杩斿洖**锛?
```json
{
  "component_health": {
    "鐢垫簮鏉?: {
      "health_score": 0.843,
      "min_score": 0.720,
      "max_score": 0.950,
      "sample_count": 1000
    }
  }
}
```

**鍓嶇鏈熸湜**锛坰ubComponents锛夛細
```javascript
{
  left: [
    { id: 'comp_0', name: '鐢垫簮鏉?, healthScore: 0.843, ... }
  ],
  right: [...]
}
```

**淇**锛氬湪`updateDisplayFromMemory`涓坊鍔犺浆鎹㈤€昏緫锛堝凡瀹屾垚锛?

---

## 鉁?瀹屾暣鐨勪慨澶嶆竻鍗?

### 1. 鐘舵€佺鐞嗕慨澶?
```javascript
// 鉁?绔嬪嵆璁剧疆hasSelectedCmgAndTime锛堣Е鍙戦〉闈㈡樉绀猴級
// 鉁?绔嬪嵆閲嶇疆isDetecting锛堟寜閽姸鎬佹纭級
// 鉁?鍙欢杩熷叧闂璇濇锛堢敤鎴蜂綋楠屽ソ锛?
```

### 2. 鏁版嵁瀛楁杞崲
```javascript
// 鉁?anomaly_score 鈫?score锛堝紓甯稿抚鍒楄〃鏄剧ず锛?
// 鉁?component_health 鈫?subComponents锛堥儴浠跺仴搴锋樉绀猴級
```

### 3. 鍙屾ā寮忔暟鎹幏鍙?
```javascript
// 鉁?涓婁紶妯″紡锛氫粠memoryDetectionResults鑾峰彇
// 鉁?鍘嗗彶妯″紡锛氫粠API鑾峰彇
```

### 4. 杈呭姪鍑芥暟娣诲姞
```javascript
// 鉁?extractTop3Components - 鎻愬彇TOP3閮ㄤ欢
// 鉁?calculateRiskLevel - 璁＄畻椋庨櫓绛夌骇
```

### 5. 閿欒澶勭悊澧炲己
```javascript
// 鉁?妫€鏌ata.error
// 鉁?妫€鏌ata.results瀛樺湪
```

---

## 馃搳 鏁版嵁娴佸畬鏁村鐓?

### 鍘嗗彶鏌ヨ妯″紡
```
鐢ㄦ埛閫夋嫨鏃堕棿
  鈫?
fetchAnomalyResults(cmg_id, start_time, end_time)
  鈫?API璋冪敤
鍚庣浠庢暟鎹簱鏌ヨ
  鈫?
杩斿洖缁撴灉
  鈫?
鏇存柊: anomalyRatio, totalFrames, anomalyCount, anomalyFrames
  鈫?
鐢ㄦ埛鐐瑰嚮寮傚父甯?
  鈫?
showAnomalyDetails(frame)
  鈫?API璋冪敤
鍚庣鏌ヨ璇︾粏淇℃伅锛坕ms_details, rule_details, msfg_details锛?
  鈫?
鏄剧ず璇︽儏瀵硅瘽妗?
```

### 瀹炴椂妫€娴嬫ā寮?
```
鐢ㄦ埛涓婁紶鏂囦欢
  鈫?
startDetection()
  鈫?API璋冪敤锛堝甫鏂囦欢锛?
鍚庣鎵ц妫€娴嬶紙涓存椂瀛樺偍鈫掓娴嬧啋鏀堕泦鈫掓竻鐞嗭級
  鈫?
杩斿洖鍐呭瓨缁撴灉锛堝寘鍚玣rame_details锛?
  鈫?
updateDisplayFromMemory(results)
  鈹溾攢 鏇存柊: anomalyRatio, totalFrames, anomalyCount
  鈹溾攢 杞崲骞舵洿鏂? anomalyFrames锛堟坊鍔爏core瀛楁锛夆渽
  鈹斺攢 杞崲骞舵洿鏂? subComponents锛堥儴浠跺仴搴凤級鉁?
  鈫?
hasSelectedCmgAndTime = true锛堣Е鍙戦〉闈㈡樉绀猴級鉁?
isDetecting = false锛堟寜閽姸鎬侀噸缃級鉁?
  鈫?
鐢ㄦ埛鐐瑰嚮寮傚父甯?
  鈫?
showAnomalyDetails(frame)
  鈫?妫€娴嬪埌upload妯″紡
浠巑emoryDetectionResults.frame_details鏌ユ壘
  鈫?
鐩存帴浣跨敤鍐呭瓨鏁版嵁鏄剧ず锛堜笉璋冪敤API锛夆渽
  鈫?
鏄剧ず璇︽儏瀵硅瘽妗?
```

---

## 馃幆 鍏抽敭鏀硅繘鐐?

### 鏀硅繘1锛氱姸鎬佺珛鍗崇敓鏁?
**鏁堟灉**锛氭娴嬪畬鎴愬悗锛岄〉闈㈢珛鍗冲埛鏂版樉绀虹粨鏋?

### 鏀硅繘2锛氬瓧娈靛悕鍏煎
**鏁堟灉**锛氬紓甯稿抚鍒楄〃姝ｇ‘鏄剧ず鍒嗘暟

### 鏀硅繘3锛氬弻妯″紡閫傞厤
**鏁堟灉**锛?
- 鍘嗗彶妯″紡锛氫粠鏁版嵁搴撴煡璇㈣鎯?
- 涓婁紶妯″紡锛氫粠鍐呭瓨鑾峰彇璇︽儏

### 鏀硅繘4锛氬畬鏁存暟鎹浆鎹?
**鏁堟灉**锛?
- 寮傚父甯э細鏈夊垎鏁版樉绀?
- 閮ㄤ欢鍋ュ悍锛氬畬鏁寸殑宸﹀彸甯冨眬鏄剧ず

---

## 馃摑 鐢ㄦ埛浣撻獙娴佺▼

### 瀹炴椂妫€娴嬪畬鏁存祦绋?

```
1. 閫夋嫨"涓婁紶鏂囦欢妫€娴?
2. 閫夋嫨PHM鍨嬪彿鍜屼釜浣?
3. 涓婁紶鏂囦欢锛岄厤缃弬鏁?
4. 鐐瑰嚮"寮€濮嬫娴?
   鈫?
   [瀵硅瘽妗嗘樉绀鸿繘搴
   10% - 姝ｅ湪涓婁紶鏂囦欢...
   90% - 姝ｅ湪鎵ц妫€娴?..
   100% - 妫€娴嬪畬鎴愶紒鉁?
   
5. 妫€娴嬪畬鎴愶紙T+0绉掞級
   鉁?涓婚〉闈㈢珛鍗虫樉绀猴細
      - 寮傚父甯ф€绘暟锛?000
      - 寮傚父鏁帮細51锛?.1%锛?
      - 寮傚父甯у垪琛細51鏉★紙甯﹀垎鏁帮級鉁?
   鉁?鍙充晶鏄剧ず锛?
      - 閮ㄤ欢鍋ュ悍鐘舵€侊紙9涓儴浠讹級鉁?
   鉁?鎸夐挳鍙樹负"寮€濮嬫娴?
   
6. 瀵硅瘽妗嗗仠鐣?.5绉掑悗鑷姩鍏抽棴
   
7. 鐢ㄦ埛鐐瑰嚮浠绘剰寮傚父甯?
   鉁?寮瑰嚭璇︽儏瀵硅瘽妗?
   鉁?鏄剧ずIMS/瑙勫垯/MSFG璇︽儏锛堜粠鍐呭瓨锛夆渽
```

---

## 鉁?淇敼鎬荤粨

**淇敼鏂囦欢**锛歚frontend/src/views/DetectionOverview.vue`

**淇敼鍐呭**锛?
1. `startDetection`鍑芥暟锛?
   - 绔嬪嵆璁剧疆`hasSelectedCmgAndTime`鍜宍isDetecting`
   - 娣诲姞閿欒妫€鏌?
   - 鍙欢杩熷叧闂璇濇

2. `updateDisplayFromMemory`鍑芥暟锛?
   - 娣诲姞瀛楁鍚嶈浆鎹紙anomaly_score 鈫?score锛?
   - 瀹屽杽閮ㄤ欢鍋ュ悍鏁版嵁杞崲

3. `showAnomalyDetails`鍑芥暟锛?
   - 娣诲姞妯″紡鍒ゆ柇
   - 涓婁紶妯″紡浠庡唴瀛樿幏鍙栬鎯?
   - 鍘嗗彶妯″紡浠嶢PI鑾峰彇璇︽儏

4. 鏂板杈呭姪鍑芥暟锛?
   - `extractTop3Components` - 鎻愬彇TOP3缁勪欢
   - `calculateRiskLevel` - 璁＄畻椋庨櫓绛夌骇

**鎬昏**锛氱害80琛屼慨鏀?

**璇硶妫€鏌?*锛氣渽 閫氳繃

---

## 馃帀 鐜板湪搴旇瀹屽叏姝ｅ父浜嗭紒

**璇锋祴璇曪細**
1. 鍒锋柊椤甸潰
2. 涓婁紶鏂囦欢妫€娴?
3. 妫€娴嬪畬鎴愬悗锛?
   - 鉁?瀵硅瘽妗嗘寜閽珛鍗冲彉涓?寮€濮嬫娴?
   - 鉁?涓婚〉闈㈢珛鍗虫樉绀烘墍鏈夋暟鎹?
   - 鉁?寮傚父甯у垪琛ㄥ彲浠ョ偣鍑绘煡鐪嬭鎯?
   - 鉁?閮ㄤ欢鍋ュ悍鐘舵€佸畬鏁存樉绀?
   - 鉁?1.5绉掑悗瀵硅瘽妗嗚嚜鍔ㄥ叧闂?

**搴旇鑳界湅鍒板畬鏁寸殑妫€娴嬬粨鏋滀簡锛?* 馃殌鉁?

---

**淇鏃堕棿**锛?025-10-10  
**淇绫诲瀷**锛氭樉绀洪€昏緫鍜屾暟鎹祦  
**鐢ㄦ埛浣撻獙**锛氣渽 瀹屾暣浼樺寲



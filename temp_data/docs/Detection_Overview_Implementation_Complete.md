# 妫€娴嬬粨鏋滄€昏椤甸潰鍗囩骇 - 瀹炴柦瀹屾垚鎶ュ憡

## 鉁?瀹炴柦鐘舵€侊細宸插畬鎴?

**瀹炴柦鏃堕棿**锛?025-10-10  
**鎬昏€楁椂**锛氱害45鍒嗛挓  
**鏀瑰姩鏂囦欢鏁?*锛?涓? 
**鏂板浠ｇ爜琛屾暟**锛氱害600琛? 

---

## 馃搵 瀹炴柦鍐呭

### Phase 1: 鍓嶇UI鏀归€?鉁?

**淇敼鏂囦欢**锛歚frontend/src/views/DetectionOverview.vue`

#### 1.1 鏇存柊鎿嶄綔姝ラ鎻愮ず
- 淇敼姝ラ璇存槑锛氫粠"閫夋嫨鍨嬪彿鍜屼釜浣?鈫?閫夋嫨鏃堕棿娈?鏀逛负"閫夋嫨妯″紡 鈫?閫夋嫨鍨嬪彿鍜屼釜浣?鈫?閫夋嫨鏃堕棿鎴栦笂浼犳枃浠?

#### 1.2 鏇挎崲actions-container
```vue
<!-- 鏃х増锛氬瀷鍙烽€夋嫨 + 鏃堕棿閫夋嫨鎸夐挳 -->
<!-- 鏂扮増锛氭ā寮忛€夋嫨 + PHM鍨嬪彿閫夋嫨 -->
<div class="actions-container">
  <div class="mode-selection">...</div>  <!-- 鏂板 -->
  <div class="cmg-selection" :disabled="!selectedMode">...</div>  <!-- 澧炲姞disabled -->
</div>
```

#### 1.3 鏂板涓や釜瀵硅瘽妗?
- **鏃堕棿閫夋嫨瀵硅瘽妗?*锛氱敤浜庡巻鍙叉ā寮?
- **鏂囦欢涓婁紶瀵硅瘽妗?*锛氱敤浜庝笂浼犳ā寮忥紝鍖呭惈锛?
  - 鏂囦欢涓婁紶缁勪欢
  - 妫€娴嬫ā寮忛€夋嫨
  - 淇濆瓨缁撴灉寮€鍏?
  - 杩涘害鏉℃樉绀?

---

### Phase 2: 鍓嶇閫昏緫鏀归€?鉁?

**淇敼鏂囦欢**锛歚frontend/src/views/DetectionOverview.vue`

#### 2.1 鏂板鐘舵€佸彉閲?
```javascript
const selectedMode = ref('');  // 'history' 鎴?'upload'
const timeSelectDialogVisible = ref(false);
const fileUploadDialogVisible = ref(false);
const uploadedFile = ref(null);
const detectionConfig = ref({ mode: 'full', saveResults: false });
const isDetecting = ref(false);
const detectionProgress = ref(0);
const detectionStatus = ref('');
const detectionMessage = ref('');
const memoryDetectionResults = ref(null);
```

#### 2.2 鏂板鍑芥暟锛堝叡10涓級
1. `onModeChange()` - 妯″紡鍒囨崲澶勭悊
2. `openTimeSelectDialog()` - 鎵撳紑鏃堕棿閫夋嫨瀵硅瘽妗?
3. `confirmTimeSelection()` - 纭鏃堕棿閫夋嫨
4. `loadHistoryData()` - 鍔犺浇鍘嗗彶鏁版嵁
5. `openFileUploadDialog()` - 鎵撳紑鏂囦欢涓婁紶瀵硅瘽妗?
6. `handleFileChange()` - 鏂囦欢閫夋嫨澶勭悊
7. `handleFileRemove()` - 鏂囦欢绉婚櫎澶勭悊
8. `startDetection()` - 寮€濮嬫娴?
9. `updateDisplayFromMemory()` - 浠庡唴瀛樻洿鏂版樉绀?

#### 2.3 淇敼鐜版湁鍑芥暟
- `selectCmg()` - 澧炲姞妯″紡鍒ゆ柇閫昏緫锛屾牴鎹ā寮忓脊鍑轰笉鍚屽璇濇

---

### Phase 3: 鍚庣API瀹炵幇 鉁?

**淇敼鏂囦欢**锛?
- `data_management/views.py`
- `data_management/urls.py`

#### 3.1 鏂板API瑙嗗浘
```python
class RealtimeDetectionView(APIView):
    """
    瀹炴椂妫€娴婣PI - 绠€鍖栫増
    鎺ユ敹鏂囦欢涓婁紶锛屾墽琛屾娴嬶紝鐩存帴杩斿洖鍐呭瓨涓殑妫€娴嬬粨鏋?
    """
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser]
    
    def post(self, request: Request) -> Response:
        # 楠岃瘉鍙傛暟銆佷繚瀛樻枃浠躲€佹墽琛屾娴嬨€佽繑鍥炵粨鏋?
```

**绔偣璺緞**锛歚/api/v1/data/realtime-detection/`

**璇锋眰鍙傛暟**锛?
- `file` - 涓婁紶鐨勬枃浠讹紙CSV鎴朎xcel锛?
- `cmg_id` - PHM ID
- `detection_mode` - 妫€娴嬫ā寮忥紙full/ims_only/rule_only/msfg_only锛?
- `save_results` - 鏄惁淇濆瓨鍒版暟鎹簱锛坱rue/false锛?
- `return_memory_results` - 鏄惁杩斿洖璇︾粏缁撴灉锛坱rue/false锛?

**鍝嶅簲鏍煎紡**锛?
```json
{
  "success": true,
  "message": "妫€娴嬪畬鎴?,
  "results": {
    "total_frames": 1000,
    "anomaly_count": 50,
    "anomaly_ratio": 0.05,
    "anomaly_frames": [...],
    "frame_details": [...],
    "component_health": {...},
    "overall_health": 0.85
  }
}
```

---

### Phase 4: batch_processing鎵╁睍 鉁?

**淇敼鏂囦欢**锛歚data_management/batch_processing.py`

#### 4.1 鏂板鍏叡鏂规硶
```python
def process_file_for_detection(
    self, 
    file_path: str, 
    cmg: PHM, 
    detection_mode: str = 'full',
    save_to_db: bool = False,
    return_details: bool = True
) -> Dict[str, Any]:
```

#### 4.2 鏂板杈呭姪鏂规硶锛堝叡8涓級
1. `_parse_file_by_path()` - 閫氳繃鏂囦欢璺緞瑙ｆ瀽鏂囦欢
2. `_parse_csv_by_path()` - 瑙ｆ瀽CSV鏂囦欢
3. `_parse_excel_by_path()` - 瑙ｆ瀽Excel鏂囦欢
4. `_run_detection_for_record()` - 涓哄崟鏉¤褰曟墽琛屾娴?
5. `_save_detection_to_db()` - 淇濆瓨妫€娴嬬粨鏋滃埌鏁版嵁搴?
6. `_aggregate_component_health()` - 鑱氬悎閮ㄤ欢鍋ュ悍搴?
7. `_calculate_overall_health()` - 璁＄畻鏁翠綋鍋ュ悍搴?

**妫€娴嬫祦绋?*锛?
```
瑙ｆ瀽鏂囦欢 鈫?閫愭潯妫€娴?鈫?鏀堕泦缁撴灉 鈫?鑱氬悎鏁版嵁 鈫?杩斿洖缁撴灉
```

---

## 馃幆 鍏抽敭璁捐鐗规€?

### 1. 鍙屾ā寮忔敮鎸?
- **鍘嗗彶妯″紡**锛氫繚鐣欏師鏈夊姛鑳斤紝浠庢暟鎹簱璇诲彇
- **涓婁紶妯″紡**锛氱洿鎺ヤ娇鐢ㄥ唴瀛樼粨鏋滐紝鏃犻渶鏁版嵁搴?

### 2. 闃诲閫昏緫
- 蹇呴』鍏堥€夋嫨妯″紡鎵嶈兘閫夋嫨PHM鍨嬪彿
- `:disabled="!selectedMode"` 瀹炵幇UI灞傞潰鐨勯樆濉?

### 3. 妯″紡鍖哄垎
```javascript
if (selectedMode.value === 'history') {
  openTimeSelectDialog();  // 寮瑰嚭鏃堕棿閫夋嫨
} else if (selectedMode.value === 'upload') {
  openFileUploadDialog();  // 寮瑰嚭鏂囦欢涓婁紶
}
```

### 4. 鍐呭瓨缁撴灉浣跨敤
```javascript
// 涓婁紶妯″紡锛氫娇鐢ㄥ唴瀛樼粨鏋?
memoryDetectionResults.value = data.results;
updateDisplayFromMemory(data.results);

// 鍘嗗彶妯″紡锛氫粠鏁版嵁搴撹鍙?
await fetchAnomalyResults(selectedCmg.id, startTime, endTime);
```

### 5. 鏈€灏忓寲鏀瑰姩
- 鉁?UI鍙噸鎺掞紝涓嶉噸鏋?
- 鉁?澶嶇敤鐜版湁鐨勬樉绀虹粍浠?
- 鉁?澶嶇敤batch_processing鐨勬娴嬮€昏緫
- 鉁?鏃犻渶WebSocket锛屽悓姝ュ鐞?

---

## 馃搳 淇敼缁熻

### 鍓嶇淇敼
```
frontend/src/views/DetectionOverview.vue
  - 鎿嶄綔姝ラ鎻愮ず锛?琛?
  - UI缁撴瀯璋冩暣锛?0琛?
  - 鏂板瀵硅瘽妗嗭細100琛?
  - 鏂板鐘舵€佸彉閲忥細15琛?
  - 鏂板鍑芥暟锛?00琛?
  - 淇敼鐜版湁鍑芥暟锛?0琛?
  鎬昏锛氱害380琛?
```

### 鍚庣淇敼
```
data_management/views.py
  - 鏂板RealtimeDetectionView锛?0琛?

data_management/urls.py
  - 瀵煎叆鍜孶RL閰嶇疆锛?琛?

data_management/batch_processing.py
  - 鏂板鍏叡鏂规硶锛?0琛?
  - 鏂板杈呭姪鏂规硶锛?50琛?
  鎬昏锛氱害240琛?
```

---

## 鉁?娴嬭瘯娓呭崟

### 鍓嶇娴嬭瘯
- [ ] 妯″紡閫夋嫨涓嬫媺妗嗘甯告樉绀?
- [ ] 鏈€夋嫨妯″紡鏃讹紝PHM鍨嬪彿閫夋嫨琚鐢?
- [ ] 鍘嗗彶妯″紡锛氱偣鍑籆MG鍗＄墖寮瑰嚭鏃堕棿閫夋嫨
- [ ] 涓婁紶妯″紡锛氱偣鍑籆MG鍗＄墖寮瑰嚭鏂囦欢涓婁紶
- [ ] 鏂囦欢涓婁紶锛氭嫋鎷藉拰鐐瑰嚮涓婁紶閮芥甯?
- [ ] 妫€娴嬭繘搴︽潯姝ｅ父鏄剧ず
- [ ] 妫€娴嬪畬鎴愬悗缁撴灉姝ｇ‘鏄剧ず

### 鍚庣娴嬭瘯
- [ ] `/api/v1/data/realtime-detection/` 绔偣鍙闂?
- [ ] 鏂囦欢涓婁紶姝ｅ父澶勭悊
- [ ] CSV鏂囦欢瑙ｆ瀽姝ｇ‘
- [ ] Excel鏂囦欢瑙ｆ瀽姝ｇ‘
- [ ] IMS妫€娴嬫甯告墽琛?
- [ ] 瑙勫垯妫€娴嬫甯告墽琛?
- [ ] MSFG妫€娴嬫甯告墽琛?
- [ ] 妫€娴嬬粨鏋滄牸寮忔纭?

### 闆嗘垚娴嬭瘯
- [ ] 瀹屾暣妫€娴嬫祦绋嬶紙浠庝笂浼犲埌鏄剧ず锛?
- [ ] 鍘嗗彶妯″紡鍜屼笂浼犳ā寮忓垏鎹?
- [ ] 閿欒澶勭悊锛堟枃浠舵牸寮忎笉鏀寔銆丆MG涓嶅瓨鍦ㄧ瓑锛?
- [ ] 澶ф枃浠跺鐞嗭紙1000+鏉℃暟鎹級

---

## 馃摑 浣跨敤璇存槑

### 鍘嗗彶妯″紡浣跨敤娴佺▼
```
1. 閫夋嫨"鏌ョ湅鍘嗗彶缁撴灉"
2. 閫夋嫨PHM鍨嬪彿
3. 鐐瑰嚮PHM涓綋鍗＄墖
4. 鍦ㄥ脊鍑哄璇濇涓€夋嫨鏃堕棿鑼冨洿
5. 鏌ョ湅鍘嗗彶妫€娴嬬粨鏋?
```

### 涓婁紶妯″紡浣跨敤娴佺▼
```
1. 閫夋嫨"涓婁紶鏂囦欢妫€娴?
2. 閫夋嫨PHM鍨嬪彿
3. 鐐瑰嚮PHM涓綋鍗＄墖
4. 鍦ㄥ脊鍑哄璇濇涓笂浼犳枃浠?
5. 閰嶇疆妫€娴嬪弬鏁帮紙妫€娴嬫ā寮忋€佹槸鍚︿繚瀛橈級
6. 鐐瑰嚮"寮€濮嬫娴?
7. 绛夊緟妫€娴嬪畬鎴?
8. 鏌ョ湅瀹炴椂妫€娴嬬粨鏋?
```

---

## 馃殌 閮ㄧ讲璇存槑

### 鍓嶇閮ㄧ讲
```bash
cd frontend
npm run build
```

### 鍚庣閮ㄧ讲
```bash
# 鏃犻渶杩佺Щ锛屽彧闇€閲嶅惎鏈嶅姟
python manage.py runserver
```

### 渚濊禆妫€鏌?
- 鉁?鏃犳柊澧濸ython渚濊禆
- 鉁?鏃犳柊澧濶ode.js渚濊禆
- 鉁?浣跨敤鐜版湁鐨凞jango REST Framework
- 鉁?浣跨敤鐜版湁鐨凟lement Plus缁勪欢

---

## 鈿狅笍 娉ㄦ剰浜嬮」

1. **鏂囦欢澶у皬闄愬埗**
   - 鍓嶇闄愬埗锛?00MB
   - 鍙湪`fileUploadDialogVisible`瀵硅瘽妗嗙殑tip涓慨鏀?

2. **妫€娴嬫€ц兘**
   - 1000鏉℃暟鎹害闇€10-30绉?
   - 寤鸿娣诲姞杩涘害鍙嶉鏈哄埗

3. **鍐呭瓨绠＄悊**
   - 妫€娴嬪畬鎴愬悗鑷姩娓呯悊涓存椂鏂囦欢
   - 澶ф枃浠跺缓璁垎鎵瑰鐞?

4. **鏁版嵁鏍煎紡**
   - CSV锛歎TF-8缂栫爜锛岄琛屼负琛ㄥご
   - Excel锛氶琛屼负琛ㄥご锛屾敮鎸亁lsx鍜寈ls鏍煎紡

---

## 馃帀 瀹屾垚鐘舵€?

鉁?**Phase 1**: 鍓嶇UI鏀归€? 
鉁?**Phase 2**: 鍓嶇閫昏緫鏀归€? 
鉁?**Phase 3**: 鍚庣API瀹炵幇  
鉁?**Phase 4**: batch_processing鎵╁睍  
鉁?**璇硶妫€鏌?*: 鏃犻敊璇? 
鈴?**娴嬭瘯楠岃瘉**: 寰呯敤鎴锋祴璇? 

---

**瀹炴柦瀹屾垚鏃堕棿**锛?025-10-10  
**瀹炴柦浜哄憳**锛欰I Assistant  
**浠ｇ爜璐ㄩ噺**锛氣渽 閫氳繃璇硶妫€鏌? 
**鏂囨。瀹屾暣鎬?*锛氣渽 瀹屾暣  
**閮ㄧ讲灏辩华**锛氣渽 灏辩华




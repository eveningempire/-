# 妫€娴嬬粨鏋滄€昏椤甸潰绠€鍖栧崌绾ф柟妗?

## 馃幆 璁捐鍘熷垯
- **鏈€灏忓寲浠ｇ爜鏀瑰姩**
- **澶嶇敤鐜版湁閫昏緫**
- **鐩磋鐨勭敤鎴蜂綋楠?*

---

## 馃搵 UI鏀归€犳柟妗?

### 淇敼鍓嶇殑甯冨眬
```
[PHM鍨嬪彿閫夋嫨妗哴  [鏃堕棿閫夋嫨鎸夐挳]
```

### 淇敼鍚庣殑甯冨眬
```
[妯″紡閫夋嫨妗哴     [PHM鍨嬪彿閫夋嫨妗哴
```

---

## 馃攧 浜や簰娴佺▼

### 娴佺▼1锛氭煡鐪嬪巻鍙茬粨鏋滄ā寮?
```
1. 閫夋嫨妯″紡锛氭煡鐪嬪巻鍙茬粨鏋?
   鈫?
2. 閫夋嫨PHM鍨嬪彿锛堜笅鎷夋鍙敤锛?
   鈫?
3. 鐐瑰嚮PHM涓綋鍗＄墖
   鈫?
4. 寮瑰嚭鏃堕棿閫夋嫨瀵硅瘽妗?
   鈫?
5. 閫夋嫨鏃堕棿鑼冨洿
   鈫?
6. 浠庢暟鎹簱璇诲彇缁撴灉骞舵樉绀?
```

### 娴佺▼2锛氫笂浼犳枃浠舵娴嬫ā寮?
```
1. 閫夋嫨妯″紡锛氫笂浼犳枃浠舵娴?
   鈫?
2. 閫夋嫨PHM鍨嬪彿锛堜笅鎷夋鍙敤锛?
   鈫?
3. 鐐瑰嚮PHM涓綋鍗＄墖
   鈫?
4. 寮瑰嚭鏂囦欢涓婁紶瀵硅瘽妗?
   鈫?
5. 涓婁紶鏂囦欢
   鈫?
6. 鎵цbatch_processing妫€娴?
   鈫?
7. 鐩存帴浣跨敤鍐呭瓨涓殑缁撴灉鏄剧ず锛堜笉璇绘暟鎹簱锛?
```

---

## 馃捇 浠ｇ爜瀹炵幇

### 1. 鍓嶇Template淇敼

```vue
<!-- 淇敼actions-container閮ㄥ垎 -->
<div class="actions-container">
  <!-- 妯″紡閫夋嫨 -->
  <div class="mode-selection">
    <el-select 
      v-model="selectedMode" 
      placeholder="璇烽€夋嫨鎿嶄綔妯″紡" 
      style="width: 100%;"
      @change="onModeChange"
      size="small"
    >
      <el-option label="鏌ョ湅鍘嗗彶缁撴灉" value="history" />
      <el-option label="涓婁紶鏂囦欢妫€娴? value="upload" />
    </el-select>
  </div>
  
  <!-- PHM鍨嬪彿閫夋嫨 -->
  <div class="cmg-selection">
    <el-select 
      v-model="selectedCmgModel" 
      placeholder="璇烽€夋嫨PHM鍨嬪彿" 
      style="width: 100%;"
      @change="onModelChange"
      size="small"
      :disabled="!selectedMode"
    >
      <el-option
        v-for="model in cmgModels"
        :key="model.value"
        :label="model.label"
        :value="model.value"
      />
    </el-select>
  </div>
</div>

<!-- 淇敼placeholder鎻愮ず -->
<div v-else class="placeholder-text">
  <div class="placeholder-content">
    <el-icon size="60" color="#c0c4cc"><DataAnalysis /></el-icon>
    <span v-if="!selectedMode">璇峰厛閫夋嫨鎿嶄綔妯″紡</span>
    <span v-else>璇烽€夋嫨涓€涓狢MG鍨嬪彿</span>
  </div>
</div>

<!-- 鏂板锛氭椂闂撮€夋嫨瀵硅瘽妗嗭紙鍘嗗彶妯″紡锛?-->
<el-dialog
  v-model="timeSelectDialogVisible"
  title="閫夋嫨鏃堕棿鑼冨洿"
  width="500px"
>
  <el-date-picker
    v-model="timeRange"
    type="datetimerange"
    range-separator="鑷?
    start-placeholder="寮€濮嬫椂闂?
    end-placeholder="缁撴潫鏃堕棿"
    style="width: 100%;"
  />
  
  <template #footer>
    <el-button @click="timeSelectDialogVisible = false">鍙栨秷</el-button>
    <el-button type="primary" @click="confirmTimeSelection" :disabled="!timeRange">
      纭畾
    </el-button>
  </template>
</el-dialog>

<!-- 鏂板锛氭枃浠朵笂浼犲璇濇锛堜笂浼犳ā寮忥級 -->
<el-dialog
  v-model="fileUploadDialogVisible"
  title="涓婁紶鏂囦欢杩涜妫€娴?
  width="600px"
>
  <el-upload
    ref="uploadRef"
    :auto-upload="false"
    :on-change="handleFileChange"
    :limit="1"
    accept=".csv,.xlsx,.xls"
    drag
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">
      鎷栨嫿鏂囦欢鍒版澶勬垨 <em>鐐瑰嚮涓婁紶</em>
    </div>
    <template #tip>
      <div class="el-upload__tip">
        鏀寔 CSV 鎴?Excel 鏍煎紡锛屽崟娆℃渶澶?00MB
      </div>
    </template>
  </el-upload>

  <!-- 妫€娴嬮厤缃?-->
  <el-form :model="detectionConfig" label-width="120px" style="margin-top: 20px;">
    <el-form-item label="妫€娴嬫ā寮?>
      <el-select v-model="detectionConfig.mode" placeholder="璇烽€夋嫨妫€娴嬫ā寮?>
        <el-option label="瀹屾暣妫€娴嬶紙IMS+瑙勫垯+MSFG锛? value="full" />
        <el-option label="浠匢MS妫€娴? value="ims_only" />
        <el-option label="浠呰鍒欐娴? value="rule_only" />
        <el-option label="浠匨SFG妫€娴? value="msfg_only" />
      </el-select>
    </el-form-item>

    <el-form-item label="鏄惁淇濆瓨缁撴灉">
      <el-switch v-model="detectionConfig.saveResults" />
      <span style="margin-left: 10px; color: #909399; font-size: 12px;">
        淇濆瓨鍒版暟鎹簱浠ヤ究鍚庣画鏌ヨ
      </span>
    </el-form-item>
  </el-form>

  <!-- 杩涘害鏄剧ず -->
  <div v-if="isDetecting" class="detection-progress">
    <el-progress :percentage="detectionProgress" :status="detectionStatus" />
    <p style="margin-top: 10px; text-align: center;">{{ detectionMessage }}</p>
  </div>

  <template #footer>
    <el-button @click="fileUploadDialogVisible = false" :disabled="isDetecting">
      鍙栨秷
    </el-button>
    <el-button 
      type="primary" 
      @click="startDetection" 
      :disabled="!uploadedFile || isDetecting"
      :loading="isDetecting"
    >
      {{ isDetecting ? '妫€娴嬩腑...' : '寮€濮嬫娴? }}
    </el-button>
  </template>
</el-dialog>
```

### 2. 鍓嶇Script淇敼

```javascript
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus';

// 鏂板鐘舵€?
const selectedMode = ref(''); // 'history' 鎴?'upload'
const timeSelectDialogVisible = ref(false);
const fileUploadDialogVisible = ref(false);
const uploadedFile = ref(null);
const detectionConfig = reactive({
  mode: 'full',
  saveResults: false  // 榛樿涓嶄繚瀛?
});
const isDetecting = ref(false);
const detectionProgress = ref(0);
const detectionStatus = ref('');
const detectionMessage = ref('');

// 鍐呭瓨涓殑妫€娴嬬粨鏋滐紙鐢ㄤ簬涓婁紶妯″紡锛?
const memoryDetectionResults = ref(null);

// 淇敼锛氭ā寮忛€夋嫨鍙樺寲
function onModeChange() {
  // 娓呯┖涔嬪墠鐨勯€夋嫨
  selectedCmgModel.value = null;
  selectedCmgId.value = null;
  cmgInstances.value = [];
  memoryDetectionResults.value = null;
  
  // 娓呯┖鏄剧ず鐨勬暟鎹?
  anomalyRatio.value = 0;
  totalFrames.value = 0;
  anomalyCount.value = 0;
  anomalyFrames.value = [];
  
  ElMessage.info(`宸插垏鎹㈠埌${selectedMode.value === 'history' ? '鍘嗗彶鏌ヨ' : '鏂囦欢妫€娴?}妯″紡`);
}

// 淇敼锛欳MG涓綋閫夋嫨
function selectCmg(id) {
  console.log('閫夋嫨PHM涓綋锛宨d:', id, '褰撳墠妯″紡:', selectedMode.value);
  selectedCmgId.value = id;
  
  // 鏍规嵁妯″紡鍐冲畾鍚庣画鎿嶄綔
  if (selectedMode.value === 'history') {
    // 鍘嗗彶妯″紡锛氬脊鍑烘椂闂撮€夋嫨瀵硅瘽妗?
    openTimeSelectDialog();
  } else if (selectedMode.value === 'upload') {
    // 涓婁紶妯″紡锛氬脊鍑烘枃浠朵笂浼犲璇濇
    openFileUploadDialog();
  } else {
    ElMessage.warning('璇峰厛閫夋嫨鎿嶄綔妯″紡');
  }
}

// 鏂板锛氭墦寮€鏃堕棿閫夋嫨瀵硅瘽妗?
function openTimeSelectDialog() {
  timeRange.value = null;
  timeSelectDialogVisible.value = true;
}

// 鏂板锛氱‘璁ゆ椂闂撮€夋嫨
async function confirmTimeSelection() {
  if (!timeRange.value || timeRange.value.length !== 2) {
    ElMessage.warning('璇烽€夋嫨鏃堕棿鑼冨洿');
    return;
  }
  
  timeSelectDialogVisible.value = false;
  hasSelectedCmgAndTime.value = true;
  
  // 璋冪敤鍘熸湁鐨勫姞杞芥暟鎹€昏緫
  await loadHistoryData();
}

// 鏂板锛氬姞杞藉巻鍙叉暟鎹紙鍘熸湁閫昏緫锛?
async function loadHistoryData() {
  if (!selectedCmgId.value || !timeRange.value) {
    return;
  }
  
  try {
    const selectedCmg = cmgInstances.value.find(cmg => cmg.id === selectedCmgId.value);
    if (!selectedCmg) {
      ElMessage.error('鏈壘鍒伴€変腑鐨凜MG涓綋');
      return;
    }
    
    const startTime = timeRange.value[0].toISOString();
    const endTime = timeRange.value[1].toISOString();
    
    // 璋冪敤鐜版湁鐨凙PI鑾峰彇鏁版嵁
    await fetchAnomalyResults(selectedCmg.id, startTime, endTime);
    
    ElMessage.success('鍘嗗彶鏁版嵁鍔犺浇瀹屾垚');
  } catch (error) {
    console.error('鍔犺浇鍘嗗彶鏁版嵁澶辫触:', error);
    ElMessage.error('鍔犺浇鍘嗗彶鏁版嵁澶辫触');
  }
}

// 鏂板锛氭墦寮€鏂囦欢涓婁紶瀵硅瘽妗?
function openFileUploadDialog() {
  uploadedFile.value = null;
  detectionProgress.value = 0;
  detectionStatus.value = '';
  detectionMessage.value = '';
  isDetecting.value = false;
  fileUploadDialogVisible.value = true;
}

// 鏂板锛氭枃浠堕€夋嫨澶勭悊
function handleFileChange(file) {
  uploadedFile.value = file.raw;
  console.log('閫夋嫨鐨勬枃浠?', file.name, '澶у皬:', file.size);
}

// 鏂板锛氬紑濮嬫娴?
async function startDetection() {
  if (!uploadedFile.value) {
    ElMessage.warning('璇峰厛涓婁紶鏂囦欢');
    return;
  }
  
  if (!selectedCmgId.value) {
    ElMessage.warning('璇峰厛閫夋嫨PHM涓綋');
    return;
  }
  
  try {
    isDetecting.value = true;
    detectionProgress.value = 0;
    detectionStatus.value = 'active';
    detectionMessage.value = '姝ｅ湪涓婁紶鏂囦欢...';
    
    // 鏋勫缓FormData
    const formData = new FormData();
    formData.append('file', uploadedFile.value);
    formData.append('cmg_id', selectedCmgId.value);
    formData.append('detection_mode', detectionConfig.mode);
    formData.append('save_results', detectionConfig.saveResults);
    formData.append('return_memory_results', 'true'); // 鍏抽敭锛氳姹傝繑鍥炲唴瀛樼粨鏋?
    
    // 璋冪敤鍚庣API
    detectionMessage.value = '姝ｅ湪鎵ц妫€娴?..';
    detectionProgress.value = 10;
    
    const response = await fetch('/api/v1/data/realtime-detection/', {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    detectionProgress.value = 90;
    const data = await response.json();
    
    // 鍏抽敭锛氱洿鎺ヤ娇鐢ㄨ繑鍥炵殑鍐呭瓨缁撴灉
    memoryDetectionResults.value = data.results;
    
    // 鏇存柊鏄剧ず鏁版嵁锛堜笉浠庢暟鎹簱璇诲彇锛?
    updateDisplayFromMemory(data.results);
    
    detectionProgress.value = 100;
    detectionStatus.value = 'success';
    detectionMessage.value = '妫€娴嬪畬鎴愶紒';
    
    ElMessage.success(`妫€娴嬪畬鎴愶紒鍏卞鐞?${data.results.total_frames} 甯ф暟鎹紝妫€娴嬪埌 ${data.results.anomaly_count} 涓紓甯竊);
    
    // 寤惰繜鍏抽棴瀵硅瘽妗?
    setTimeout(() => {
      fileUploadDialogVisible.value = false;
      isDetecting.value = false;
      hasSelectedCmgAndTime.value = true; // 鏍囪涓哄凡鏈夋暟鎹?
    }, 1500);
    
  } catch (error) {
    console.error('妫€娴嬪け璐?', error);
    ElMessage.error('妫€娴嬪け璐? ' + error.message);
    detectionStatus.value = 'exception';
    detectionMessage.value = '妫€娴嬪け璐?;
    isDetecting.value = false;
  }
}

// 鏂板锛氫粠鍐呭瓨缁撴灉鏇存柊鏄剧ず
function updateDisplayFromMemory(results) {
  console.log('浠庡唴瀛樻洿鏂版樉绀烘暟鎹?', results);
  
  // 鏇存柊寮傚父妫€娴嬬粨鏋?
  anomalyRatio.value = results.anomaly_ratio || 0;
  totalFrames.value = results.total_frames || 0;
  anomalyCount.value = results.anomaly_count || 0;
  anomalyFrames.value = results.anomaly_frames || [];
  
  // 鏇存柊閮ㄤ欢鍋ュ悍鐘舵€侊紙濡傛灉鏈夛級
  if (results.component_health) {
    // 灏嗗唴瀛樹腑鐨勯儴浠跺仴搴锋暟鎹浆鎹负鏄剧ず鏍煎紡
    // 娉ㄦ剰锛氶渶瑕佺‘淇濆瓧娈靛悕绉板尮閰?
    // results.component_health 鏍煎紡搴旇涓庝粠鏁版嵁搴撹鍙栫殑鏍煎紡涓€鑷?
  }
  
  // 鏇存柊鏁翠綋鍋ュ悍搴︼紙濡傛灉鏈夛級
  if (results.overall_health !== undefined) {
    // 鏇存柊鏁翠綋鍋ュ悍搴︽樉绀?
  }
  
  console.log('鏄剧ず鏁版嵁鏇存柊瀹屾垚');
}

// 淇敼锛氭樉绀哄紓甯稿抚璇︽儏锛堥渶瑕佸吋瀹逛袱绉嶆ā寮忥級
async function showAnomalyDetails(frame) {
  selectedAnomalyFrame.value = frame;
  detailDialogVisible.value = true;
  
  // 濡傛灉鏄笂浼犳ā寮忥紝鐩存帴浣跨敤鍐呭瓨涓殑鏁版嵁
  if (selectedMode.value === 'upload' && memoryDetectionResults.value) {
    // 浠庡唴瀛樼粨鏋滀腑鏌ユ壘瀵瑰簲鐨勮鎯?
    const frameDetails = memoryDetectionResults.value.frame_details?.find(
      f => f.timestamp === frame.timestamp || f.frame_number === frame.frame_number
    );
    
    if (frameDetails) {
      // 鐩存帴浣跨敤鍐呭瓨涓殑鏁版嵁
      selectedAnomalyFrame.value.ims_details = frameDetails.ims_result;
      selectedAnomalyFrame.value.rule_details = frameDetails.rule_result;
      selectedAnomalyFrame.value.msfg_details = frameDetails.msfg_result;
      return;
    }
  }
  
  // 鍘嗗彶妯″紡锛氳皟鐢ˋPI浠庢暟鎹簱鑾峰彇
  if (selectedMode.value === 'history') {
    // 鍘熸湁鐨凙PI璋冪敤閫昏緫
    const [imsResponse, ruleResponse, msfgResponse] = await Promise.all([
      fetch(`/api/v1/data/detection-overview/?action=ims_details&frame_id=${frame.id}`),
      fetch(`/api/v1/data/detection-overview/?action=rule_details&frame_id=${frame.id}`),
      fetch(`/api/v1/data/detection-overview/?action=msfg_details&frame_id=${frame.id}`)
    ]);
    
    // ... 鍘熸湁鐨勫鐞嗛€昏緫
  }
}
```

---

## 馃敡 鍚庣鏀归€?

### 鏂板API绔偣锛坉ata_management/views.py锛?

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
import tempfile
import os

@api_view(['POST'])
def realtime_detection(request):
    """
    瀹炴椂妫€娴婣PI - 绠€鍖栫増
    鐩存帴杩斿洖鍐呭瓨涓殑妫€娴嬬粨鏋滐紝涓嶄緷璧朩ebSocket
    """
    try:
        # 楠岃瘉鍙傛暟
        if 'file' not in request.FILES:
            return Response({'error': '娌℃湁涓婁紶鏂囦欢'}, status=status.HTTP_400_BAD_REQUEST)
        
        cmg_id = request.data.get('cmg_id')
        if not cmg_id:
            return Response({'error': '缂哄皯PHM ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        detection_mode = request.data.get('detection_mode', 'full')
        save_results = request.data.get('save_results', 'false').lower() == 'true'
        return_memory_results = request.data.get('return_memory_results', 'false').lower() == 'true'
        
        # 鑾峰彇PHM瀵硅薄
        try:
            cmg = PHM.objects.get(id=cmg_id)
        except PHM.DoesNotExist:
            return Response({'error': 'PHM涓嶅瓨鍦?}, status=status.HTTP_404_NOT_FOUND)
        
        # 淇濆瓨涓婁紶鐨勬枃浠跺埌涓存椂鐩綍
        uploaded_file = request.FILES['file']
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_file_path = tmp_file.name
        
        try:
            # 鎵ц妫€娴?
            logger.info(f"寮€濮嬪疄鏃舵娴? PHM={cmg.cmg_id}, 鏂囦欢={uploaded_file.name}, 妯″紡={detection_mode}")
            
            # 璋冪敤batch_processing鐨勬娴嬮€昏緫
            processor = BatchFileProcessor()
            results = processor.process_file_for_detection(
                file_path=tmp_file_path,
                cmg=cmg,
                detection_mode=detection_mode,
                save_to_db=save_results,
                return_details=return_memory_results
            )
            
            logger.info(f"妫€娴嬪畬鎴? 鎬诲抚鏁?{results['total_frames']}, 寮傚父鏁?{results['anomaly_count']}")
            
            return Response({
                'success': True,
                'message': '妫€娴嬪畬鎴?,
                'results': results
            }, status=status.HTTP_200_OK)
            
        finally:
            # 娓呯悊涓存椂鏂囦欢
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
        
    except Exception as e:
        logger.error(f"瀹炴椂妫€娴嬪け璐? {e}", exc_info=True)
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 淇敼batch_processing.py

```python
class BatchFileProcessor:
    """鎵归噺鏂囦欢澶勭悊鍣?""
    
    def process_file_for_detection(
        self, 
        file_path: str, 
        cmg: PHM, 
        detection_mode: str = 'full',
        save_to_db: bool = False,
        return_details: bool = True
    ) -> Dict[str, Any]:
        """
        澶勭悊鏂囦欢骞舵墽琛屾娴?
        
        Args:
            file_path: 鏂囦欢璺緞
            cmg: PHM瀵硅薄
            detection_mode: 妫€娴嬫ā寮?('full', 'ims_only', 'rule_only', 'msfg_only')
            save_to_db: 鏄惁淇濆瓨鍒版暟鎹簱
            return_details: 鏄惁杩斿洖璇︾粏缁撴灉
            
        Returns:
            妫€娴嬬粨鏋滃瓧鍏?
        """
        logger.info(f"寮€濮嬪鐞嗘枃浠? {file_path}")
        
        # 瑙ｆ瀽鏂囦欢
        parsed_data = self._parse_file_by_path(file_path)
        if not parsed_data:
            raise ValueError("鏂囦欢瑙ｆ瀽澶辫触鎴栨棤鏈夋晥鏁版嵁")
        
        total_frames = len(parsed_data)
        logger.info(f"瑙ｆ瀽瀹屾垚锛屽叡 {total_frames} 鏉℃暟鎹?)
        
        # 鍒濆鍖栫粨鏋?
        results = {
            'total_frames': total_frames,
            'anomaly_count': 0,
            'anomaly_ratio': 0.0,
            'anomaly_frames': [],
            'frame_details': [] if return_details else None,
            'component_health': {},
            'overall_health': None
        }
        
        # 閫愭潯鎵ц妫€娴?
        for idx, record in enumerate(parsed_data):
            if idx % 100 == 0:
                logger.info(f"妫€娴嬭繘搴? {idx}/{total_frames}")
            
            # 鎵ц妫€娴?
            detection_result = self._run_detection_for_record(
                record=record,
                cmg=cmg,
                detection_mode=detection_mode
            )
            
            # 鏀堕泦缁撴灉
            is_anomaly = detection_result.get('is_anomaly', False)
            
            if is_anomaly:
                results['anomaly_count'] += 1
                results['anomaly_frames'].append({
                    'frame_number': idx + 1,
                    'timestamp': record.get('timestamp'),
                    'anomaly_type': detection_result.get('anomaly_type'),
                    'severity': detection_result.get('severity', 'medium')
                })
            
            # 淇濆瓨璇︾粏缁撴灉
            if return_details:
                results['frame_details'].append({
                    'frame_number': idx + 1,
                    'timestamp': record.get('timestamp'),
                    'is_anomaly': is_anomaly,
                    'ims_result': detection_result.get('ims_result'),
                    'rule_result': detection_result.get('rule_result'),
                    'msfg_result': detection_result.get('msfg_result')
                })
            
            # 鍙€夛細淇濆瓨鍒版暟鎹簱
            if save_to_db:
                self._save_detection_to_db(cmg, record, detection_result)
        
        # 璁＄畻寮傚父姣斾緥
        results['anomaly_ratio'] = results['anomaly_count'] / total_frames if total_frames > 0 else 0.0
        
        # 濡傛灉鍖呭惈MSFG妫€娴嬶紝姹囨€婚儴浠跺仴搴峰害
        if detection_mode in ['full', 'msfg_only']:
            results['component_health'] = self._aggregate_component_health(results['frame_details'])
            results['overall_health'] = self._calculate_overall_health(results['component_health'])
        
        logger.info(f"妫€娴嬪畬鎴? 寮傚父鐜?{results['anomaly_ratio']:.2%}")
        
        return results
    
    def _run_detection_for_record(
        self, 
        record: Dict, 
        cmg: PHM, 
        detection_mode: str
    ) -> Dict[str, Any]:
        """
        涓哄崟鏉¤褰曟墽琛屾娴?
        
        Returns:
            妫€娴嬬粨鏋滐紝鍖呭惈鍚勬娴嬫ā鍧楃殑缁撴灉
        """
        result = {
            'is_anomaly': False,
            'anomaly_type': [],
            'severity': 'normal',
            'ims_result': None,
            'rule_result': None,
            'msfg_result': None
        }
        
        # IMS妫€娴?
        if detection_mode in ['full', 'ims_only']:
            ims_result = run_ims_detection(record)
            result['ims_result'] = ims_result
            
            if ims_result.get('is_anomaly'):
                result['is_anomaly'] = True
                result['anomaly_type'].append('ims')
                result['severity'] = max(result['severity'], ims_result.get('severity', 'medium'))
        
        # 瑙勫垯妫€娴?
        if detection_mode in ['full', 'rule_only']:
            rule_result = evaluate_rules_for_data_point(record, cmg)
            result['rule_result'] = rule_result
            
            if rule_result.get('has_violation'):
                result['is_anomaly'] = True
                result['anomaly_type'].append('rule')
                result['severity'] = max(result['severity'], rule_result.get('severity', 'medium'))
        
        # MSFG妫€娴?
        if detection_mode in ['full', 'msfg_only']:
            msfg_result = self._run_msfg_detection(record, cmg)
            result['msfg_result'] = msfg_result
            
            if msfg_result.get('has_fault'):
                result['is_anomaly'] = True
                result['anomaly_type'].append('msfg')
                result['severity'] = max(result['severity'], msfg_result.get('severity', 'medium'))
        
        return result
    
    def _aggregate_component_health(self, frame_details: List[Dict]) -> Dict[str, Dict]:
        """
        浠庡抚璇︽儏涓仛鍚堥儴浠跺仴搴峰害
        """
        if not frame_details:
            return {}
        
        # 鏀堕泦鎵€鏈夊抚鐨凪SFG缁撴灉
        component_scores = {}
        
        for frame in frame_details:
            msfg_result = frame.get('msfg_result')
            if not msfg_result or not msfg_result.get('component_health'):
                continue
            
            for comp_name, comp_data in msfg_result['component_health'].items():
                if comp_name not in component_scores:
                    component_scores[comp_name] = []
                component_scores[comp_name].append(comp_data.get('health_score', 1.0))
        
        # 璁＄畻骞冲潎鍋ュ悍搴?
        component_health = {}
        for comp_name, scores in component_scores.items():
            avg_score = sum(scores) / len(scores) if scores else 1.0
            component_health[comp_name] = {
                'name': comp_name,
                'health_score': round(avg_score, 3),
                'status': 'healthy' if avg_score >= 0.7 else 'warning' if avg_score >= 0.5 else 'critical',
                'sample_count': len(scores)
            }
        
        return component_health
    
    def _calculate_overall_health(self, component_health: Dict) -> float:
        """璁＄畻鏁翠綋鍋ュ悍搴?""
        if not component_health:
            return 1.0
        
        scores = [comp['health_score'] for comp in component_health.values()]
        return round(sum(scores) / len(scores), 3) if scores else 1.0
```

---

## 馃攽 鍏抽敭鐐?

### 1. 鏁版嵁瀛楁瀵瑰簲
纭繚batch_processing杩斿洖鐨勭粨鏋滄牸寮忎笌浠庢暟鎹簱璇诲彇鐨勬牸寮忎竴鑷达細

```python
# 鏁版嵁搴撴牸寮忥紙鍘嗗彶妯″紡锛?
{
    'total_frames': 1000,
    'anomaly_count': 50,
    'anomaly_ratio': 0.05,
    'anomaly_frames': [
        {
            'id': 123,  # 鏁版嵁搴揑D
            'frame_number': 10,
            'timestamp': '2025-10-10T10:00:00Z',
            'anomaly_type': 'ims',
            'severity': 'high'
        }
    ]
}

# 鍐呭瓨鏍煎紡锛堜笂浼犳ā寮忥級
{
    'total_frames': 1000,
    'anomaly_count': 50,
    'anomaly_ratio': 0.05,
    'anomaly_frames': [
        {
            # 'id': None,  # 鏃犳暟鎹簱ID
            'frame_number': 10,
            'timestamp': '2025-10-10T10:00:00Z',
            'anomaly_type': 'ims',
            'severity': 'high'
        }
    ],
    'frame_details': [...]  # 棰濆鐨勮缁嗕俊鎭?
}
```

### 2. 妯″紡鍖哄垎
鍦ㄦ墍鏈夐渶瑕佹暟鎹殑鍦版柟锛屾鏌ュ綋鍓嶆ā寮忥細
- `selectedMode.value === 'history'` 鈫?璋冪敤API浠庢暟鎹簱璇诲彇
- `selectedMode.value === 'upload'` 鈫?浣跨敤 `memoryDetectionResults.value`

### 3. 鏈€灏忓寲鏀瑰姩
- 鉁?澶嶇敤鐜版湁鐨勬樉绀虹粍浠跺拰鏍峰紡
- 鉁?澶嶇敤鐜版湁鐨勬娴嬮€昏緫锛坆atch_processing.py锛?
- 鉁?鍙慨鏀规暟鎹潵婧愶紝涓嶄慨鏀规暟鎹鐞嗘柟寮?

---

## 鉁?浼樺娍

1. **浠ｇ爜鏀瑰姩鏈€灏?* - 涓昏鏄疷I閲嶆帓鍜屾暟鎹潵婧愬垏鎹?
2. **鐢ㄦ埛浣撻獙娓呮櫚** - 妯″紡閫夋嫨浼樺厛锛屾祦绋嬬畝鍗?
3. **鏃犻渶WebSocket** - 鍚屾澶勭悊锛岀畝鍖栧疄鐜?
4. **瀹屽叏澶嶇敤閫昏緫** - batch_processing.py鏍稿績閫昏緫涓嶅彉

---

**鏂囨。鍒涘缓鏃ユ湡**锛?025-10-10  
**鏂规绫诲瀷**锛氱畝鍖栧崌绾ф柟妗堬紙鎺ㄨ崘锛?



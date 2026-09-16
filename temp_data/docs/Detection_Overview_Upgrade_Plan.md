# 妫€娴嬬粨鏋滄€昏椤甸潰鍗囩骇鏂规

## 馃搵 褰撳墠閫昏緫鍒嗘瀽

### 现有流程（只读模式）
```
1. 用户选择PHM型号
   鈫?
2. 鐢ㄦ埛閫夋嫨PHM涓綋
   鈫?
3. 鐢ㄦ埛閫夋嫨鏃堕棿娈?
   鈫?
4. 鍓嶇璋冪敤API璇诲彇宸插瓨鍌ㄧ殑妫€娴嬬粨鏋?
   鈫?
5. 鏄剧ず妫€娴嬬粨鏋滐紙寮傚父妫€娴嬨€侀儴浠跺仴搴枫€丮SFG鎺ㄧ悊绛夛級
```

### 鍏抽敭API绔偣锛坉ata_management/views.py锛?
- **`detection-overview/`** - 妫€娴嬬粨鏋滄€昏API
  - `action=anomaly_results` - 鑾峰彇寮傚父妫€娴嬬粨鏋?
  - `action=ims_details` - 鑾峰彇IMS妫€娴嬭鎯?
  - `action=rule_details` - 鑾峰彇瑙勫垯妫€娴嬭鎯?
  - `action=msfg_details` - 鑾峰彇MSFG妫€娴嬭鎯?
  - `action=component_details` - 获取部件详细信息
  - `action=telemetry_data` - 鑾峰彇閬ユ祴鏁版嵁

### 鏁版嵁鏉ユ簮
- **鏁版嵁搴撲腑鐨勫巻鍙叉暟鎹?*
  - `PHMData` - 鍘熷閬ユ祴鏁版嵁
  - `IMSResult` - IMS妫€娴嬬粨鏋?
  - `RuleDetectionResult` - 瑙勫垯妫€娴嬬粨鏋?
  - `MSFGAnalysisResult` - MSFG分析结果

---

## 馃殌 鍗囩骇闇€姹?

### 新增流程（实时检测模式）
```
1. 用户选择PHM型号
   鈫?
2. 鐢ㄦ埛閫夋嫨PHM涓綋
   鈫?
3. 鐢ㄦ埛涓婁紶鏁版嵁鏂囦欢锛圕SV/Excel锛?
   鈫?
4. 鍚庣璋冪敤batch_processing.py鎵ц瀹炴椂妫€娴?
   鈫?
5. 瀹炴椂鍙嶉妫€娴嬭繘搴︼紙WebSocket锛?
   鈫?
6. 妫€娴嬪畬鎴愶紝鑷姩鏄剧ず缁撴灉
   鈫?
7. 结果保存到数据库（可选）
```

---

## 馃幆 瀹炵幇鏂规

### 鏂规鏋舵瀯

#### 1. 鍓嶇鏀归€狅紙DetectionOverview.vue锛?

**鏂板UI缁勪欢锛?*
```vue
<template>
  <!-- 鍦ㄦ椂闂撮€夋嫨鎸夐挳鏃佽竟娣诲姞"瀹炴椂妫€娴?鎸夐挳 -->
  <div class="actions-container">
    <!-- 鍘熸湁鐨勬椂闂撮€夋嫨鎸夐挳 -->
    <el-button 
      type="primary" 
      :icon="Calendar" 
      @click="openTimeSelector"
    >
      鍘嗗彶鏁版嵁鏌ヨ
    </el-button>
    
    <!-- 鏂板锛氬疄鏃舵娴嬫寜閽?-->
    <el-button 
      type="success" 
      :icon="Upload" 
      @click="openRealtimeDetection"
      :disabled="!selectedCmgId"
    >
      瀹炴椂妫€娴?
    </el-button>
  </div>

  <!-- 新增：实时检测对话框 -->
  <el-dialog
    v-model="realtimeDetectionDialogVisible"
    title="瀹炴椂妫€娴?
    width="600px"
  >
    <div class="realtime-detection-container">
      <!-- 姝ラ鎸囩ず鍣?-->
      <el-steps :active="currentStep" finish-status="success">
        <el-step title="涓婁紶鏂囦欢" />
        <el-step title="配置参数" />
        <el-step title="鎵ц妫€娴? />
        <el-step title="查看结果" />
      </el-steps>

      <!-- 姝ラ1: 鏂囦欢涓婁紶 -->
      <div v-if="currentStep === 0" class="step-content">
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

        <el-form :model="detectionConfig" label-width="120px" style="margin-top: 20px;">
          <el-form-item label="妫€娴嬫ā寮?>
            <el-select v-model="detectionConfig.mode" placeholder="璇烽€夋嫨妫€娴嬫ā寮?>
              <el-option label="瀹屾暣妫€娴嬶紙IMS+瑙勫垯+MSFG锛? value="full" />
              <el-option label="浠匢MS妫€娴? value="ims_only" />
              <el-option label="浠呰鍒欐娴? value="rule_only" />
              <el-option label="浠匨SFG妫€娴? value="msfg_only" />
            </el-select>
          </el-form-item>

          <el-form-item label="是否保存结果">
            <el-switch v-model="detectionConfig.saveResults" />
            <span class="tip-text">保存到数据库以便后续查询</span>
          </el-form-item>
        </el-form>
      </div>

      <!-- 姝ラ2: 鎵ц妫€娴嬶紙杩涘害鏄剧ず锛?-->
      <div v-if="currentStep === 1" class="step-content">
        <div class="progress-container">
          <el-progress 
            :percentage="detectionProgress.percentage" 
            :status="detectionProgress.status"
          />
          <div class="progress-info">
            <p>{{ detectionProgress.message }}</p>
            <p class="progress-details">
              宸插鐞? {{ detectionProgress.processed }} / {{ detectionProgress.total }}
            </p>
          </div>
        </div>

        <!-- 瀹炴椂鏃ュ織 -->
        <div class="detection-log">
          <el-scrollbar height="200px">
            <div v-for="(log, index) in detectionLogs" :key="index" class="log-item">
              <span class="log-time">{{ log.time }}</span>
              <span :class="['log-message', log.level]">{{ log.message }}</span>
            </div>
          </el-scrollbar>
        </div>
      </div>

      <!-- 步骤3: 结果预览 -->
      <div v-if="currentStep === 2" class="step-content">
        <el-result 
          icon="success" 
          title="妫€娴嬪畬鎴? 
          :sub-title="`鍏卞鐞?${detectionResults.totalFrames} 甯ф暟鎹紝妫€娴嬪埌 ${detectionResults.anomalyCount} 涓紓甯竊"
        >
          <template #extra>
            <el-button type="primary" @click="viewDetectionResults">
              查看详细结果
            </el-button>
            <el-button @click="downloadResults">
              涓嬭浇妫€娴嬫姤鍛?
            </el-button>
          </template>
        </el-result>
      </div>
    </div>

    <template #footer>
      <el-button v-if="currentStep === 0" @click="closeRealtimeDetection">
        鍙栨秷
      </el-button>
      <el-button v-if="currentStep === 0" type="primary" @click="startDetection" :disabled="!uploadedFile">
        寮€濮嬫娴?
      </el-button>
      <el-button v-if="currentStep === 2" @click="closeRealtimeDetection">
        鍏抽棴
      </el-button>
    </template>
  </el-dialog>
</template>
```

**鏂板JavaScript閫昏緫锛?*
```javascript
import { ref, reactive } from 'vue';
import { ElMessage } from 'element-plus';

// 瀹炴椂妫€娴嬬浉鍏崇姸鎬?
const realtimeDetectionDialogVisible = ref(false);
const currentStep = ref(0);
const uploadedFile = ref(null);
const detectionConfig = reactive({
  mode: 'full',
  saveResults: true
});
const detectionProgress = reactive({
  percentage: 0,
  status: '',
  message: '鍑嗗寮€濮嬫娴?..',
  processed: 0,
  total: 0
});
const detectionLogs = ref([]);
const detectionResults = ref(null);
let ws = null; // WebSocket杩炴帴

// 鎵撳紑瀹炴椂妫€娴嬪璇濇
function openRealtimeDetection() {
  if (!selectedCmgId.value) {
    ElMessage.warning('璇峰厛閫夋嫨涓€涓狢MG涓綋');
    return;
  }
  realtimeDetectionDialogVisible.value = true;
  currentStep.value = 0;
  uploadedFile.value = null;
  detectionLogs.value = [];
}

// 鍏抽棴瀹炴椂妫€娴嬪璇濇
function closeRealtimeDetection() {
  if (ws) {
    ws.close();
    ws = null;
  }
  realtimeDetectionDialogVisible.value = false;
  currentStep.value = 0;
  uploadedFile.value = null;
}

// 鏂囦欢閫夋嫨澶勭悊
function handleFileChange(file) {
  uploadedFile.value = file.raw;
  console.log('閫夋嫨鐨勬枃浠?', file.name);
}

// 寮€濮嬫娴?
async function startDetection() {
  if (!uploadedFile.value) {
    ElMessage.warning('璇峰厛涓婁紶鏂囦欢');
    return;
  }

  try {
    // 鍒囨崲鍒版娴嬭繘搴︽楠?
    currentStep.value = 1;
    detectionProgress.percentage = 0;
    detectionProgress.status = 'active';
    detectionProgress.message = '姝ｅ湪涓婁紶鏂囦欢...';

    // 鏋勫缓FormData
    const formData = new FormData();
    formData.append('file', uploadedFile.value);
    formData.append('cmg_id', selectedCmgId.value);
    formData.append('detection_mode', detectionConfig.mode);
    formData.append('save_results', detectionConfig.saveResults);

    // 璋冪敤鍚庣API寮€濮嬫娴?
    const response = await fetch('/api/v1/data/realtime-detection/', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const sessionId = data.session_id;

    addLog('info', `妫€娴嬩换鍔″凡鍒涘缓锛屼細璇滻D: ${sessionId}`);

    // 寤虹珛WebSocket杩炴帴鎺ユ敹杩涘害鏇存柊
    connectWebSocket(sessionId);

  } catch (error) {
    console.error('寮€濮嬫娴嬪け璐?', error);
    ElMessage.error('寮€濮嬫娴嬪け璐? ' + error.message);
    detectionProgress.status = 'exception';
    detectionProgress.message = '妫€娴嬪け璐?;
  }
}

// 寤虹珛WebSocket杩炴帴
function connectWebSocket(sessionId) {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/realtime-detection/${sessionId}/`;
  
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket杩炴帴宸插缓绔?);
    addLog('info', 'WebSocket杩炴帴宸插缓绔?);
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    handleProgressUpdate(data);
  };

  ws.onerror = (error) => {
    console.error('WebSocket閿欒:', error);
    addLog('error', 'WebSocket杩炴帴閿欒');
  };

  ws.onclose = () => {
    console.log('WebSocket杩炴帴宸插叧闂?);
  };
}

// 澶勭悊杩涘害鏇存柊
function handleProgressUpdate(data) {
  switch (data.type) {
    case 'progress':
      detectionProgress.percentage = data.percentage;
      detectionProgress.processed = data.processed;
      detectionProgress.total = data.total;
      detectionProgress.message = data.message;
      addLog('info', data.message);
      break;

    case 'status':
      addLog(data.level, data.message);
      break;

    case 'completed':
      detectionProgress.percentage = 100;
      detectionProgress.status = 'success';
      detectionProgress.message = '妫€娴嬪畬鎴愶紒';
      detectionResults.value = data.results;
      addLog('success', '妫€娴嬪畬鎴愶紒');
      
      // 鍒囨崲鍒扮粨鏋滄楠?
      setTimeout(() => {
        currentStep.value = 2;
      }, 1000);
      break;

    case 'error':
      detectionProgress.status = 'exception';
      detectionProgress.message = '妫€娴嬪け璐?;
      addLog('error', data.message);
      ElMessage.error('妫€娴嬪け璐? ' + data.message);
      break;
  }
}

// 娣诲姞鏃ュ織
function addLog(level, message) {
  const now = new Date();
  const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
  
  detectionLogs.value.push({
    time: timeStr,
    level: level,
    message: message
  });

  // 闄愬埗鏃ュ織鏁伴噺
  if (detectionLogs.value.length > 100) {
    detectionLogs.value.shift();
  }
}

// 鏌ョ湅妫€娴嬬粨鏋?
function viewDetectionResults() {
  // 鍏抽棴瀵硅瘽妗?
  closeRealtimeDetection();
  
  // 鍔犺浇妫€娴嬬粨鏋滃埌涓婚〉闈?
  if (detectionResults.value) {
    // 鏇存柊涓婚〉闈㈢殑鏁版嵁
    anomalyRatio.value = detectionResults.value.anomaly_ratio;
    totalFrames.value = detectionResults.value.total_frames;
    anomalyCount.value = detectionResults.value.anomaly_count;
    anomalyFrames.value = detectionResults.value.anomaly_frames || [];
    
    // 濡傛灉鏈夐儴浠跺仴搴锋暟鎹紝涔熸洿鏂?
    if (detectionResults.value.component_health) {
      // 更新部件健康显示
      // ... 更新逻辑
    }
    
    ElMessage.success('妫€娴嬬粨鏋滃凡鍔犺浇鍒颁富椤甸潰');
  }
}

// 涓嬭浇妫€娴嬫姤鍛?
async function downloadResults() {
  try {
    if (!detectionResults.value?.session_id) {
      ElMessage.warning('没有可下载的结果');
      return;
    }

    const response = await fetch(`/api/v1/data/realtime-detection/report/?session_id=${detectionResults.value.session_id}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `detection_report_${detectionResults.value.session_id}.xlsx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    ElMessage.success('报告下载成功');
  } catch (error) {
    console.error('涓嬭浇鎶ュ憡澶辫触:', error);
    ElMessage.error('涓嬭浇鎶ュ憡澶辫触');
  }
}
```

---

#### 2. 鍚庣鏀归€?

**鏂板API绔偣锛坉ata_management/views.py锛夛細**

```python
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.core.files.storage import default_storage
from .batch_processing import RealtimeDetectionProcessor

@api_view(['POST'])
def realtime_detection(request):
    """
    瀹炴椂妫€娴婣PI绔偣
    接收文件上传，创建检测会话，返回会话ID
    """
    try:
        # 验证参数
        if 'file' not in request.FILES:
            return Response({'error': '娌℃湁涓婁紶鏂囦欢'}, status=status.HTTP_400_BAD_REQUEST)
        
        cmg_id = request.data.get('cmg_id')
        if not cmg_id:
            return Response({'error': '缂哄皯PHM ID'}, status=status.HTTP_400_BAD_REQUEST)
        
        detection_mode = request.data.get('detection_mode', 'full')
        save_results = request.data.get('save_results', 'true').lower() == 'true'
        
        # 淇濆瓨涓婁紶鐨勬枃浠?
        uploaded_file = request.FILES['file']
        file_path = default_storage.save(f'realtime_detection/{uploaded_file.name}', uploaded_file)
        
        # 鍒涘缓妫€娴嬩細璇?
        processor = RealtimeDetectionProcessor()
        session_id = processor.create_session(
            cmg_id=cmg_id,
            file_path=file_path,
            detection_mode=detection_mode,
            save_results=save_results
        )
        
        # 寮傛寮€濮嬫娴?
        processor.start_detection_async(session_id)
        
        return Response({
            'session_id': session_id,
            'message': '妫€娴嬩换鍔″凡鍒涘缓'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"鍒涘缓瀹炴椂妫€娴嬩换鍔″け璐? {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def realtime_detection_report(request):
    """
    鐢熸垚骞朵笅杞芥娴嬫姤鍛?
    """
    session_id = request.query_params.get('session_id')
    if not session_id:
        return Response({'error': '缂哄皯session_id'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        processor = RealtimeDetectionProcessor()
        report_path = processor.generate_report(session_id)
        
        # 杩斿洖鏂囦欢涓嬭浇
        from django.http import FileResponse
        return FileResponse(open(report_path, 'rb'), as_attachment=True, filename=f'detection_report_{session_id}.xlsx')
        
    except Exception as e:
        logger.error(f"鐢熸垚妫€娴嬫姤鍛婂け璐? {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

**鏂板澶勭悊鍣紙data_management/batch_processing.py锛夛細**

```python
class RealtimeDetectionProcessor:
    """瀹炴椂妫€娴嬪鐞嗗櫒"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self._active_sessions = {}
    
    def create_session(self, cmg_id, file_path, detection_mode, save_results):
        """鍒涘缓妫€娴嬩細璇?""
        session = ImportSession.objects.create(
            cmg_id=cmg_id,
            file=file_path,
            status=ImportSession.ProcessingStatus.PENDING,
            processing_options={
                'detection_mode': detection_mode,
                'save_results': save_results,
                'is_realtime': True
            }
        )
        return session.id
    
    def start_detection_async(self, session_id):
        """寮傛寮€濮嬫娴?""
        def _process():
            try:
                self._run_detection(session_id)
            except Exception as e:
                logger.error(f"瀹炴椂妫€娴嬪け璐?{session_id}: {e}")
                self._send_progress(session_id, {
                    'type': 'error',
                    'message': str(e)
                })
        
        thread = threading.Thread(target=_process, daemon=True)
        self._active_sessions[session_id] = thread
        thread.start()
    
    def _run_detection(self, session_id):
        """鎵ц妫€娴?""
        try:
            session = ImportSession.objects.get(id=session_id)
            options = session.processing_options or {}
            
            # 瑙ｆ瀽鏂囦欢
            self._send_progress(session_id, {
                'type': 'status',
                'level': 'info',
                'message': '姝ｅ湪瑙ｆ瀽鏂囦欢...'
            })
            
            data_records = self._parse_file(session)
            total_records = len(data_records)
            
            # 鏍规嵁妫€娴嬫ā寮忔墽琛屾娴?
            detection_mode = options.get('detection_mode', 'full')
            save_results = options.get('save_results', True)
            
            results = {
                'total_frames': total_records,
                'anomaly_count': 0,
                'anomaly_ratio': 0,
                'anomaly_frames': [],
                'component_health': {},
                'session_id': session_id
            }
            
            for idx, record in enumerate(data_records):
                # 鍙戦€佽繘搴︽洿鏂?
                if idx % 10 == 0:
                    self._send_progress(session_id, {
                        'type': 'progress',
                        'percentage': int((idx / total_records) * 100),
                        'processed': idx,
                        'total': total_records,
                        'message': f'姝ｅ湪澶勭悊绗?{idx}/{total_records} 鏉℃暟鎹?..'
                    })
                
                # 鎵ц妫€娴?
                detection_result = self._run_detection_for_record(
                    record, 
                    session.cmg, 
                    detection_mode
                )
                
                # 收集结果
                if detection_result.get('is_anomaly'):
                    results['anomaly_count'] += 1
                    results['anomaly_frames'].append(detection_result)
                
                # 鍙€夛細淇濆瓨鍒版暟鎹簱
                if save_results:
                    self._save_detection_result(session.cmg, record, detection_result)
            
            # 璁＄畻寮傚父姣斾緥
            results['anomaly_ratio'] = results['anomaly_count'] / total_records if total_records > 0 else 0
            
            # 鍙戦€佸畬鎴愭秷鎭?
            self._send_progress(session_id, {
                'type': 'completed',
                'results': results
            })
            
            # 鏇存柊浼氳瘽鐘舵€?
            session.status = ImportSession.ProcessingStatus.COMPLETED
            session.completed_at = timezone.now()
            session.processed_records = total_records
            session.save()
            
        except Exception as e:
            logger.error(f"妫€娴嬫墽琛屽け璐? {e}")
            raise
    
    def _run_detection_for_record(self, record, cmg, detection_mode):
        """涓哄崟鏉¤褰曟墽琛屾娴?""
        result = {
            'timestamp': record.get('timestamp'),
            'is_anomaly': False,
            'ims_result': None,
            'rule_result': None,
            'msfg_result': None
        }
        
        if detection_mode in ['full', 'ims_only']:
            # IMS妫€娴?
            ims_result = run_ims_detection(record)
            result['ims_result'] = ims_result
            if ims_result.get('is_anomaly'):
                result['is_anomaly'] = True
        
        if detection_mode in ['full', 'rule_only']:
            # 瑙勫垯妫€娴?
            rule_result = evaluate_rules_for_data_point(record, cmg)
            result['rule_result'] = rule_result
            if rule_result.get('has_violation'):
                result['is_anomaly'] = True
        
        if detection_mode in ['full', 'msfg_only']:
            # MSFG妫€娴?
            msfg_result = self._run_msfg_detection(record, cmg)
            result['msfg_result'] = msfg_result
            if msfg_result.get('has_fault'):
                result['is_anomaly'] = True
        
        return result
    
    def _send_progress(self, session_id, data):
        """閫氳繃WebSocket鍙戦€佽繘搴︽洿鏂?""
        channel_name = f"realtime_detection_{session_id}"
        async_to_sync(self.channel_layer.group_send)(
            channel_name,
            {
                'type': 'detection_progress',
                'data': data
            }
        )
    
    def generate_report(self, session_id):
        """鐢熸垚妫€娴嬫姤鍛婏紙Excel鏍煎紡锛?""
        # 实现报告生成逻辑
        # ...
        pass
```

**鏂板WebSocket Consumer锛坉ata_management/consumers.py锛夛細**

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class RealtimeDetectionConsumer(AsyncWebsocketConsumer):
    """瀹炴椂妫€娴嬭繘搴ebSocket Consumer"""
    
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f"realtime_detection_{self.session_id}"
        
        # 鍔犲叆缁?
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # 绂诲紑缁?
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def detection_progress(self, event):
        """鎺ユ敹杩涘害鏇存柊骞跺彂閫佺粰瀹㈡埛绔?""
        await self.send(text_data=json.dumps(event['data']))
```

**鏇存柊routing.py娣诲姞WebSocket璺敱锛?*

```python
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/realtime-detection/(?P<session_id>\w+)/$', consumers.RealtimeDetectionConsumer.as_asgi()),
]
```

---

## 馃搳 鎶€鏈鐐?

### 1. 鍓嶇
- **Vue 3 Composition API** - 鐘舵€佺鐞?
- **Element Plus** - UI缁勪欢锛圖ialog銆乁pload銆丳rogress銆丼teps锛?
- **WebSocket** - 瀹炴椂杩涘害閫氫俊

### 2. 鍚庣
- **Django REST Framework** - API绔偣
- **Django Channels** - WebSocket鏀寔
- **Threading** - 寮傛妫€娴嬪鐞?
- **batch_processing.py** - 澶嶇敤鐜版湁妫€娴嬮€昏緫

### 3. 鏁版嵁娴?
```
鍓嶇涓婁紶鏂囦欢 
  鈫?(HTTP POST)
鍒涘缓妫€娴嬩細璇?
  鈫?(杩斿洖session_id)
寤虹珛WebSocket杩炴帴
  鈫?
鍚庣寮傛鎵ц妫€娴?
  鈫?(WebSocket鎺ㄩ€佽繘搴?
鍓嶇瀹炴椂鏄剧ず杩涘害
  鈫?
妫€娴嬪畬鎴?
  鈫?(WebSocket鎺ㄩ€佺粨鏋?
前端显示结果
```

---

## 鉁?浼樺娍

1. **鐢ㄦ埛浣撻獙鎻愬崌**
   - 鏃犻渶绛夊緟鏁版嵁瀵煎叆鍜屽鐞?
   - 瀹炴椂鏌ョ湅妫€娴嬭繘搴?
   - 鍗虫椂鍙嶉妫€娴嬬粨鏋?

2. **鐏垫椿鎬?*
   - 鏀寔鍘嗗彶鏁版嵁鏌ヨ鍜屽疄鏃舵娴嬩袱绉嶆ā寮?
   - 鍙€夋嫨淇濆瓨缁撴灉鍒版暟鎹簱
   - 鏀寔澶氱妫€娴嬫ā寮忥紙IMS/瑙勫垯/MSFG锛?

3. **澶嶇敤鎬?*
   - 瀹屽叏澶嶇敤鐜版湁鐨刞batch_processing.py`妫€娴嬮€昏緫
   - 涓嶅奖鍝嶇幇鏈夊姛鑳?
   - 娓愯繘寮忓崌绾?

4. **鍙墿灞曟€?*
   - 鏄撲簬娣诲姞鏂扮殑妫€娴嬬被鍨?
   - 鏀寔鎵归噺妫€娴?
   - 鍙敓鎴愭娴嬫姤鍛?

---

## 馃攧 瀹炴柦姝ラ

### Phase 1: 鍩虹鏋舵瀯锛?-2澶╋級
1. 鉁?瀹夎Django Channels
2. 鉁?閰嶇疆WebSocket routing
3. 鉁?鍒涘缓RealtimeDetectionConsumer
4. 鉁?娴嬭瘯WebSocket杩炴帴

### Phase 2: 鍚庣API锛?-3澶╋級
1. 鉁?瀹炵幇`realtime_detection`绔偣
2. 鉁?鍒涘缓`RealtimeDetectionProcessor`绫?
3. 鉁?瀹炵幇杩涘害鎺ㄩ€佹満鍒?
4. 鉁?瀹炵幇鎶ュ憡鐢熸垚鍔熻兘
5. 鉁?鍗曞厓娴嬭瘯

### Phase 3: 鍓嶇UI锛?-3澶╋級
1. 鉁?娣诲姞瀹炴椂妫€娴嬫寜閽?
2. 鉁?鍒涘缓瀹炴椂妫€娴嬪璇濇
3. 鉁?瀹炵幇鏂囦欢涓婁紶閫昏緫
4. 鉁?瀹炵幇WebSocket杩炴帴
5. 鉁?瀹炵幇杩涘害鏄剧ず
6. 鉁?瀹炵幇缁撴灉灞曠ず

### Phase 4: 闆嗘垚娴嬭瘯锛?-2澶╋級
1. 鉁?绔埌绔祴璇?
2. 鉁?鎬ц兘娴嬭瘯
3. 鉁?閿欒澶勭悊娴嬭瘯
4. 鉁?鐢ㄦ埛浣撻獙浼樺寲

---

## 馃摑 鎬荤粨

杩欎釜鍗囩骇鏂规灏嗘娴嬬粨鏋滄€昏椤甸潰浠?*鍙妯″紡**鍗囩骇涓?*璇诲啓妯″紡**锛屽厑璁哥敤鎴凤細
- 鉁?鏌ヨ鍘嗗彶妫€娴嬬粨鏋滐紙鍘熸湁鍔熻兘锛?
- 鉁?瀹炴椂鎵ц妫€娴嬩换鍔★紙鏂板鍔熻兘锛?

閫氳繃澶嶇敤鐜版湁鐨勬娴嬮€昏緫鍜屾暟鎹簱缁撴瀯锛屼互**娓愯繘寮忋€佹棤鐮村潖鎬?*鐨勬柟寮忓疄鐜板姛鑳藉崌绾э紝澶уぇ鎻愬崌浜嗙郴缁熺殑瀹炵敤鎬у拰鐢ㄦ埛浣撻獙銆?

---

**鏂囨。鍒涘缓鏃ユ湡**锛?025-10-10  
**鍒涘缓鑰?*锛欰I Assistant  
**鐘舵€?*锛氬緟瀹℃牳



<template>
  <div class="tp-rules-page">
    <el-card class="toolbar">
      <el-form :model="query" inline>
        <el-form-item label="CMG 模型">
          <el-select v-model="query.cmgModelId" placeholder="选择模型" style="min-width: 260px;" @change="onCmgModelChange">
            <el-option v-for="m in cmgModels" :key="m.id" :label="m.model_name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试点">
          <el-select v-model="query.testName" placeholder="（从活跃MSFG加载）" clearable style="min-width: 240px;" @change="loadTPRules">
            <el-option v-for="t in testNames" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="query.activeOnly" @change="loadTPRules">仅启用</el-checkbox>
        </el-form-item>
        <el-form-item>
          <el-button type="success" @click="openCreateTPRule" :disabled="!query.cmgModelId">新增测点规则</el-button>
          <el-button type="primary" @click="openComponentMappings" :disabled="!query.cmgModelId" style="margin-left:8px;">部件对应管理</el-button>
          <el-button @click="loadTPRules" style="margin-left:8px;">刷新</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <el-table :data="tpRules" size="small" border v-loading="loading">
        <el-table-column label="#" type="index" width="60" />
        <el-table-column prop="rule_id" label="规则ID" width="200" />
        <el-table-column prop="test_name" label="测试点名称" />
        <el-table-column prop="weight" label="权重" width="100" />
        <el-table-column prop="is_online" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_online ? 'success' : 'info'">{{ scope.row.is_online ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="rule_expression" label="表达式">
          <template #default="scope">
            <span style="color:#666;">{{ (scope.row.rule_expression || '').slice(0,120) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" text type="primary" @click="openEditTPRule(scope.row)">编辑</el-button>
            <el-popconfirm title="确认删除该规则？" @confirm="removeTPRule(scope.row)">
              <template #reference>
                <el-button size="small" text type="danger">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

        <!-- 测点规则 Dialog -->
    <el-dialog v-model="tpRuleDialog" :title="tpRuleMode==='create'?'新增测点规则':'编辑测点规则'" width="560px">
      <el-form :model="tpRuleForm" label-width="110px">
        <el-form-item label="CMG 模型">
          <el-select v-model="tpRuleForm.cmg_model" placeholder="选择模型">
            <el-option v-for="m in cmgModels" :key="m.id" :label="m.model_name" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="测试点">
          <el-select v-model="tpRuleForm.test_name" placeholder="选择测试点" filterable>
            <el-option v-for="t in testNames" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则ID">
          <el-input v-model="tpRuleForm.rule_id" placeholder="如：TP_TEMP_001" />
        </el-form-item>
        <el-form-item label="表达式">
          <el-input v-model="tpRuleForm.rule_expression" type="textarea" :rows="3" placeholder="如：Temperature > 80" />
        </el-form-item>
        <el-form-item label="权重">
          <el-input-number v-model="tpRuleForm.weight" :min="0" :max="10" :step="0.1" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="tpRuleForm.is_online" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="tpRuleForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tpRuleDialog=false">取消</el-button>
        <el-button type="primary" @click="submitTPRule">保存</el-button>
      </template>
    </el-dialog>

    <!-- 部件对应管理 Dialog -->
    <el-dialog v-model="componentMappingsDialog" title="MSFG部件对应管理" width="90%" :close-on-click-modal="false">
      <div style="max-height: 70vh; display: flex; flex-direction: column;">
        <div style="position: sticky; top: 0; z-index: 1; background: var(--el-bg-color); padding-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <el-tag type="info">当前模型：{{ currentModelName }}</el-tag>
            <el-tag type="success" style="margin-left: 8px;">活跃MSFG：{{ activeMsfgName }}</el-tag>
          </div>
          <div style="display: flex; gap: 10px;">
            <el-tooltip content="从多信号流图配置.json文件中提取部件并修复MSFG配置。适用于部件提取失败或新增型号的情况。" placement="top">
              <el-button type="warning" size="small" @click="fixComponents" :loading="fixingComponents">
                🔧 修复部件提取
              </el-button>
            </el-tooltip>
            <el-tooltip content="查看当前MSFG的故障D矩阵，显示测试点到故障点的依赖关系" placement="top">
              <el-button type="success" size="small" @click="showDMatrix" :disabled="!activeMsfgId">
                📊 查看D矩阵
              </el-button>
            </el-tooltip>
            <el-button type="primary" size="small" @click="refreshComponentMappings">刷新</el-button>
            <el-button type="info" size="small" @click="openComponentMappingsInNewTab">新窗口打开</el-button>
          </div>
        </div>
        <el-scrollbar style="flex: 1;" max-height="65vh">
        <!-- 缺失映射提示框 -->
        <el-alert
          v-if="missingMappingsCount > 0"
          type="warning"
          :closable="false"
          show-icon
          style="margin-bottom: 15px;"
        >
          <template #title>
            <div style="display: flex; align-items: center; gap: 10px;">
              <span style="font-size: 16px; font-weight: bold;">🚨 重要提醒：发现缺失的映射关系</span>
              <el-tag type="danger" size="small">{{ missingMappingsCount }} 个映射缺失</el-tag>
            </div>
          </template>
          <template #default>
            <div style="margin-top: 10px;">
              <p style="margin: 0 0 10px 0; font-size: 14px; line-height: 1.5;">
                <strong>以下映射关系缺失，将严重影响故障诊断推理的准确性：</strong>
              </p>
              
              <div v-if="unmappedTests.length > 0" style="margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                  <span style="font-size: 16px;">📋</span>
                  <span style="font-weight: bold; color: #e6a23c;">缺失的测试点-部件映射 ({{ unmappedTests.length }}个)</span>
                </div>
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #666;">
                  这些测试点无法关联到具体部件，导致无法进行有效的故障定位：
                </p>
                <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                  <el-tag 
                    v-for="test in unmappedTests.slice(0, 8)" 
                    :key="test" 
                    type="warning" 
                    size="small"
                    effect="plain"
                  >
                    {{ test }}
                  </el-tag>
                  <el-tag 
                    v-if="unmappedTests.length > 8" 
                    type="info" 
                    size="small"
                    effect="plain"
                  >
                    ... 还有{{ unmappedTests.length - 8 }}个
                  </el-tag>
                </div>
              </div>
              
              <div v-if="unmappedFaults.length > 0" style="margin-bottom: 15px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                  <span style="font-size: 16px;">⚠️</span>
                  <span style="font-weight: bold; color: #f56c6c;">缺失的故障-部件映射 ({{ unmappedFaults.length }}个)</span>
                </div>
                <p style="margin: 0 0 8px 0; font-size: 13px; color: #666;">
                  这些故障无法关联到具体部件，导致无法进行准确的故障诊断：
                </p>
                <div style="display: flex; flex-wrap: wrap; gap: 5px;">
                  <el-tag 
                    v-for="fault in unmappedFaults.slice(0, 8)" 
                    :key="fault" 
                    type="danger" 
                    size="small"
                    effect="plain"
                  >
                    {{ fault }}
                  </el-tag>
                  <el-tag 
                    v-if="unmappedFaults.length > 8" 
                    type="info" 
                    size="small"
                    effect="plain"
                  >
                    ... 还有{{ unmappedFaults.length - 8 }}个
                  </el-tag>
                </div>
              </div>
              
              <div style="background: #f0f9ff; padding: 12px; border-radius: 6px; border-left: 4px solid #409eff; margin-top: 15px;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                  <span style="font-size: 16px;">💡</span>
                  <span style="font-weight: bold; color: #409eff;">🎯 立即行动建议</span>
                </div>
                <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #666;">
                  <li>使用下方的映射管理表格添加缺失的映射关系</li>
                  <li>点击"添加映射"按钮快速创建新的映射</li>
                  <li>补全映射后，故障诊断推理的准确性和完整性将显著提升</li>
                </ul>
              </div>
            </div>
          </template>
        </el-alert>
        
        <!-- 测试点-部件映射管理 -->
        <el-card style="margin-bottom: 10px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>测试点-部件映射管理</span>
              <el-button type="primary" size="small" @click="addMapping">添加映射</el-button>
            </div>
          </template>
          <el-table :data="componentMappings" size="small" border v-loading="mappingsLoading" height="260">
            <el-table-column label="#" type="index" width="60" />
            <el-table-column prop="test_point" label="测试点" width="200">
              <template #default="scope">
                <el-select v-model="scope.row.test_point" placeholder="选择测试点" style="width: 100%;" @change="updateMapping(scope.$index)">
                  <el-option v-for="test in availableTestPoints" :key="test" :label="test" :value="test" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="component" label="部件" width="200">
              <template #default="scope">
                <el-select v-model="scope.row.component" placeholder="选择部件" style="width: 100%;" @change="updateMapping(scope.$index)">
                  <el-option v-for="comp in availableComponents" :key="comp" :label="comp" :value="comp" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="mapping_type" label="映射类型" width="120">
              <template #default="scope">
                <el-select v-model="scope.row.mapping_type" placeholder="映射类型" style="width: 100%;" @change="updateMapping(scope.$index)">
                  <el-option label="一对一" value="one_to_one" />
                  <el-option label="一对多" value="one_to_many" />
                  <el-option label="多对一" value="many_to_one" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="权重" width="100">
              <template #default="scope">
                <el-input-number v-model="scope.row.weight" :min="0" :max="10" :step="0.1" :precision="1" style="width: 100%;" @change="updateMapping(scope.$index)" />
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述">
              <template #default="scope">
                <el-input v-model="scope.row.description" placeholder="描述" @change="updateMapping(scope.$index)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" text type="danger" @click="removeMapping(scope.$index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div style="margin-top: 10px; display: flex; gap: 10px;">
            <el-button type="success" size="small" @click="saveMappings" :loading="savingMappings">保存映射</el-button>
            <el-button size="small" @click="loadMappings">重新加载</el-button>
            <el-button size="small" @click="exportMappings">导出映射</el-button>
            <el-button size="small" @click="importMappings">导入映射</el-button>
          </div>
        </el-card>
 
         <!-- 新增：故障-部件映射管理 -->
         <el-card style="margin-bottom: 10px;">
           <template #header>
             <div style="display: flex; justify-content: space-between; align-items: center;">
               <span>故障-部件映射管理</span>
               <el-button type="primary" size="small" @click="addFaultMapping">添加映射</el-button>
             </div>
           </template>
 
          <el-table :data="faultComponentMappings" size="small" border v-loading="faultMappingsLoading" height="260">
            <el-table-column label="#" type="index" width="60" />
            <el-table-column prop="fault_name" label="故障" width="220">
              <template #default="scope">
                <el-select v-model="scope.row.fault_name" placeholder="选择故障" style="width: 100%;" @change="updateFaultMapping(scope.$index)">
                  <el-option v-for="f in availableFaults" :key="f" :label="f" :value="f" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="component" label="部件" width="220">
              <template #default="scope">
                <el-select v-model="scope.row.component" placeholder="选择部件" style="width: 100%;" @change="updateFaultMapping(scope.$index)">
                  <el-option v-for="comp in availableComponents" :key="comp" :label="comp" :value="comp" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="mapping_type" label="映射类型" width="120">
              <template #default="scope">
                <el-select v-model="scope.row.mapping_type" placeholder="映射类型" style="width: 100%;" @change="updateFaultMapping(scope.$index)">
                  <el-option label="一对一" value="one_to_one" />
                  <el-option label="一对多" value="one_to_many" />
                  <el-option label="多对一" value="many_to_one" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="权重" width="100">
              <template #default="scope">
                <el-input-number v-model="scope.row.weight" :min="0" :max="10" :step="0.1" :precision="1" style="width: 100%;" @change="updateFaultMapping(scope.$index)" />
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述">
              <template #default="scope">
                <el-input v-model="scope.row.description" placeholder="描述" @change="updateFaultMapping(scope.$index)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" text type="danger" @click="removeFaultMapping(scope.$index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
 
          <div style="margin-top: 10px; display: flex; gap: 10px;">
            <el-button type="success" size="small" @click="saveFaultMappings" :loading="savingFaultMappings">保存映射</el-button>
            <el-button size="small" @click="loadFaultMappings">重新加载</el-button>
            <el-button size="small" @click="exportFaultMappings">导出映射</el-button>
            <el-button size="small" @click="importFaultMappings">导入映射</el-button>
          </div>
        </el-card>

        <!-- 新增：测试点-故障映射管理 -->
        <el-card style="margin-bottom: 10px;">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>测试点-故障映射管理</span>
              <el-button type="primary" size="small" @click="addTestPointFaultMapping">添加映射</el-button>
            </div>
          </template>

          <el-table :data="testPointFaultMappings" size="small" border v-loading="testPointFaultMappingsLoading" height="260">
            <el-table-column label="#" type="index" width="60" />
            <el-table-column prop="test_point_name" label="测试点" width="200">
              <template #default="scope">
                <el-select v-model="scope.row.test_point_name" placeholder="选择测试点" style="width: 100%;" @change="updateTestPointFaultMapping(scope.$index)">
                  <el-option v-for="test in availableTestPoints" :key="test" :label="test" :value="test" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="fault_name" label="故障" width="220">
              <template #default="scope">
                <el-select v-model="scope.row.fault_name" placeholder="选择故障" style="width: 100%;" @change="updateTestPointFaultMapping(scope.$index)">
                  <el-option v-for="fault in availableFaults" :key="fault" :label="fault" :value="fault" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="mapping_type" label="映射类型" width="120">
              <template #default="scope">
                <el-select v-model="scope.row.mapping_type" placeholder="映射类型" style="width: 100%;" @change="updateTestPointFaultMapping(scope.$index)">
                  <el-option label="一对一" value="one_to_one" />
                  <el-option label="一对多" value="one_to_many" />
                  <el-option label="多对一" value="many_to_one" />
                </el-select>
              </template>
            </el-table-column>
            <el-table-column prop="weight" label="权重" width="100">
              <template #default="scope">
                <el-input-number v-model="scope.row.weight" :min="0" :max="10" :step="0.1" :precision="1" style="width: 100%;" @change="updateTestPointFaultMapping(scope.$index)" />
              </template>
            </el-table-column>
            <el-table-column prop="confidence" label="置信度" width="100">
              <template #default="scope">
                <el-input-number v-model="scope.row.confidence" :min="0.1" :max="1" :step="0.1" :precision="1" style="width: 100%;" @change="updateTestPointFaultMapping(scope.$index)" />
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述">
              <template #default="scope">
                <el-input v-model="scope.row.description" placeholder="描述" @change="updateTestPointFaultMapping(scope.$index)" />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="120">
              <template #default="scope">
                <el-button size="small" text type="danger" @click="removeTestPointFaultMapping(scope.$index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div style="margin-top: 10px; display: flex; gap: 10px;">
            <el-button type="success" size="small" @click="saveTestPointFaultMappings" :loading="savingTestPointFaultMappings">保存映射</el-button>
            <el-button size="small" @click="loadTestPointFaultMappings">重新加载</el-button>
            <el-button size="small" @click="exportTestPointFaultMappings">导出映射</el-button>
            <el-button size="small" @click="importTestPointFaultMappings">导入映射</el-button>
          </div>
        </el-card>
        </el-scrollbar>
        <!-- 统一去除旧的嵌入页面，避免与本页管理UI重复导致混乱 -->
      </div>
    </el-dialog>

    <!-- D矩阵显示 Dialog -->
    <el-dialog v-model="dMatrixDialog" title="故障D矩阵" width="95%" :close-on-click-modal="false" class="d-matrix-dialog">
      <div v-loading="dMatrixLoading" style="min-height: 400px;">
        <div v-if="dMatrixData" class="d-matrix-container">
          <!-- 矩阵信息统计 -->
          <div class="matrix-info">
            <el-row :gutter="20">
              <el-col :span="6">
                <el-card shadow="never" class="info-card">
                  <div class="info-item">
                    <div class="info-label">矩阵大小</div>
                    <div class="info-value">{{ dMatrixData.shape[0] }} × {{ dMatrixData.shape[1] }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="never" class="info-card">
                  <div class="info-item">
                    <div class="info-label">故障数量</div>
                    <div class="info-value">{{ dMatrixData.fault_count }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="never" class="info-card">
                  <div class="info-item">
                    <div class="info-label">测试点数量</div>
                    <div class="info-value">{{ dMatrixData.test_count }}</div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="6">
                <el-card shadow="never" class="info-card">
                  <div class="info-item">
                    <div class="info-label">非零元素</div>
                    <div class="info-value">{{ dMatrixData.nonzero_count }}</div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>

          <!-- 矩阵显示区域 -->
          <div class="matrix-display">
            <div class="matrix-header">
              <h3>依赖矩阵 D (Fault × Test)</h3>
              <div class="matrix-controls">
                <el-switch v-model="showMatrixValues" active-text="显示数值" inactive-text="仅显示连接" />
                <el-button size="small" @click="exportDMatrix">导出矩阵</el-button>
              </div>
            </div>
            
            <div class="matrix-table-container">
              <table class="d-matrix-table">
                <thead>
                  <tr>
                    <th class="corner-cell">故障\测试点</th>
                    <th v-for="test in dMatrixData.test_names" :key="test" class="test-header">
                      <div class="test-name">{{ test }}</div>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(fault, faultIndex) in dMatrixData.fault_names" :key="fault">
                    <td class="fault-header">
                      <div class="fault-name">{{ fault }}</div>
                    </td>
                    <td 
                      v-for="(test, testIndex) in dMatrixData.test_names" 
                      :key="test"
                      :class="getMatrixCellClass(faultIndex, testIndex)"
                      @click="showCellDetails(faultIndex, testIndex)"
                    >
                      <div v-if="showMatrixValues && dMatrixData.matrix[faultIndex][testIndex] > 0" class="cell-value">
                        {{ dMatrixData.matrix[faultIndex][testIndex].toFixed(2) }}
                      </div>
                      <div v-else-if="dMatrixData.matrix[faultIndex][testIndex] > 0" class="cell-connection">
                        ●
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 诊断分析 -->
          <div class="diagnostic-analysis" v-if="dMatrixData.analysis">
            <h3>诊断能力分析</h3>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-card shadow="never" class="analysis-card">
                  <div class="analysis-item">
                    <div class="analysis-label">可检测故障</div>
                    <div class="analysis-value">{{ dMatrixData.analysis.detectable_faults.length }}</div>
                    <div class="analysis-detail">
                      <el-tag 
                        v-for="fault in dMatrixData.analysis.detectable_faults.slice(0, 3)" 
                        :key="fault" 
                        size="small" 
                        type="success"
                        style="margin: 2px;"
                      >
                        {{ fault }}
                      </el-tag>
                      <el-tag v-if="dMatrixData.analysis.detectable_faults.length > 3" size="small" type="info">
                        +{{ dMatrixData.analysis.detectable_faults.length - 3 }}
                      </el-tag>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card shadow="never" class="analysis-card">
                  <div class="analysis-item">
                    <div class="analysis-label">可隔离故障</div>
                    <div class="analysis-value">{{ dMatrixData.analysis.isolable_faults.length }}</div>
                    <div class="analysis-detail">
                      <el-tag 
                        v-for="fault in dMatrixData.analysis.isolable_faults.slice(0, 3)" 
                        :key="fault" 
                        size="small" 
                        type="primary"
                        style="margin: 2px;"
                      >
                        {{ fault }}
                      </el-tag>
                      <el-tag v-if="dMatrixData.analysis.isolable_faults.length > 3" size="small" type="info">
                        +{{ dMatrixData.analysis.isolable_faults.length - 3 }}
                      </el-tag>
                    </div>
                  </div>
                </el-card>
              </el-col>
              <el-col :span="8">
                <el-card shadow="never" class="analysis-card">
                  <div class="analysis-item">
                    <div class="analysis-label">不可区分组</div>
                    <div class="analysis-value">{{ dMatrixData.analysis.indistinguishable_groups.length }}</div>
                    <div class="analysis-detail">
                      <el-tag 
                        v-for="(group, index) in dMatrixData.analysis.indistinguishable_groups.slice(0, 2)" 
                        :key="index" 
                        size="small" 
                        type="warning"
                        style="margin: 2px;"
                      >
                        {{ group.length }}个故障
                      </el-tag>
                      <el-tag v-if="dMatrixData.analysis.indistinguishable_groups.length > 2" size="small" type="info">
                        +{{ dMatrixData.analysis.indistinguishable_groups.length - 2 }}
                      </el-tag>
                    </div>
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </div>
        
        <div v-else-if="!dMatrixLoading" class="no-data">
          <el-empty description="暂无D矩阵数据" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { ElMessage } from 'element-plus';
import api from '../api';

defineOptions({ name: 'TestPointRules' });

const loading = ref(false);
const cmgModels = ref([]);
const tpRules = ref([]);

const query = ref({ cmgModelId: null, activeOnly: true, testName: '' });
const testNames = ref([]);

const tpRuleDialog = ref(false);
const tpRuleMode = ref('create');
const tpRuleForm = ref({ id: null, cmg_model: null, test_name: '', rule_id: '', rule_expression: '', weight: 1.0, is_online: true, description: ''});

// 部件对应管理相关
const componentMappingsDialog = ref(false);
const componentMappingsIframe = ref(null);
const activeMsfg = ref(null);

// 测试点-部件映射管理
const componentMappings = ref([]);
const availableTestPoints = ref([]);
const availableComponents = ref([]);
const mappingsLoading = ref(false);
const savingMappings = ref(false);

// 故障-部件映射管理
const faultComponentMappings = ref([]);
const availableFaults = ref([]);
const faultMappingsLoading = ref(false);
const savingFaultMappings = ref(false);

// 测试点-故障映射管理
const testPointFaultMappings = ref([]);
const availableTestPointsForFault = ref([]); // 用于测试点-故障映射的可用测试点
const testPointFaultMappingsLoading = ref(false);
const savingTestPointFaultMappings = ref(false);

// 修复部件提取相关
const fixingComponents = ref(false);

// D矩阵显示相关
const dMatrixDialog = ref(false);
const dMatrixLoading = ref(false);
const dMatrixData = ref(null);
const showMatrixValues = ref(false);

// 计算属性
const activeMsfgId = computed(() => activeMsfg.value?.id);

// 通用验证函数
function validateMappingData(mapping, type = 'testpoint') {
  if (type === 'testpoint') {
    return mapping.test_point && mapping.component;
  } else if (type === 'fault') {
    return mapping.fault_name && mapping.component;
  }
  return false;
}

function validateImportData(data, expectedType = 'testpoint') {
  if (!data || typeof data !== 'object') {
    return { valid: false, error: '数据格式错误' };
  }
  
  if (!data.mappings || !Array.isArray(data.mappings)) {
    return { valid: false, error: '缺少mappings数组' };
  }
  
  if (data.mappings.length === 0) {
    return { valid: false, error: 'mappings数组为空' };
  }
  
  return { valid: true };
}

async function loadCmgModels() {
  try {
    const res = await api.get('/data/cmg-models/');
    cmgModels.value = Array.isArray(res.data) ? res.data : [];
  } catch (e) { console.error('加载模型失败', e); }
}

async function loadActiveMsfgTestNames() {
  testNames.value = [];
  activeMsfg.value = null;
  if (!query.value.cmgModelId) return;
  try {
    const res = await api.get('/msfg/msfg-definitions/', { params: { cmg_model_id: query.value.cmgModelId, is_active: 'true' } });
    const list = Array.isArray(res.data) ? res.data : (res.data.results || []);
    if (list.length > 0) {
      activeMsfg.value = list[0];
      testNames.value = list[0].test_names || [];
    }
  } catch (e) { console.error('加载测试点失败', e); }
}

async function loadTPRules(){
  loading.value = true;
  try{
    const params = {};
    if (query.value.cmgModelId) params.cmg_model_id = query.value.cmgModelId;
    if (query.value.testName) params.test_name = query.value.testName;
    if (query.value.activeOnly) params.is_online = 'true';
    const res = await api.get('/msfg/testpoint-rules/', { params });
    tpRules.value = Array.isArray(res.data) ? res.data : (res.data.results || []);
  }catch(e){ console.error('加载测点规则失败', e); tpRules.value = []; }
  finally{ loading.value = false; }
}

function openCreateTPRule(){
  tpRuleMode.value = 'create';
  tpRuleForm.value = { id: null, cmg_model: query.value.cmgModelId, test_name: query.value.testName || '', rule_id: '', rule_expression: '', weight: 1.0, is_online: true, description: '' };
  tpRuleDialog.value = true;
}

function openEditTPRule(row){
  tpRuleMode.value = 'edit';
  tpRuleForm.value = { id: row.id, cmg_model: row.cmg_model, test_name: row.test_name, rule_id: row.rule_id, rule_expression: row.rule_expression, weight: row.weight, is_online: row.is_online, description: row.description || '' };
  tpRuleDialog.value = true;
}

async function submitTPRule(){
  try{
    if(!tpRuleForm.value.cmg_model || !tpRuleForm.value.test_name || !tpRuleForm.value.rule_id || !tpRuleForm.value.rule_expression) return;
    if(tpRuleMode.value==='create'){
      await api.post('/msfg/testpoint-rules/', tpRuleForm.value);
    }else{
      await api.put(`/msfg/testpoint-rules/${tpRuleForm.value.id}/`, tpRuleForm.value);
    }
    tpRuleDialog.value=false;
    await loadTPRules();
  }catch(e){ console.error('保存测点规则失败', e); }
}

async function removeTPRule(row){
  try{
    await api.delete(`/msfg/testpoint-rules/${row.id}/`);
    await loadTPRules();
  }catch(e){ console.error('删除测点规则失败', e); }
}

// 计算属性
const currentModelName = computed(() => {
  const model = cmgModels.value.find(m => m.id === query.value.cmgModelId);
  return model ? model.model_name : '未选择';
});

const activeMsfgName = computed(() => {
  return activeMsfg.value ? activeMsfg.value.msfg_name || '未知' : '未找到活跃MSFG';
});

// 计算缺失的映射
const unmappedTests = computed(() => {
  if (!activeMsfg.value || !availableTestPoints.value.length) return [];
  const mappedTests = new Set(componentMappings.value.map(m => m.test_point));
  return availableTestPoints.value.filter(test => !mappedTests.has(test));
});

const unmappedFaults = computed(() => {
  if (!activeMsfg.value || !availableFaults.value.length) return [];
  const mappedFaults = new Set(faultComponentMappings.value.map(m => m.fault_name));
  return availableFaults.value.filter(fault => !mappedFaults.has(fault));
});

const missingMappingsCount = computed(() => {
  return unmappedTests.value.length + unmappedFaults.value.length;
});

const componentMappingsIframeSrc = computed(() => {
  const hint = window.__BACKEND_ORIGIN__;
  const backendOrigin = typeof hint === 'string' && hint.startsWith('http') ? hint : `${window.location.protocol}//${window.location.hostname}:8000`;
  return `${backendOrigin}/api/v1/msfg/component-mappings-ui/`;
});

// 部件对应管理函数
async function openComponentMappings() {
  componentMappingsDialog.value = true;
  // 加载映射数据
  await loadMappings();
}

function refreshComponentMappings() {
  // 重新加载映射数据
  loadMappings();
}

function openComponentMappingsInNewTab() {
  window.open(componentMappingsIframeSrc.value, '_blank');
}

function onComponentMappingsIframeLoad() {
  console.log('部件对应管理页面加载完成');
}

// 测试点-部件映射管理函数
async function loadMappings() {
  if (!activeMsfg.value) {
    console.warn('没有活跃的MSFG，无法加载映射');
    return;
  }
  
  mappingsLoading.value = true;
  try {
    // 加载可用的测试点（从活跃MSFG）
    availableTestPoints.value = activeMsfg.value.test_names || [];
    
    // 加载可用的部件（从MSFG结构提取）
    const componentsRes = await api.get(`/msfg/msfg-definitions/${activeMsfg.value.id}/components/`);
    availableComponents.value = componentsRes.data.components || [];
    
    // 加载现有映射
    const mappingsRes = await api.get(`/msfg/component-mappings/`, {
      params: { msfg_definition_id: activeMsfg.value.id }
    });
    
    if (Array.isArray(mappingsRes.data)) {
      componentMappings.value = mappingsRes.data.map(it => ({
        test_point: it.test_point ?? it.test_point_name,
        component: it.component ?? it.component_name,
        mapping_type: it.mapping_type || 'one_to_one',
        weight: (typeof it.weight === 'number') ? it.weight : Number(it.weight ?? 1.0),
        description: it.description || ''
      }));
    } else {
      componentMappings.value = [];
    }
    
    // 加载故障列表
    const faultsRes = await api.get(`/msfg/msfg-definitions/${activeMsfg.value.id}/faults/`);
    availableFaults.value = faultsRes.data?.faults || [];
    
    // 加载故障-部件映射
    await loadFaultMappings();
    
    // 加载测试点-故障映射
    await loadTestPointFaultMappings();

    console.log('映射加载完成:', {
      testPoints: availableTestPoints.value.length,
      components: availableComponents.value.length,
      mappings: componentMappings.value.length,
      faults: availableFaults.value.length,
      testPointFaultMappings: testPointFaultMappings.value.length
    });
    
    // 显示加载结果
    if (availableComponents.value.length === 0) {
      ElMessage.warning('未找到部件数据，请检查MSFG配置或使用"修复部件提取"功能');
    }
    
  } catch (error) {
    console.error('加载映射失败:', error);
    const errorMsg = error.response?.data?.error || error.message || '加载映射失败';
    ElMessage.error(`加载映射失败：${errorMsg}`);
    
    // 重置数据
    availableTestPoints.value = [];
    availableComponents.value = [];
    componentMappings.value = [];
    availableFaults.value = [];
    faultComponentMappings.value = [];
  } finally {
    mappingsLoading.value = false;
  }
}

function addMapping() {
  componentMappings.value.push({
    test_point: '',
    component: '',
    mapping_type: 'one_to_one',
    weight: 1.0,
    description: ''
  });
}

function updateMapping(index) {
  // 实时更新映射（可选，也可以只在保存时更新）
  console.log('更新映射:', componentMappings.value[index]);
}

function removeMapping(index) {
  componentMappings.value.splice(index, 1);
}

async function saveMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  // 验证映射数据
  const validMappings = componentMappings.value.filter(m => m.test_point && m.component);
  if (validMappings.length === 0) {
    ElMessage.warning('没有有效的映射数据需要保存');
    return;
  }
  
  // 检查重复映射
  const mappingKeys = new Set();
  const duplicates = [];
  for (const mapping of validMappings) {
    const key = `${mapping.test_point}-${mapping.component}`;
    if (mappingKeys.has(key)) {
      duplicates.push(key);
    } else {
      mappingKeys.add(key);
    }
  }
  
  if (duplicates.length > 0) {
    ElMessage.warning(`发现重复映射：${duplicates.join(', ')}，将保留最后一个`);
  }
  
  savingMappings.value = true;
  try {
    const response = await api.post(`/msfg/component-mappings/batch/`, {
      msfg_definition_id: activeMsfg.value.id,
      mappings: validMappings
    });
    
    if (response.data && response.data.saved !== undefined) {
      ElMessage.success(`映射保存成功，共保存 ${response.data.saved} 个映射`);
    } else {
      ElMessage.success('映射保存成功');
    }
    
    await loadMappings(); // 重新加载
  } catch (error) {
    console.error('保存映射失败:', error);
    const errorMsg = error.response?.data?.error || error.message || '保存映射失败';
    ElMessage.error(`保存映射失败：${errorMsg}`);
  } finally {
    savingMappings.value = false;
  }
}

function exportMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  const data = {
    msfg_definition_id: activeMsfg.value.id,
    msfg_definition_name: activeMsfg.value.msfg_name || activeMsfg.value.name,
    export_time: new Date().toISOString(),
    mappings: componentMappings.value.filter(m => m.test_point && m.component)
  };
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `testpoint_component_mappings_${activeMsfg.value.msfg_name || activeMsfg.value.name || 'unknown'}_${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
  
  ElMessage.success(`映射导出成功，共导出 ${data.mappings.length} 个映射`);
}

function importMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      // 验证文件格式
      if (!data.mappings || !Array.isArray(data.mappings)) {
        ElMessage.error('文件格式不正确：缺少mappings数组');
        return;
      }
      
      // 验证MSFG定义ID匹配（可选）
      if (data.msfg_definition_id && data.msfg_definition_id !== activeMsfg.value.id) {
        const confirmImport = confirm(`警告：导入文件的MSFG定义ID (${data.msfg_definition_id}) 与当前活跃MSFG (${activeMsfg.value.id}) 不匹配。是否继续导入？`);
        if (!confirmImport) return;
      }
      
      // 验证映射数据格式
      const validMappings = [];
      const invalidMappings = [];
      
      for (let i = 0; i < data.mappings.length; i++) {
        const mapping = data.mappings[i];
        if (mapping.test_point && mapping.component) {
          validMappings.push({
            test_point: mapping.test_point,
            component: mapping.component,
            mapping_type: mapping.mapping_type || 'one_to_one',
            weight: parseFloat(mapping.weight) || 1.0,
            description: mapping.description || ''
          });
        } else {
          invalidMappings.push(i + 1);
        }
      }
      
      if (invalidMappings.length > 0) {
        ElMessage.warning(`发现 ${invalidMappings.length} 个无效映射（第${invalidMappings.join(',')}行），已跳过`);
      }
      
      if (validMappings.length === 0) {
        ElMessage.error('没有有效的映射数据');
        return;
      }
      
      // 更新映射数据
      componentMappings.value = validMappings;
      ElMessage.success(`映射导入成功，共导入 ${validMappings.length} 个有效映射`);
      
    } catch (error) {
      console.error('导入映射失败:', error);
      if (error instanceof SyntaxError) {
        ElMessage.error('文件格式错误：不是有效的JSON文件');
      } else {
        ElMessage.error('导入映射失败：' + error.message);
      }
    }
  };
  input.click();
}

async function loadFaultMappings() {
  if (!activeMsfg.value) {
    console.warn('没有活跃的MSFG，无法加载故障映射');
    return;
  }
  
  faultMappingsLoading.value = true;
  try {
    const res = await api.get(`/msfg/fault-component-mappings/`, {
      params: { msfg_definition_id: activeMsfg.value.id }
    });
    
    if (Array.isArray(res.data)) {
      faultComponentMappings.value = res.data.map(it => ({
        fault_name: it.fault_name,
        component: it.component_name || it.component,
        mapping_type: it.mapping_type || 'one_to_one',
        weight: parseFloat(it.weight) || 1.0,
        description: it.description || ''
      }));
    } else {
      faultComponentMappings.value = [];
    }
    
    console.log('故障映射加载完成:', faultComponentMappings.value.length);
  } catch (e) {
    console.error('加载故障映射失败:', e);
    const errorMsg = e.response?.data?.error || e.message || '加载故障映射失败';
    ElMessage.error(`加载故障映射失败：${errorMsg}`);
    faultComponentMappings.value = [];
  } finally { 
    faultMappingsLoading.value = false; 
  }
}

async function saveFaultMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  // 验证映射数据
  const valid = faultComponentMappings.value.filter(m => m.fault_name && m.component);
  if (valid.length === 0) {
    ElMessage.warning('没有有效的故障映射数据需要保存');
    return;
  }
  
  // 检查重复映射
  const mappingKeys = new Set();
  const duplicates = [];
  for (const mapping of valid) {
    const key = `${mapping.fault_name}-${mapping.component}`;
    if (mappingKeys.has(key)) {
      duplicates.push(key);
    } else {
      mappingKeys.add(key);
    }
  }
  
  if (duplicates.length > 0) {
    ElMessage.warning(`发现重复故障映射：${duplicates.join(', ')}，将保留最后一个`);
  }
  
  savingFaultMappings.value = true;
  try {
    const response = await api.post(`/msfg/fault-component-mappings/batch/`, {
      msfg_definition_id: activeMsfg.value.id,
      mappings: valid
    });
    
    if (response.data && response.data.saved !== undefined) {
      ElMessage.success(`故障-部件映射保存成功，共保存 ${response.data.saved} 个映射`);
    } else {
      ElMessage.success('故障-部件映射保存成功');
    }
    
    await loadFaultMappings();
  } catch (e) {
    console.error('保存故障映射失败:', e);
    const errorMsg = e.response?.data?.error || e.message || '保存故障映射失败';
    ElMessage.error(`保存故障映射失败：${errorMsg}`);
  } finally { 
    savingFaultMappings.value = false; 
  }
}

// 新增一条故障-部件映射（供“添加映射”按钮使用）
function addFaultMapping() {
  faultComponentMappings.value.push({
    fault_name: '',
    component: '',
    mapping_type: 'one_to_one',
    weight: 1.0,
    description: ''
  });
}

// 删除故障-部件映射
function removeFaultMapping(index) {
  faultComponentMappings.value.splice(index, 1);
}

// 更新故障-部件映射
function updateFaultMapping(index) {
  // 实时更新映射（可选，也可以只在保存时更新）
  console.log('更新故障映射:', faultComponentMappings.value[index]);
}

// 新增一条测试点-故障映射（供“添加映射”按钮使用）
function addTestPointFaultMapping() {
  testPointFaultMappings.value.push({
    test_point_name: '',
    fault_name: '',
    mapping_type: 'one_to_one',
    weight: 1.0,
    confidence: 0.5,
    description: ''
  });
}

// 删除测试点-故障映射
function removeTestPointFaultMapping(index) {
  testPointFaultMappings.value.splice(index, 1);
}

// 更新测试点-故障映射
function updateTestPointFaultMapping(index) {
  // 实时更新映射（可选，也可以只在保存时更新）
  console.log('更新测试点-故障映射:', testPointFaultMappings.value[index]);
}

// 修复部件提取功能
async function fixComponents() {
  if (!query.value.cmgModelId) {
    ElMessage.error('请先选择CMG模型');
    return;
  }
  
  try {
    fixingComponents.value = true;
    
    const response = await api.post('/msfg/fix-components/', {
      cmg_model_id: query.value.cmgModelId
    });
    
    if (response.data.success) {
      const details = response.data.details;
      ElMessage.success(`修复成功！提取到 ${details.components_count} 个部件，创建了 ${details.system_nodes_created} 个系统节点，生成了 ${details.mappings_count} 个映射。`);
      
      // 重新加载映射数据
      await refreshComponentMappings();
    } else {
      ElMessage.error(response.data.error || '修复失败');
    }
  } catch (error) {
    console.error('修复部件提取失败:', error);
    ElMessage.error(error.response?.data?.error || '修复失败，请检查控制台错误信息');
  } finally {
    fixingComponents.value = false;
  }
}

function exportFaultMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  const data = {
    msfg_definition_id: activeMsfg.value.id,
    msfg_definition_name: activeMsfg.value.msfg_name || activeMsfg.value.name,
    export_time: new Date().toISOString(),
    mappings: faultComponentMappings.value.filter(m => m.fault_name && m.component)
  };
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `fault_component_mappings_${activeMsfg.value.msfg_name || activeMsfg.value.name || 'unknown'}_${new Date().toISOString().split('T')[0]}.json`;
  a.click();
  URL.revokeObjectURL(url);
  ElMessage.success(`故障映射导出成功，共导出 ${data.mappings.length} 个映射`);
}

function importFaultMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      // 验证文件格式
      if (!data.mappings || !Array.isArray(data.mappings)) {
        ElMessage.error('文件格式不正确：缺少mappings数组');
        return;
      }
      
      // 验证MSFG定义ID匹配（可选）
      if (data.msfg_definition_id && data.msfg_definition_id !== activeMsfg.value.id) {
        const confirmImport = confirm(`警告：导入文件的MSFG定义ID (${data.msfg_definition_id}) 与当前活跃MSFG (${activeMsfg.value.id}) 不匹配。是否继续导入？`);
        if (!confirmImport) return;
      }
      
      // 验证映射数据格式
      const validMappings = [];
      const invalidMappings = [];
      
      for (let i = 0; i < data.mappings.length; i++) {
        const mapping = data.mappings[i];
        if (mapping.fault_name && mapping.component) {
          validMappings.push({
            fault_name: mapping.fault_name,
            component: mapping.component,
            mapping_type: mapping.mapping_type || 'one_to_one',
            weight: parseFloat(mapping.weight) || 1.0,
            description: mapping.description || ''
          });
        } else {
          invalidMappings.push(i + 1);
        }
      }
      
      if (invalidMappings.length > 0) {
        ElMessage.warning(`发现 ${invalidMappings.length} 个无效映射（第${invalidMappings.join(',')}行），已跳过`);
      }
      
      if (validMappings.length === 0) {
        ElMessage.error('没有有效的映射数据');
        return;
      }
      
      // 更新映射数据
      faultComponentMappings.value = validMappings;
      ElMessage.success(`故障映射导入成功，共导入 ${validMappings.length} 个有效映射`);
      
    } catch (error) {
      console.error('导入故障映射失败:', error);
      if (error instanceof SyntaxError) {
        ElMessage.error('文件格式错误：不是有效的JSON文件');
      } else {
        ElMessage.error('导入故障映射失败：' + error.message);
      }
    }
  };
  input.click();
}

async function loadTestPointFaultMappings() {
  if (!activeMsfg.value) {
    console.warn('没有活跃的MSFG，无法加载测试点-故障映射');
    return;
  }

  testPointFaultMappingsLoading.value = true;
  try {
    // 加载可用的测试点（从活跃MSFG）
    availableTestPointsForFault.value = activeMsfg.value.test_names || [];

         // 加载现有映射
     const mappingsRes = await api.get(`/msfg/testpoint-fault-mappings/`, {
       params: { msfg_definition_id: activeMsfg.value.id }
     });
    
    if (Array.isArray(mappingsRes.data)) {
      testPointFaultMappings.value = mappingsRes.data.map(it => ({
        test_point_name: it.test_point_name,
        fault_name: it.fault_name,
        mapping_type: it.mapping_type || 'one_to_one',
        weight: (typeof it.weight === 'number') ? it.weight : Number(it.weight ?? 1.0),
        confidence: (typeof it.confidence === 'number') ? it.confidence : Number(it.confidence ?? 0.5),
        description: it.description || ''
      }));
    } else {
      testPointFaultMappings.value = [];
    }
    
    console.log('测试点-故障映射加载完成:', testPointFaultMappings.value.length);
  } catch (error) {
    console.error('加载测试点-故障映射失败:', error);
    const errorMsg = error.response?.data?.error || error.message || '加载测试点-故障映射失败';
    ElMessage.error(`加载测试点-故障映射失败：${errorMsg}`);
    testPointFaultMappings.value = [];
  } finally {
    testPointFaultMappingsLoading.value = false;
  }
}

async function saveTestPointFaultMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  // 验证映射数据
  const valid = testPointFaultMappings.value.filter(m => m.test_point_name && m.fault_name);
  if (valid.length === 0) {
    ElMessage.warning('没有有效的测试点-故障映射数据需要保存');
    return;
  }
  
  // 检查重复映射
  const mappingKeys = new Set();
  const duplicates = [];
  for (const mapping of valid) {
    const key = `${mapping.test_point_name}-${mapping.fault_name}`;
    if (mappingKeys.has(key)) {
      duplicates.push(key);
    } else {
      mappingKeys.add(key);
    }
  }
  
  if (duplicates.length > 0) {
    ElMessage.warning(`发现重复测试点-故障映射：${duplicates.join(', ')}，将保留最后一个`);
  }
  
  savingTestPointFaultMappings.value = true;
  try {
    const response = await api.post(`/msfg/testpoint-fault-mappings/batch/`, {
      msfg_definition_id: activeMsfg.value.id,
      mappings: valid
    });
    
    if (response.data && response.data.saved !== undefined) {
      ElMessage.success(`测试点-故障映射保存成功，共保存 ${response.data.saved} 个映射`);
    } else {
      ElMessage.success('测试点-故障映射保存成功');
    }
    
    await loadTestPointFaultMappings();
  } catch (e) {
    console.error('保存测试点-故障映射失败:', e);
    const errorMsg = e.response?.data?.error || e.message || '保存测试点-故障映射失败';
    ElMessage.error(`保存测试点-故障映射失败：${errorMsg}`);
  } finally { 
    savingTestPointFaultMappings.value = false; 
  }
}

async function exportTestPointFaultMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  const validMappings = testPointFaultMappings.value.filter(m => m.test_point_name && m.fault_name);
  if (validMappings.length === 0) {
    ElMessage.warning('没有可导出的测试点-故障映射数据');
    return;
  }
  
  const exportData = {
    msfg_definition_name: activeMsfg.value.name,
    export_time: new Date().toISOString(),
    mappings: validMappings
  };
  
  const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `testpoint_fault_mappings_${activeMsfg.value.name}_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  
  ElMessage.success(`测试点-故障映射导出成功，共导出 ${validMappings.length} 个映射`);
}

async function importTestPointFaultMappings() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = '.json';
  input.onchange = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
      const text = await file.text();
      const data = JSON.parse(text);
      
      // 验证导入数据
      const validation = validateImportData(data, 'testpoint_fault');
      if (!validation.valid) {
        ElMessage.error(`导入数据验证失败：${validation.error}`);
        return;
      }
      
      // 检查MSFG定义ID匹配
      if (data.msfg_definition_id && data.msfg_definition_id !== activeMsfg.value.id) {
        const confirm = await ElMessageBox.confirm(
          `导入的映射数据来自不同的MSFG定义，是否继续导入？`,
          '确认导入',
          { confirmButtonText: '继续导入', cancelButtonText: '取消', type: 'warning' }
        );
        if (!confirm) return;
      }
      
      // 验证映射数据格式
      const validMappings = [];
      for (const mapping of data.mappings) {
        if (mapping.test_point_name && mapping.fault_name) {
          validMappings.push({
            test_point_name: mapping.test_point_name,
            fault_name: mapping.fault_name,
            mapping_type: mapping.mapping_type || 'one_to_one',
            weight: Number(mapping.weight || 1.0),
            confidence: Number(mapping.confidence || 0.8),
            description: mapping.description || ''
          });
        }
      }
      
      if (validMappings.length === 0) {
        ElMessage.warning('导入的数据中没有有效的测试点-故障映射');
        return;
      }
      
      // 替换现有映射
      testPointFaultMappings.value = validMappings;
      ElMessage.success(`测试点-故障映射导入成功，共导入 ${validMappings.length} 个映射`);
      
    } catch (error) {
      console.error('导入测试点-故障映射失败:', error);
      ElMessage.error(`导入测试点-故障映射失败：${error.message}`);
    }
  };
  input.click();
}

async function onCmgModelChange(){
  await loadActiveMsfgTestNames();
  await loadTPRules();
}

// 监听MSFG状态变化
function setupMsfgChangeListener() {
  // 监听来自iframe的消息
  window.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'MSFG_STATUS_CHANGED') {
      console.log('检测到MSFG状态变化，重新加载活跃MSFG');
      loadActiveMsfgTestNames().then(() => {
        // 如果当前有选中的CMG模型，刷新部件对应管理页面
        if (query.value.cmgModelId && activeMsfg.value) {
          console.log('刷新部件对应管理页面');
          refreshComponentMappings();
        }
      });
    }
  });
}

// D矩阵相关方法
async function showDMatrix() {
  if (!activeMsfg.value) {
    ElMessage.error('没有活跃的MSFG');
    return;
  }
  
  dMatrixDialog.value = true;
  dMatrixLoading.value = true;
  
  try {
    const response = await api.get(`/msfg/msfg-definitions/${activeMsfg.value.id}/d-matrix/`);
    dMatrixData.value = response.data;
    showMatrixValues.value = false; // 默认显示连接关系
  } catch (error) {
    console.error('获取D矩阵失败:', error);
    ElMessage.error('获取D矩阵失败：' + (error.response?.data?.error || error.message));
    dMatrixData.value = null;
  } finally {
    dMatrixLoading.value = false;
  }
}

function getMatrixCellClass(faultIndex, testIndex) {
  const value = dMatrixData.value?.matrix[faultIndex]?.[testIndex] || 0;
  if (value === 0) return 'matrix-cell empty';
  if (value >= 0.8) return 'matrix-cell strong';
  if (value >= 0.5) return 'matrix-cell medium';
  return 'matrix-cell weak';
}

function showCellDetails(faultIndex, testIndex) {
  const fault = dMatrixData.value?.fault_names[faultIndex];
  const test = dMatrixData.value?.test_names[testIndex];
  const value = dMatrixData.value?.matrix[faultIndex]?.[testIndex] || 0;
  
  if (value > 0) {
    ElMessage.info(`故障 "${fault}" 与测试点 "${test}" 的依赖强度: ${value.toFixed(3)}`);
  }
}

async function exportDMatrix() {
  if (!dMatrixData.value) {
    ElMessage.error('没有D矩阵数据可导出');
    return;
  }
  
  try {
    const exportData = {
      msfg_definition_id: activeMsfg.value.id,
      msfg_name: activeMsfg.value.name,
      export_time: new Date().toISOString(),
      matrix_data: dMatrixData.value
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `D矩阵_${activeMsfg.value.name}_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    ElMessage.success('D矩阵导出成功');
  } catch (error) {
    console.error('导出D矩阵失败:', error);
    ElMessage.error('导出D矩阵失败：' + error.message);
  }
}

onMounted(async () => {
  await loadCmgModels();
  await loadActiveMsfgTestNames();
  await loadTPRules();
  setupMsfgChangeListener();
});
</script>

<style scoped>
.tp-rules-page { padding: 12px; }
.toolbar { margin-bottom: 12px; }

/* D矩阵样式 */
.d-matrix-dialog .el-dialog__body {
  padding: 20px;
}

.matrix-info {
  margin-bottom: 20px;
}

.info-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.info-item {
  text-align: center;
  padding: 10px;
}

.info-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 5px;
}

.info-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.matrix-display {
  margin-bottom: 30px;
}

.matrix-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 2px solid #409eff;
}

.matrix-header h3 {
  margin: 0;
  color: #303133;
  font-size: 16px;
}

.matrix-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.matrix-table-container {
  overflow-x: auto;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.d-matrix-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}

.d-matrix-table th,
.d-matrix-table td {
  border: 1px solid #e4e7ed;
  padding: 8px;
  text-align: center;
  vertical-align: middle;
  min-width: 80px;
  max-width: 120px;
  word-wrap: break-word;
}

.corner-cell {
  background: #f5f7fa;
  font-weight: bold;
  color: #606266;
  min-width: 120px;
  max-width: 150px;
}

.test-header {
  background: #e1f3d8;
  font-weight: bold;
  color: #67c23a;
  transform: rotate(-45deg);
  height: 80px;
  vertical-align: bottom;
}

.test-name {
  transform: rotate(45deg);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.fault-header {
  background: #fef0f0;
  font-weight: bold;
  color: #f56c6c;
  text-align: left;
  min-width: 120px;
  max-width: 150px;
}

.fault-name {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 120px;
}

.matrix-cell {
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.matrix-cell:hover {
  background-color: #f0f9ff;
  transform: scale(1.05);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.matrix-cell.empty {
  background-color: #fafafa;
}

.matrix-cell.weak {
  background-color: #f0f9ff;
}

.matrix-cell.medium {
  background-color: #e6f7ff;
}

.matrix-cell.strong {
  background-color: #bae7ff;
}

.cell-value {
  font-weight: bold;
  color: #1890ff;
  font-size: 11px;
}

.cell-connection {
  color: #52c41a;
  font-size: 14px;
  font-weight: bold;
}

.diagnostic-analysis {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e4e7ed;
}

.diagnostic-analysis h3 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.analysis-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
}

.analysis-item {
  text-align: center;
  padding: 15px;
}

.analysis-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.analysis-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 10px;
}

.analysis-detail {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 4px;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}
</style>



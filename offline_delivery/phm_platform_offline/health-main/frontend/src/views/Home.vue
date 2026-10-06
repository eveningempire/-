<template >
<dv-full-screen-container class="background">
    <div class="module-box">
        <div style = "flex:0 1 30%">
      <dv-decoration-10 style="width:100%;height:5px;" />
      <div style="display: flex; justify-content: space-between;align-items: center; ">
            <div class="ate">ATE</div>
            <div style="display: flex; flex-direction: row;align-items: center; gap: 10px;">
            <div class="date">{{ currentDate }}</div>
            <div class="time">{{ currentTime }}</div>
          </div>
          <dv-decoration1 style="width:200px;height:50px;" />
          </div>
        </div>
        <div style = "flex:0 1 40%">
            <div class="d-flex">
                <dv-decoration8 style="width:30%;height:50px; flex: 1;" />
                <dv-decoration-11 style="width:40%;height:60px; flex: 1;" >
                 <div class="dv-decoration-111">
                    健康管理平台
                 </div>
                </dv-decoration-11>
                <dv-decoration8 :reverse="true" style="width:30%;height:50px; flex: 1; " />
            </div>
        </div>
        <div style = "flex:0 1 30%">
<dv-decoration-10 style="width:100%;height:5px;  transform: rotateY(180deg);" />
<div style="display: flex; justify-content: row;align-items: center; gap: 20px;">
              <dv-decoration1 style="width:200px;height:50px; transform: rotateY(180deg);" />
              <div style="display: flex; flex-direction: row;align-items: center; gap: 50px;">
                <div style="display: flex; flex-direction: row;align-items: center; gap: 10px;">
              <el-icon :size="32" color="white"><UserFilled /></el-icon>
              <div class="username">{{ currentUser }}</div></div>
              <dv-button @click="showLogoutDialog" border="Border6" color="#615ea8">注销登录</dv-button>
              <el-dialog
                    title="确认注销"
                    v-model="logoutDialogVisible"
                    width="30%"
                  >
                    <span>确定要注销登录吗?</span>
                    <template #footer>
                      <el-button @click="cancelLogout">取消</el-button>
                      <el-button type="primary" @click="confirmLogout">确定</el-button>
                    </template>
                </el-dialog>
            </div>
            </div>
        </div>
    </div>

    <div class="module-box2">
    <div style = "flex:0 1 30%">
        <div class="boxall" style="height: 388px; width:100%;  margin-left: 5px;">
            <div class="tit01">整器可靠性</div>
            <div style="display: flex;  flex-direction:row ; justify-content: center; align-items: center; gap: 50px; margin-top: 20px;">
            <!-- <div style="display: flex;  flex-direction:column ; justify-content: center; align-items: center; gap: 5px;">
            <dv-decoration-9 style="width:150px;height:150px;">
            <div style="color: red; font-weight: bold; font-size: 30px;"  bg="~ dark/0">
             66%
            </div>
            </dv-decoration-9>
            <div style="color: white; font-weight: bold; font-size: 24px; ">可靠度</div>
            </div>
            <div style="display: flex;  flex-direction:column ; justify-content: center; align-items: center; gap: 5px;">
            <dv-decoration-9 style="width:150px;height:150px;">
            <div style="color: red; font-weight: bold; font-size: 30px;"  bg="~ dark/0">
             66%
            </div>
            </dv-decoration-9>
            <div style="color: white; font-weight: bold; font-size: 24px; ">可用度</div>
            </div> -->
            <div style="display: flex;  flex-direction:column ; justify-content: center; align-items: center; gap: 5px;">
            <dv-decoration-9 style="width:150px;height:150px;">
            <div style="color: red; font-weight: bold; font-size: 30px;"  bg="~ dark/0">
             {{ system_index }}%
            </div>
            </dv-decoration-9>
            <div style="color: white; font-weight: bold; font-size: 24px; ">健康度</div>
            
            </div>
            <div style="display: flex;  flex-direction:column ; justify-content: center; align-items: center; gap: 5px;">
            <dv-decoration-9 style="width:150px;height:150px;">
            <div style="color: red; font-weight: bold; font-size: 30px;"  bg="~ dark/0">
             {{ confidence }}%
            </div>
            </dv-decoration-9>
            <div style="color: white; font-weight: bold; font-size: 24px; ">置信度</div>
            </div>
            </div>
            <div style="display: flex;  flex-direction:row ; justify-content: center; align-items: center; gap: 50px;">
            <div style="display: flex;  flex-direction:column ; justify-content: center; align-items: center; gap: 5px;">
            <dv-percent-pond :config="progress" style="width:200px;height:100px; margin-top: 25px;" />
            <div style="color: white; font-weight: bold; font-size: 22px;">算法进度</div>
            </div>
            <div style="display: flex;  flex-direction:column; justify-content: center; align-items: center; gap: 20px;">
                 <dv-button @click="start_evaluate" border="Border4" color="#a6559d">开始评估</dv-button>
                 <div style="color: yellowgreen; font-weight: bold; font-size: 22px;">再飞判定结果:{{ finalresult }}</div>
            </div>
            </div>


        <div class="boxfoot"></div>

    </div>

    <div class="boxall" style="height: 388px; width:100%; margin-left: 5px;">
      
        <div class="tit01">部件剩余寿命</div>
        <el-select v-model="value" placeholder="请选择部件" style="width: 240px; margin-top: 20px; margin-left: 150px;" @change="handleSelectChange2">
        <el-option
        v-for="item in options"
        :key="item.value"
        :label="item.label"
        :value="item.value"
        :disabled="item.disabled"
        />
        </el-select>
        <div style="width: 420px; height: 250px; margin-top: 20px; margin-left: 40px; " id="echart1"></div>
        <div style="display: flex; flex-direction: row; margin-top: 10px;">
        <div style="color: yellowgreen; font-weight: bold; font-size: 22px; margin-top: 1px; margin-left: 100px;" >剩余寿命:{{ remainlife }}</div>
        <div style="color: yellowgreen; font-weight: bold; font-size: 22px; margin-top: 1px; margin-left: 50px;" >健康度:{{ component_index }}</div>
        </div>

        <div class="boxfoot"></div>

    </div>

    </div>

    <div style = "flex:0 1 40%">
        <!-- <div style="height: 80px; width:90%;  margin-left: 45px;  display: flex;   justify-content: center; align-items: center; gap: 50px;">
            <dv-button @click="console.log('click')" border="Border2" color="#4c8045">模型监控</dv-button>
            <dv-button @click="console.log('click')" border="Border2" color="#4c8045">状态监测</dv-button>

        </div> -->
        <div class="boxall" style="height: 337px; width:90%;  margin-left: 45px;">
            <!-- <div class="tit01">模型监控</div> -->
             <ThreeModel style="height: 95%; width:95%; " />
        <div class="boxfoot"></div>
    </div>
        <div class="boxall" style="height: 338px; width:90%;  margin-left: 45px;">
            <!-- <div class="tit01">状态检测</div> -->
          <div>
            <div style = "display: flex; direction: row; gap:30px">
          <el-select v-model="value2" placeholder="请选择参数" style="width: 240px; margin-top: 5px; margin-left: 150px;" @change="handleSelectChange">
          <el-option
          v-for="item in options2"
          :key="item.value"
          :label="item.label"
          :value="item.value"
          />
          </el-select>
          <dv-button :bg="false" @click="Anomaly">异常检测</dv-button></div>
          <div style="width: 420px; height: 350px; margin-top: 10px; margin-left: 40px; " id="echart2"></div>
          </div>


        <div class="boxfoot"></div>
    </div>
    
    <div class="boxall" style="height: 60px; width:90%;  margin-left: 45px; display: flex;   justify-content: center; align-items: center; gap: 50px;">
            <!-- <div class="tit01">状态检测</div> -->
             <dv-button @click="fault_dialog" border="Border5" color="#e18a3b">诊断结果</dv-button>
             <dv-button @click="show_troubleshoot" border="Border5" color="#e18a3b">维修排故</dv-button>
             <dv-button @click="show_ietm" border="Border5" color="#e18a3b">维修手册</dv-button>
             <dv-button @click="export_report" border="Border5" color="#e18a3b">报告导出</dv-button>



        <div class="boxfoot"></div>
    </div>

    </div>

    <div style = "flex:0 1 30%">
        <div class="boxall" style="height: 100px; width:90%;  margin-left: 20px;">
            <div class="tit01">编辑区域</div>
            <div style="display: flex;   justify-content: center; align-items: center; gap: 20px; margin-top: 28px;">
            <dv-button @click="Algorithm" border="Border3" color="#c8161d" font-color="#e18a3b">算法配置</dv-button>
            <dv-button @click="show_knowledge" border="Border3" color="#c8161d" font-color="#e18a3b">知识管理</dv-button>
            <dv-button @click="show_model" border="Border3" color="#c8161d" font-color="#e18a3b">模型管理</dv-button>
            <dv-button @click="show_right" border="Border3" color="#c8161d" font-color="#e18a3b">用户管理</dv-button>
            </div>
        <div class="boxfoot"></div>
    </div>
    <div class="boxall" style="height: 318px; width:90%;  margin-left: 20px;">
            <div class="tit01">子系统健康度</div>
            <div style="display: flex;   justify-content: center; align-items: center; gap: 50px; margin-top: 20px;">
            <div style="display: flex;  flex-direction: column; justify-content: center; align-items: center; gap: 10px; margin-top: 20px;">
            <dv-water-level-pond :config="powersys" style="width:200px;height:200px" />
            <div style="color: white; font-weight: bold; font-size: 24px; ">动力系统</div>
            </div>
            <div style="display: flex;  flex-direction: column; justify-content: center; align-items: center; gap: 10px; margin-top: 20px;">
            <dv-water-level-pond :config="controlsys" style="width:200px;height:200px" />
            <div style="color: white; font-weight: bold; font-size: 24px; ">飞控系统</div>
            </div>
            </div>
        <div class="boxfoot"></div>
    </div>
    <div class="boxall" style="height: 318px; width:90%;  margin-left: 20px;">
            <div class="tit01">系统故障情况</div>
            <dv-scroll-ranking-board :config="faultlist" style="width:500px;height:300px" />


        <div class="boxfoot"></div>
    </div>
    <div
      v-if="hier14WindowSeries.length"
      class="boxall"
      style="height: 360px; width:90%; margin-left: 20px;"
    >
      <div class="tit01">Hier14 滑窗诊断时序</div>
      <div id="echart_hier14" style="width:500px;height:300px;margin-top:10px;"></div>
      <div class="boxfoot"></div>
    </div>

    </div>
<el-dialog
      title="算法配置"
      v-model="showalgorithm"
      width="1000px"
      @close="cancelDialog_algorithm"
    >
    <div class= "containerselect">
  <h3>模型故障诊断算法选择</h3>
  <el-select v-model="value3" placeholder="请选择模型故障诊断算法" style="width: 240px">
      <el-option
        v-for="item in options3"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
  </el-select>
</div>
<div class= "containerselect">
  <h3>机器学习诊断算法选择</h3>
  <el-select v-model="value7" placeholder="请选择机器学习诊断算法" style="width: 240px">
      <el-option
        v-for="item in options7"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
  </el-select>
</div>
<div class= "containerselect">
  <h3>子系统评估算法选择</h3>
  <el-select v-model="value4" placeholder="请选择子系统评估算法" style="width: 240px">
      <el-option
        v-for="item in options4"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
  </el-select>
</div>
<div class= "containerselect">
  <h3>系统评估算法选择</h3>
  <el-select v-model="value5" placeholder="请选择系统评估算法" style="width: 240px">
      <el-option
        v-for="item in options5"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
  </el-select>
</div>
<div class= "containerselect">
  <h3>寿命预测算法选择</h3>
  <el-select v-model="value6" placeholder="请选择寿命预测算法" style="width: 240px">
      <el-option
        v-for="item in options6"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
  </el-select>
</div>
<div class= "containerselect">
  <h3>维修排故算法选择</h3>
  <el-select v-model="value8" placeholder="请选择维修排故算法" style="width: 240px">
      <el-option
        v-for="item in options8"
        :key="item.value"
        :label="item.label"
        :value="item.value"
      />
  </el-select>
</div>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelDialog_algorithm">取消</el-button>
        <el-button type="primary" @click="confirmDialog_algorithm">确认</el-button>
      </div>
    </el-dialog>
    
 </div>

 <el-dialog
      title="异常检测结果"
      v-model="showanomaly"
      width="900px"
      @close="cancelDialog_anomaly"
    >
    <div style="display: flex; flex-wrap: wrap; gap: 10px; ">
    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">氧泵出口压强</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P1"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">氧涡轮转速</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P2"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">煤油出口压强</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P3"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">煤油出口流量</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P4"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">燃气压强</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P5"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">燃烧室压强</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P6"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">发动机推力</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P7"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">发动机偏角</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P8"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">栅格舵偏角</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P9"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">RCS输出力矩</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P10"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">舵机电流</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P11"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">欧拉角</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P12"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">液氧出口压强</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P14"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">液氧出口流量</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P15"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">煤油泵压强</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P16"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    <div style="display: flex; align-items: center; gap: 10px;">
    <div style="width: 150px; color: black; font-weight: bold;">煤油涡轮转速</div>
    <div style="display: flex; align-items: center; position: relative; width: 100%;">
      <el-switch
        v-model="P17"
        class="mb-2"
        style="--el-switch-on-color: #13ce66; --el-switch-off-color: #ff4949"
        active-text="故障"
        inactive-text="正常"
      />
    </div>
    </div>

    </div>


    <div slot="footer" class="dialog-footer" style="margin-top: 20px;">
        <el-button @click="cancelDialog_anomaly">取消</el-button>
        <el-button type="primary" @click="cancelDialog_anomaly">确认</el-button>
      </div>
    </el-dialog>


<el-dialog
      title="故障诊断结果"
      v-model="showdiagresult"
      width="1500px"
      @close="cancelDialog_diagresult"
      @opened="onDiagResultOpened"
    >
    <div>
      <el-card style="width: 1200px">
      <template #header>
      <div class="card-header">
        <span>诊断为正常</span>
      </div>
    </template>
    <div class="button-container">
      <div class="spacer"></div> <!-- 用于调整第一行按钮左侧距离 -->
    <el-button 
      v-for="(fault, index) in G_faults" 
      :key="index" 
      type="success" style="width: 250px">
      {{ fault }}
    </el-button>
    </div>
      </el-card>
      <el-card style="width: 1200px">
      <template #header>
      <div class="card-header">
        <span>诊断为故障</span>
      </div>
    </template>
    <div class="button-container">
      <div class="spacer"></div> <!-- 用于调整第一行按钮左侧距离 -->
    <el-button 
      v-for="(fault, index) in B_faults" 
      :key="index" 
      type="danger" style="width: 250px">
      {{ fault }}
    </el-button></div>
      </el-card>

      <el-card style="width: 1200px">
      <template #header>
      <div class="card-header">
        <span>诊断为怀疑</span>
      </div>
    </template>
    <div class="button-container">
      <div class="spacer"></div> <!-- 用于调整第一行按钮左侧距离 -->
    <el-button 
      v-for="(fault, index) in S_faults" 
      :key="index" 
      type="warning" style="width: 250px">
      {{ fault }}
    </el-button></div>
      </el-card>
      <el-card style="width: 1200px">
      <template #header>
      <div class="card-header">
        <span>诊断为未知</span>
      </div>
    </template>
    <div class="button-container">
      <div class="spacer"></div> <!-- 用于调整第一行按钮左侧距离 -->
    <el-button 
      v-for="(fault, index) in U_faults" 
      :key="index" 
      type="info" style="width: 250px">
      {{ fault }}
    </el-button></div>
      </el-card>
      <el-card v-if="hier14WindowSeries.length" style="width: 1200px; margin-top: 16px;">
        <template #header>
          <div class="card-header">
            <span>Hier14 滑窗诊断时序({{ hier14WindowSeries.length }} 个窗口)</span>
          </div>
        </template>
        <div id="echart_hier14_dialog" style="width: 1100px; height: 420px;"></div>
      </el-card>
    </div>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelDialog_diagresult">取消</el-button>
        <el-button type="primary" @click="confirmDialog_diagresult">确认</el-button>
      </div>
</el-dialog>
 

<el-dialog
      title="维修排故决策"
      v-model="showdiagtroubleshoot"
      width="1500px"
      @close="cancelDialog_troubleshoot"
    >
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
      

  <el-table :data="troubleshoot_table" stripe style="width: 100%" class="black-border-table"  border>
  <el-table-column prop="number" label="动作编号" width="600"  align="center"/>
  <el-table-column prop="operate" label="维修动作" width="600"  align="center"/>
  </el-table>
      
   <el-button type="success" @click="operate_troubleshoot">执行动作</el-button>
   
   
    </div>
    
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelDialog_troubleshoot">取消</el-button>
        <el-button type="primary" @click="confirmDialog_troubleshoot">确认</el-button>
      </div>
</el-dialog>


<el-dialog
      title="维修手册"
      v-model="showdiagietm"
      width="800px"
      @close="cancelDialog_ietm"
    >
    <div style="display:flex; flex-direction: column;justify-content: center; align-items: center; gap: 20px;">

      <div v-if="fault_name==='无故障'">
        <p>无故障</p>
        <div>无需维修</div>
      </div>
      <div v-if="fault_name==='泵气蚀'">
        <p>泵气蚀故障</p>
        <div>工具准备:专用扳手、密封件、测量仪器、防护装备、清洗剂。</div>
        <div>故障现象:泵体异响、性能下降、出口压力波动、异常振动。</div>
        <div>维修操作:拆卸检查、更换损坏件、清洁流道、重新装配调试。</div>
      </div>
      <div v-if="fault_name==='涡轮转速下降'">
        <p>涡轮转速下降故障</p>
        <div>工具准备:转速表、专用扳手、万用表、清洗剂、更换部件。</div>
        <div>故障现象:功率输出不足、加速缓慢、异响振动、仪表显示异常。</div>
        <div>维修操作:通过维修排故检查、做好润滑与密封、清洗叶轮、更换损坏件、校准调试。</div>
      </div>
       <div v-if="fault_name==='管路堵塞'">
        <p>管路堵塞故障</p>
        <div>工具准备:专用扳手、高压清洗机、疏通工具、密封件、检测仪器。</div>
        <div>故障现象:流量不足、压力异常、发动机功率下降、接头渗漏。</div>
        <div>维修操作:分段排查堵塞点、高压清洗疏通、更换密封、测试密封性。</div>
      </div>
      <div v-if="fault_name==='主阀门卡滞'">
        <p>主阀门卡滞故障</p>
        <div>工具准备:阀门专用扳手、润滑剂、清洗剂、密封件、万用表。</div>
        <div>故障现象:阀门操作阻力大、开关不到位、流量调节失灵。</div>
        <div>维修操作:解除联动机构、清洗阀杆阀座、润滑活动部件、复位测试。</div>
      </div>
      <div v-if="fault_name==='燃气泄漏'">
        <p>燃气泄漏故障</p>
        <div>工具准备:可燃气体检测仪、防爆工具、密封材料、肥皂水检漏剂。</div>
        <div>故障现象:异味明显、压力表读数异常下降、听到嘶嘶气流声。</div>
        <div>维修操作:立即通风禁火、定位泄漏点、紧固或更换密封件、复查确认。</div>
      </div>
      <div v-if="fault_name==='燃烧不稳定'">
        <p>燃烧不稳定故障</p>
        <div>工具准备:压力表、火花塞扳手、内窥镜、清洗剂、燃料检测仪。</div>
        <div>故障现象:火焰闪烁或熄灭、异常爆震、出口温度剧烈波动。</div>
        <div>维修操作:检查清理喷嘴与火花塞、校准燃料比例、更换失效部件。</div>
      </div>
      <div v-if="fault_name==='喷管堵塞'">
        <p>喷管堵塞故障</p>
        <div>工具准备:内窥镜、专用通杆、高压清洗设备、防护镜、扳手。</div>
        <div>故障现象:推力下降、出口流场不对称、温度异常升高。</div>
        <div>维修操作:内窥镜检查确认、机械或高压疏通、清除积碳异物。</div>
      </div>
      <div v-if="fault_name==='TVC偏角不足'">
        <p>TVC偏角不足故障</p>
        <div>工具准备:作动筒专用工具、万用表、角度规、密封件、润滑剂。</div>
        <div>故障现象:矢量角度不达标、作动器响应迟缓、飞行姿态异常。</div>
        <div>维修操作:检查作动器与传感器、校准零位、更换磨损部件、重新测试。</div>
      </div>
      <div v-if="fault_name==='RCS推力不足'">
        <p>RCS推力不足故障</p>
        <div>工具准备:压力表、流量计、万用表、密封工具、专用扳手。</div>
        <div>故障现象:姿态调整迟缓、喷口脉冲异常、压力读数偏低。</div>
        <div>维修操作:检查电磁阀与管路、清洁喷注器、测试密封与电路。</div>
      </div>
      <div v-if="fault_name==='栅格舵偏角不足'">
        <p>栅格舵偏角不足故障</p>
        <div>工具准备:舵面专用工具、角度测量仪、万用表、润滑剂、校准设备。</div>
        <div>故障现象:舵面响应迟钝、实际偏角小于指令、飞行轨迹偏差。</div>
        <div>维修操作:检查传动机构、校准传感器与限位、润滑关节轴承。</div>
      </div>
      <div v-if="fault_name==='控制器无信号'">
        <p>控制器无信号故障</p>
        <div>工具准备:万用表、示波器、备用线缆、接口工具、防静电设备。</div>
        <div>故障现象:指示灯异常、无指令输出、数据中断、设备无响应。</div>
        <div>维修操作:检查供电与接地、测试接口线路、更换故障模块。</div>
      </div>
      <div v-if="fault_name==='陀螺仪恒偏差'">
        <p>陀螺仪恒偏差故障</p>
        <div>工具准备:校准设备、精密螺丝刀、万用表、无尘布、防静电工具。</div>
        <div>故障现象:姿态读数持续漂移、导航轨迹偏离、校准无效。</div>
        <div>维修操作:清洁内部光学部件、校准基准参数、更换故障单元。</div>
      </div>
      <div v-if="fault_name==='陀螺仪卡死'">
        <p>陀螺仪恒偏差故障</p>
        <div>工具准备:无尘手套、精密工具、清洁剂、润滑剂、测试电源。</div>
        <div>故障现象:转子无法启动、输出信号恒定不变、伴随异常摩擦声。</div>
        <div>维修操作:分解清洁轴承组件、更换卡滞转子、润滑后重新校准。</div>
      </div>
    </div>
    
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelDialog_ietm">取消</el-button>
        <el-button type="primary" @click="confirmDialog_ietm">确认</el-button>
      </div>
</el-dialog>


<el-dialog
      title="知识管理"
      v-model="showkonwledge"
      width="1500px"
      @close="cancelDialog_knowledge"
    >
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">

    <el-table :data="fmeca_table" stripe style="width: 100%; display:flex; flex-direction: row;justify-content: center; align-items: center;" class="black-border-table"  border>
  <el-table-column prop="component" label="部件名称" width="200"  align="center"/>
  <el-table-column prop="fault_name" label="故障名称" width="200"  align="center"/>
  <el-table-column prop="fault_prob" label="故障概率" width="200"  align="center"/>
  <el-table-column prop="fault_reason" label="故障原因" width="200"  align="center"/>
  <el-table-column prop="degree_harm" label="危害程度" width="200"  align="center"/>
  <el-table-column prop="operation" label="操作" align="center" width="200" >
      <template v-slot:default="scope"  class="button_arrange">
          <el-button @click="handleedit(scope.row)" size="small" type="default" >编辑</el-button>
        </template>
    </el-table-column>
  </el-table>
      

   
    </div>
    
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelDialog_knowledge">取消</el-button>
        <el-button type="primary" @click="confirmDialog_knowledge">确认</el-button>
      </div>
</el-dialog>


<el-dialog
      title="模型管理"
      v-model="showmodel"
      width="1000px"
      @close="cancelDialog_model"
       @opened="echarts_3"
    >
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
      
  <el-tabs v-model="activeName" class="demo-tabs"  style=" width:800px;height: 500px;" @tab-click="handleClick">
    <el-tab-pane label="动力系统" name="first" >
      <div style="width: 800px; height: 500px; margin-top: 20px; margin-left: 40px; " id="echart3"></div>
    </el-tab-pane>
    <el-tab-pane label="飞控系统" name="second">
      <div style="width: 800px; height: 500px; margin-top: 20px; margin-left: 40px; " id="echart4"></div>
    </el-tab-pane>
  </el-tabs>
   
    </div>
    
      <div slot="footer" class="dialog-footer" style="margin-top: 50px;">
        <el-button @click="cancelDialog_model">取消</el-button>
        <el-button type="primary" @click="confirmDialog_model">确认</el-button>
      </div>
</el-dialog>


<el-dialog
      title="权限管理"
      v-model="showright"
      width="1500px"
      @close="cancelDialog_right"
    >
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">

 <el-table :data="user_table" stripe style="width: 100%; display:flex; flex-direction: row;justify-content: center; align-items: center;" Border >
    <el-table-column prop="name" label="用户名称" width="200" align="center" />
    <el-table-column prop="email" label="电子邮箱" width="200"  align="center"/>
    <el-table-column prop="role" label="角色名称" width="200"  align="center"/>
     <el-table-column prop="operation" label="操作" align="center" width="400" >
      <template v-slot:default="scope"  class="button_arrange">
          <el-button @click="edituser(scope.row)" size="small" type="success" >编辑</el-button>
          <el-button @click="deleteuser(scope.row)" size="small" type="danger" >删除</el-button>
        </template>
    </el-table-column>
  </el-table>
    </div>
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelDialog_right">取消</el-button>
        <el-button type="primary" @click="confirmDialog_right">确认</el-button>
        <el-button type="info" @click="add_user">增加用户</el-button>
      </div>
</el-dialog>

<el-dialog
      title="FMECA修改"
      v-model="show_editfmeca"
      width="800px"
      @close="cancelDialog_right"
    >
    <div style="display:flex; flex-direction: column;justify-content: center; align-items: center; gap: 20px;">

      <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 10px;">
        <div style="width:100px">部件名称:</div>
        <el-input v-model="input1" placeholder="请输入部件名称" />
      </div>
      <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 10px;">
        <div style="width:100px">故障名称:</div>
        <el-input v-model="input2" placeholder="请输入故障名称" />
      </div>
      <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 10px;">
        <div style="width:100px">故障概率:</div>
        <el-input v-model="input3" placeholder="请输入故障概率" />
      </div>
      <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 10px;">
        <div style="width:100px">故障原因:</div>
        <el-input v-model="input4" placeholder="请输入故障原因" />
      </div>

      <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 10px;">
        <div style="width:100px">危害等级:</div>
        <el-input v-model="input5" placeholder="请输入危害等级" />
      </div>
   
    </div>
    
      <div slot="footer" class="dialog-footer">
        <el-button @click="cancelDialog_editfmeca">取消</el-button>
        <el-button type="primary" @click="confirmDialog_editfmeca">确认</el-button>
      </div>
</el-dialog>

<el-dialog
      title="增加用户"
      v-model="showadduser"
      width="500px"
      @close="cancelDialog_adduser"
    >
    <div style="display:flex; flex-direction: column;justify-content: center; align-items: center; gap: 20px;">
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">用户ID:</div>
    <el-input v-model="adduser0" placeholder="请输入ID" style="width: 150px" disabled></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">用户名:</div>
    <el-input v-model="adduser1" placeholder="请输入用户名" style="width: 150px"></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">电子邮箱:</div>
    <el-input v-model="adduser2" placeholder="请输入电子邮箱" style="width: 150px"></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">密码:</div>
    <el-input v-model="adduser3" placeholder="请输入密码" style="width: 150px"></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">角色:</div>
     <el-select v-model="value10" placeholder="请选择用户角色" style="width: 150px">
    <el-option
      v-for="item in adduser3table"
      :key="item.value"
      :label="item.label"
      :value="item.value"
    />
  </el-select>
    </div>
    </div>
    
      <div slot="footer" class="dialog-footer" style="margin-top: 50px;">
        <el-button @click="cancelDialog_adduser">取消</el-button>
        <el-button type="primary" @click="confirmDialog_adduser">确认</el-button>
      </div>
</el-dialog>

<el-dialog
      title="删除用户"
      v-model="showdeluser"
      width="500px"
      @close="cancelDialog_deluser"
    >
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">

    你确定要删除此用户吗?
    </div>
    
      <div slot="footer" class="dialog-footer" style="margin-top: 50px;">
        <el-button @click="cancelDialog_deluser">取消</el-button>
        <el-button type="primary" @click="confirmDialog_deluser">确认</el-button>
      </div>
</el-dialog>
<el-dialog
      title="编辑用户"
      v-model="showedituser"
      width="500px"
      @close="cancelDialog_edituser"
    >
    <div style="display:flex; flex-direction: column;justify-content: center; align-items: center; gap: 20px;">
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">用户ID:</div>
    <el-input v-model="edituser0" placeholder="请输入ID" style="width: 150px" disabled></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">用户名:</div>
    <el-input v-model="edituser1" placeholder="请输入用户名" style="width: 150px"></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">电子邮箱:</div>
    <el-input v-model="edituser2" placeholder="请输入电子邮箱" style="width: 150px"></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">密码:</div>
    <el-input v-model="edituser3" placeholder="请输入密码" style="width: 150px"></el-input>
    </div>
    <div style="display:flex; flex-direction: row;justify-content: center; align-items: center; gap: 20px;">
    <div style="width:100px">角色:</div>
     <el-select v-model="value11" placeholder="请选择用户角色" style="width: 150px">
    <el-option
      v-for="item in adduser3table"
      :key="item.value"
      :label="item.label"
      :value="item.value"
    />
  </el-select>
    </div>
    </div>
      <div slot="footer" class="dialog-footer" style="margin-top: 50px;">
        <el-button @click="cancelDialog_edituser">取消</el-button>
        <el-button type="primary" @click="confirmDialog_edituser">确认</el-button>
      </div>
</el-dialog>
</dv-full-screen-container>


 </template>


<script>
import { ref,reactive,onMounted , nextTick } from 'vue';
import { UserFilled } from '@element-plus/icons-vue';
import * as echarts from "echarts";
import ThreeModel from './ThreeModel.vue';
import axios from "axios";
import { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, AlignmentType,Media  } from 'docx';
export default{

    data(){
        return{
          activeName:ref('first'),
          activeName2:ref('first'),
          currentUser:'ATE',
          currentRole:[],
          showadduser:false,
          showdeluser:false,
          showedituser:false,
          user_table:[],
          role_table:[],
          right_table:[],
          input1:ref(),
          input2:ref(),
          input3:ref(),
          input4:ref(),
          input5:ref(),
          index_fmeca:-1,
            currentDate: '', // 当前日期
           currentTime: '', // 当前时间
           username:'ate',
           logoutDialogVisible:false,
           powersys:reactive({
                data: [45],
                shape: 'round',
            }),
            controlsys:reactive({
                data: [45],
                shape: 'roundRect',
            }),
            faultlist:reactive({
                 data: [
                             {
                            name: '无故障',
                            value: 100,
                            },

                        ],
                        waitTime:2000000000,
                        unit: '%',
                        rowNum: 5,         // 行数 >= 数据条数,保证全显示
                        carousel: 'none',  // 🚀 不轮播
                                        }),
            progress:reactive({
                value: 0,
                lineDash: [10, 2],
            }),
            finalresult:"否",
            option:"",
            remainlife:"0",
            component_index:0,
            options:[
              {value: 'Option1',label: '液氧泵',disabled: false,},
              {value: 'Option2',label: '液氧涡轮',disabled: false,},
              {value: 'Option3',label: '煤油管路',disabled: false,},
              {value: 'Option4',label: '煤油阀门',disabled: false,},
              {value: 'Option5',label: '燃气发生器',disabled: false,},
              {value: 'Option6',label: '燃烧室',disabled: false,},
              {value: 'Option7',label: '喷管',disabled: false,},
              {value: 'Option8',label: 'TVC',disabled: false,},
              {value: 'Option9',label: 'RCS',disabled: false,},
              {value: 'Option10',label: '栅格舵',disabled: false,},
              {value: 'Option11',label: '传感器',disabled: false,},
              {value: 'Option12',label: '液氧管路',disabled: false,},
              {value: 'Option13',label: '液氧阀门',disabled: false,},
              {value: 'Option14',label: '煤油泵',disabled: false,},
              {value: 'Option15',label: '煤油涡轮',disabled: false,},
              ],
               options2:ref([
              {value: 'Option1',label: 'X方向距离',},
              {value: 'Option2',label: 'Y方向距离',},
              {value: 'Option3',label: '运载器高度',},
              {value: 'Option4',label: '发动机推力',},
              {value: 'Option5',label: '氧泵出口压强',},
              {value: 'Option6',label: '氧涡轮转速',},
              {value: 'Option7',label: '煤油管路出口压强',},
              {value: 'Option8',label: '煤油管路出口流量',},
              {value: 'Option9',label: '燃气发生器压强',},
              {value: 'Option10',label: '燃烧室压强',},
              {value: 'Option11',label: '液氧管路出口压强',},
              {value: 'Option12',label: '液氧管路出口流量',},
              {value: 'Option13',label: '煤油泵出口压强',},
              {value: 'Option14',label: '煤油涡轮转速',},
              {value: 'Option15',label: '发动机偏角',},
              {value: 'Option16',label: '栅格舵偏角',},
              {value: 'Option17',label: 'RCS输出力矩',},
              {value: 'Option18',label: '舵机电流',},
              {value: 'Option19',label: '滚转角',},
              {value: 'Option20',label: '陀螺仪示数',},
              {value: 'Option21',label: '俯仰角',},
              {value: 'Option22',label: '偏航角',},
              {value: 'Option23',label: 'X方向速度',},
              {value: 'Option24',label: 'Y方向速度',},
              {value: 'Option25',label: 'Z方向速度',},
              // {value: 'Option26',label: 'P1',},
              // {value: 'Option27',label: 'P2',},
              // {value: 'Option28',label: 'P3',},
              // {value: 'Option29',label: 'P4',},
              // {value: 'Option30',label: 'P5',},
              // {value: 'Option31',label: 'P6',},
              // {value: 'Option32',label: 'P7',},
              // {value: 'Option33',label: 'P8',},
              // {value: 'Option34',label: 'P9',},
              // {value: 'Option35',label: 'P10',},
              // {value: 'Option36',label: 'P11',},
              // {value: 'Option37',label: 'P12',},
              // {value: 'Option38',label: 'P13',},
              // {value: 'Option39',label: 'P14',},
              // {value: 'Option40',label: 'P15',},
              // {value: 'Option41',label: 'P16',},
              // {value: 'Option42',label: 'P17',},
              ]),
              options3:[
                { value: 'fault1', label: 'TEAMS-RT' },
                { value: 'fault2', label: 'PTEAMS-RT' },
                { value: 'fault3', label: 'Hier14 端到端' },
              ],
              value3:'fault1',
              options4:[{ value: 'assess1', label: '图卷积神经网络' }],
              value4:'assess1',
              options5:[{ value: 'decide1', label: '生成对抗网络' }],
              value5:'decide1',
               options6:[{ value: 'prediction1', label: '多模型融合' }],
               value6:'prediction1',
              options7:[{ value: 'machine1', label: '梯度提升树' }],
               value7:'machine1',
               options8:[{ value: 'learning1', label: '双Q学习' }],
               value8:'learning1',
            option2:"",
            value:ref(''),
            value2:ref(''),
            showalgorithm:false,
            showanomaly:false,
            showdiagresult:false,
            showdiagtroubleshoot:false,
            showdiagietm:false,
            showmodel:false,
            showkonwledge:false,
            showright:false,
            show_editfmeca:false,
            paratime:[],
            paravalue:[],
            anomaly_power:[0,0,0,0,0,0,0],
            anomaly_control:[0,0,0,0,0],
            unknown:[],
            good:[1,2,3,4,5,6,7,8,9,10,11,12,13],
            bad:[],
            fuzzy:[],
            suspect:[],
            U_faults:[],
            G_faults:[],
            B_faults:[],
            S_faults:[],
            predLabel:'',
            fuzzyProbs:{},
            hier14WindowSeries:[],
            hier14EchartsInstance:null,
            hier14DialogEchartsInstance:null,
            system_index:80,
            confidence:60,
            troubleshoot_table:[],
            troubleshoot_table2:[],
            fmeca_table:[],

            D_power:[
              [1,0,0,0,0,0,1],
              [1,1,0,0,0,0,1],
              [0,0,1,0,0,0,1],
              [0,0,1,1,0,0,1],
              [0,0,0,0,1,0,1],
              [0,0,0,0,0,1,1],
              [0,0,0,0,0,0,1],
            ],

            D_control:[
              [1,0,0,0,1],
              [0,0,1,0,1],
              [0,1,0,0,1],
              [0,0,1,1,1],
              [0,0,0,0,1],
              [0,0,0,0,1],
            ],
            fault_all:[
              "泵气蚀",
              "涡轮转速下降",
              "管路堵塞",
              "主阀门卡滞",
              "燃气泄漏",
              "燃烧不稳定",
              "喷管堵塞",
              "TVC偏角不足",
              "RCS推力不足",
              "栅格舵偏角不足",
              "控制器无信号",
              "陀螺仪恒偏差",
              "陀螺仪卡死",
            ],
            fault_name:'无故障',
            HI_norm:[],
            HI_min:[],
            life_list:[],
            selectedHI:[],
            power_comindex:[],
            control_comindex:[],



            P1:false,
            P2:false,
            P3:false,
            P4:false,
            P5:false,
            P6:false,
            P7:false,
            P8:false,
            P9:false,
            P10:false,
            P11:false,
            P12:false,
            P13:false,
            P14:false,
            P15:false,
            P16:false,
            P17:false,

            delname:'',
            maxUserId:0,
            adduser0:'',
            adduser1:'',
            adduser2:'',
            adduser3:'',
            edituser0:'',
            edituser1:'',
            edituser2:'',
            edituser3:'',

            adduser3table:[
              {value: '管理员', label: '管理员',} ,
              {value: '普通用户', label: '普通用户'}
            ],
            value10:'',
            value11:'',
            

           

        };
    },
    mounted(){
       this.Current_user();
       this.init_user();
        this.updateDateTime();
        setInterval(this.updateDateTime, 1000);
        setTimeout(() => {
      this.echarts_1();
  }, 100); 
  setTimeout(() => {
      this.initChart();
  }, 100); 
  setTimeout(() => {
      this.init_role();
  }, 1000); 
//     setTimeout(() => {
//       this.echarts_3();
//   }, 1000); 
// setTimeout(() => {
//       this.echarts_4();
//   }, 100); 
  this.init_fmeca();

    },
    methods:{
     async Current_user(){
        console.log("返回数据+++++:", this.currentUser);
         try {
          const res = await axios.get(`http://localhost:8000/algorithm/currentuser/`, {

          });
          console.log("返回数据:", res.data.username);
          this.currentUser = res.data.username;
          console.log("返回数据+++++:", this.currentUser);
        } catch (error) {
          console.error("返回数据失败:", error);
        }
      },
     async init_user(){
      try {
          const res = await axios.get(`http://localhost:8000/algorithm/inituser/`, {

          });
          console.log("返回数据:", res.data.data);
          this.user_table = res.data.data;
          // this.init_role();
        } catch (error) {
          console.error("返回数据失败:", error);
        }
      },
     async init_role(){
      console.log('bbbbbbbbbbb',this.currentUser)
      try {
          const res = await axios.post(`http://localhost:8000/algorithm/currentrole/`, {
            username:this.currentUser
          });
          console.log("返回数据aaaaaaaaaaaaaaa:", res.data.role);
          this.currentRole = res.data.role;
          
        } catch (error) {
          console.error("返回数据失败:", error);
        }
      },
 async  confirmDialog_adduser(){

     try {
    const res = await axios.post("http://localhost:8000/algorithm/adduser/", {
      // id:this.adduser0,
      username: this.adduser1,
      email: this.adduser2,
      password: this.adduser3,
      role: this.value10,  // 关键:这里把选中的角色传给后端
    });

    if (res.data.status === "success") {
      this.$message.success("✅ 用户添加成功!");
      this.init_user(); // 刷新用户列表
         this.adduser1='';
            this.adduser2='';
            this.adduser3='';
    } else {
      this.$message.error("❌ 添加失败:" + res.data.msg);
    }
  } catch (error) {
    console.error(error);
    this.$message.error("网络错误或后端异常");
  }

        this.init_user();
this.showadduser= false;
      },
     
    async   add_user(){

    this.showadduser= true;
  await this.getMaxUserId();
      this.adduser0 = this.maxUserId + 1;
 
      },
      cancelDialog_adduser(){
        // console.log('关闭窗口');
        this.adduser1='';
            this.adduser2='';
            this.adduser3='';
this.showadduser= false;
      },
      cancelDialog_edituser(){
      this.showedituser = false;
      },
  async    edituser(row){
        this.edituser1 = row.name;
        this.edituser2 = row.email;
        this.edituser3 = row.password;
        this.value11 = row.role;
        this.showedituser = true;

        try {
    const res = await axios.post("http://localhost:8000/algorithm/searchid/", {
      username: this.edituser1
    });

    if (res.data.status === "success") {
      this.edituser0 = res.data.userid; // 保存到 data 里备用
      console.log("✅ 用户ID为:", this.edituser0);
    } else {
      this.$message.error("未找到该用户");
    }
  } catch (error) {
    console.error(error);
    this.$message.error("查询用户ID失败");
  }
      },
   async   confirmDialog_edituser(){

          try {
    const res = await axios.post("http://localhost:8000/algorithm/edituser/", {
      id: this.edituser0,       // 用户ID
      username: this.edituser1, // 用户名
      email: this.edituser2,    // 邮箱
      password: this.edituser3, // 密码
      role: this.value11        // 角色
    });

    if (res.data.status === "success") {
      this.$message.success("✅ 用户信息修改成功");
      this.init_user();         // 重新加载用户列表
      this.showedituser = false;
    } else {
      this.$message.error("❌ 修改失败:" + res.data.msg);
    }
  } catch (error) {
    console.error(error);
    this.$message.error("请求失败,请检查服务器");
  }


        // this.init_user();
        // this.showedituser = false;

      },
 async     confirmDialog_deluser(){

        try {
    const res = await axios.post("http://localhost:8000/algorithm/deleteuser/", {
      username: this.delname
    });

    if (res.data.success) {
      //this.edituser0 = res.data.userid; // 保存到 data 里备用
      console.log("✅ 用户删除成功");
    } else {
      this.$message.error("未找到该用户");
    }
  } catch (error) {
    console.error(error);
    this.$message.error("查询用户ID失败");
  }


        this.init_user();
        console.log('删除用户')
        this.delname = '';
        this.showdeluser = false;
      },
      deleteuser(row){
        this.delname = '';
        this.delname = row.name;
        console.log(this.delname);
        this.showdeluser = true;
      },
      cancelDialog_deluser(){
        this.showdeluser = false;
      },
        returntohome(){
             this.$router.push('/')
        },
        updateDateTime() {
      const now = new Date();

      // 格式化日期 (YYYY-MM-DD)
      const year = now.getFullYear();
      const month = now.getMonth() + 1 < 10 ? '0' + (now.getMonth() + 1) : String(now.getMonth() + 1);
      const day = now.getDate() < 10 ? '0' + now.getDate() : String(now.getDate());
      this.currentDate = `${year}-${month}-${day}`;

      // 格式化时间 (HH:mm:ss)
      const hours = now.getHours() < 10 ? '0' + now.getHours() : String(now.getHours());
      const minutes = now.getMinutes() < 10 ? '0' + now.getMinutes() : String(now.getMinutes());
      const seconds = now.getSeconds() < 10 ? '0' + now.getSeconds() : String(now.getSeconds());
      this.currentTime = `${hours}:${minutes}:${seconds}`;
    },
    // 显示对话框
    showLogoutDialog() {
      this.logoutDialogVisible = true;
    },
    // 取消注销操作
    cancelLogout() {
      console.log('quxiao')
      console.log(this.logoutDialogVisible)
      this.logoutDialogVisible = false; // 关闭对话框
      console.log(this.logoutDialogVisible)
    },
    // 确认注销操作
    confirmLogout() {
      this.logoutDialogVisible = false; // 关闭对话框
      window.sessionStorage.clear();
      this.$router.push('/'); // 跳转到 /login 路由
    },
    cancelDialog_anomaly(){
      this.showanomaly = false;

    },
    Anomaly(){
      this.showanomaly = true;
    },
     echarts_1() {
       if (!this.selectedHI || this.selectedHI.length === 0) {
        console.warn('selectedHI 为空,暂不绘图');
        return;
    }

 		var myChart = echarts.init(document.getElementById('echart1'));

    
    // 生成 X 轴索引
    const xData = this.selectedHI[0].map((_, idx) => idx); // [0,1,2,...]
 		this.option = {
 			tooltip: {

 				trigger: 'axis',
 				axisPointer: {
 					lineStyle: {
 						color: '#57617B'
 					}
 				},
 				formatter: '{b}日	:<br/> 生产情况{c}'
 			},

 			grid: {
 				left: '0',
 				right: '20',
 				top: '10',
 				bottom: '0',
 				containLabel: true
 			},
 			xAxis: [{
    type: 'category',
    boundaryGap: false,
    axisLine: {
        show: false,
        lineStyle: {
            color: 'rgba(255,255,255,.6)'
        }
    },
    axisLabel: {
        color: 'rgba(255,255,255,.6)'  // ✅ 直接写在这里
    },
    data: xData 
}],
yAxis: [{
    axisLabel: {
        show: true,
        color: 'rgba(255,255,255,.6)'   // ✅ 不要再写 textStyle
    },
    axisLine: {
        show: false,
    },
    splitLine: {
        lineStyle: {
            type: 'dotted',
            color: 'rgba(255,255,255,.1)'
        }
    }
}],
 			series: [{
    name: '生产情况',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 5,
    showSymbol: false,
    lineStyle: {
        width: 2
    },
    areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
            offset: 0,
            color: 'rgba(98, 201, 141, 0.5)'
        }, {
            offset: 1,
            color: 'rgba(98, 201, 141, 0.1)'
        }], false),
        shadowColor: 'rgba(0, 0, 0, 0.1)',
        shadowBlur: 10
    },
    itemStyle: {
        color: '#4cb9cf',
        borderColor: 'rgba(98, 201, 141,0.27)',
        borderWidth: 12
    },
    data: this.selectedHI[0]
}]
 		};

 		// 使用刚指定的配置项和数据显示图表。
 		myChart.setOption(this.option);

 	},
  initChart() {
      this.echartsInstance = echarts.init(document.getElementById("echart2"));
      const option = {
        title: { text: '航天器参数监测' ,textStyle: {color: 'white' } },
        tooltip: {},
        legend: {
          textStyle: {
      color: 'red'  // 设置字体颜色为红色
    },
        },
        xAxis: {
          type: 'category',
          boundaryGap: false,
          data: this.paratime,
          axisLine: { lineStyle: { color: '#aaa' } },
          axisLabel: { color: '#fff' }
        },
        yAxis: {
          type: 'value',
          axisLabel: { formatter: '{value}', color: '#fff' },
          axisLine: { lineStyle: { color: '#aaa' } }, // Y轴线的颜色
          splitLine: { show: true, lineStyle: { type: 'dashed', color: '#666' } }, // 显示网格线并配置样式
        },
        series: [
           {
        type: 'line',
        smooth: true,
        showSymbol: false,  // ✅ 不显示任何数据点
        symbol: 'none',     // ✅ 不渲染点图标
        data: this.paravalue,
        lineStyle: { color: '#00eaff' },
        color: 'white',  // 设置线段颜色为红色
        areaStyle: {  color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(0, 234, 255, 0.5)' }, // 上部较亮
        { offset: 1, color: 'rgba(0, 234, 255, 0.05)' } // 下部逐渐透明
      ])
    }
      }
        ],
      };

      this.echartsInstance.setOption(option);
    },
     cancelDialog_algorithm(){
        this.showalgorithm = false;

      },
      Algorithm(){
        this.showalgorithm = true;

      },
    async confirmDialog_algorithm(){
      const data = [this.value3, this.value4, this.value5, this.value6,this.value7,this.value8];

      try {
          const res = await axios.post(`http://localhost:8000/algorithm/configuration/`, {
             data: data
          });
          console.log("算法配置成功", res.data);
        } catch (error) {
          console.error("算法配置失败:", error);
        }

      this.showalgorithm = false;

     },
     fault_dialog(){
      this.showdiagresult = true;
     },
     onDiagResultOpened() {
      if (this.hier14WindowSeries.length) {
        this.$nextTick(() => {
          this.renderHier14Chart('echart_hier14_dialog', true);
        });
      }
     },
     cancelDialog_diagresult(){
      this.showdiagresult = false;
     },
     confirmDialog_diagresult(){
      this.showdiagresult = false;
     },
     cancelDialog_troubleshoot(){

      this.showdiagtroubleshoot = false;

     },
     confirmDialog_troubleshoot(){
      this.showdiagtroubleshoot = false;
     },
     show_troubleshoot(){
      this.showdiagtroubleshoot = true;
     },
     show_ietm(){

      this.showdiagietm = true;

     },
     cancelDialog_ietm(){
this.showdiagietm = false;
     },
     confirmDialog_ietm(){
this.showdiagietm = false;
     },
     export_report(){
      if (this.progress.value !== 100) {
      this.$message.warning("算法未执行完毕");
      return;
      }
      //word

      let tableData1 = [this.powersys.data[0],this.controlsys.data[0]];

       const subsystemNames = ['动力系统', '飞控系统'];
       const header = ['子系统名称', '子系统分数'];
       const component_header = ['部件名称','故障名称','健康指数','剩余寿命'];
       const component_Names = ['液氧泵','液氧涡轮','煤油管路','煤油阀门','燃气发生器','燃烧室','喷管','TVC','RCS','栅格舵','传感器','液氧管路','液氧阀门','煤油泵','煤油涡轮'];
       const component_HI = this.HI_min;
       const component_life = this.life_list;
       const component_fault = this.fault_all;
       component_fault.push('管路堵塞');
       component_fault.push('主阀门卡滞');
       component_fault.push('泵气蚀');
       component_fault.push('涡轮转速下降');

       console.log(component_HI)
       console.log(component_life)

       const result2 = [component_header];

       component_Names.forEach((name, index) => {
    const row = [
        name, // 部件名称
        component_HI[index] === 0 ? component_fault[index] : '无故障', // 故障名称
        component_HI[index]?.toString() || '0', // 健康指数 - 转换为字符串
        component_life[index]?.toString() || '0' // 剩余寿命 - 转换为字符串
    ];
    result2.push(row);
});

        
       const result = [
  header,  // 首先添加表头
  ...tableData1.map((score, index) => [subsystemNames[index], `${score}`])  // 对原始数据进行映射,生成包含子系统名称和分数的新数组
];

  const doc = new Document({
    sections: [
      {
        properties: {},
        children: [
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({
              text: "航天器健康管理报告",
                font: "SimHei",  // 设置黑体字体
                size: 32,        // 设置三号字体,16pt = 32 half-points
                bold: true,      // 设置加粗(黑体通常是加粗的)
              }),
              
            ],
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun(`导出时间: ${new Date().toLocaleString()}`),
              // new TextRun(`操作用户: ${this.username}`),
              new TextRun(`评估对象:航天器`),
            ],
          }),
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun(`整器健康分数:${this.system_index}`),
              new TextRun(`再飞置信度:${this.confidence}`),
              new TextRun(`能否再飞:${this.finalresult}`),
            ],
          }),

          
          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
            new TextRun({
              text: "表1 子系统健康分数",
                font: "SimHei",  // 设置黑体字体
                size: 24,        // 设置三号字体,16pt = 32 half-points
                bold: true,      // 设置加粗(黑体通常是加粗的)
              }),
              
            ],
          }),

          new Table({
             alignment: AlignmentType.CENTER,
            rows: result.map(row => {
              return new TableRow({
                alignment: AlignmentType.CENTER,
                children: row.map(cell => {
                  return new TableCell({
                    children: [
                      new Paragraph({
                        alignment: AlignmentType.CENTER,
                        children: [new TextRun(cell)],
                        width: { size: 4535},
                        verticalAlign: 'center',  
                      }),
                    ],
                   
                  });
                }),
              });
            }),
          }),

          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
            new TextRun({
              text: "表2 部件健康分数",
                font: "SimHei",  // 设置黑体字体
                size: 24,        // 设置三号字体,16pt = 32 half-points
                bold: true,      // 设置加粗(黑体通常是加粗的)
              }),
              
            ],
          }),

          new Table({
             alignment: AlignmentType.CENTER,
            rows: result2.map(row => {
              return new TableRow({
                alignment: AlignmentType.CENTER,
                children: row.map(cell => {
                  return new TableCell({
                    children: [
                      new Paragraph({
                        alignment: AlignmentType.CENTER,
                        children: [new TextRun(cell)],
                        width: { size: 4535},
                        verticalAlign: 'center',  
                      }),
                    ],
                   
                  });
                }),
              });
            }),
          }),



          new Paragraph({
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun(`维修预案:参考维修手册(IETM)`),
            ],
          }),

        ],
      },
    ],
  });

  Packer.toBlob(doc).then((blob) => {
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'document.docx';
    link.click();
  });

     },
     handleSelectChange2(selectedValues) {
  // 确保是数组
  if(this.progress.value!==100){
    this.$message.warning("维修排故算法未执行完毕");
    return;
  }
  const values = Array.isArray(selectedValues) ? selectedValues : [selectedValues];

  const valueToIndex = this.options.reduce((map, item, idx) => {
    map[item.value] = idx;
    return map;
  }, {});

  const selectedHI = values.map(val => {
    const index = valueToIndex[val];
    return this.HI_norm[index];
  });

  //gzy
  this.remainlife = values.map(val => {
    const index = valueToIndex[val];
    return this.life_list[index];
  });
  this.component_index = values.map(val => {
    const index = valueToIndex[val];
    return this.HI_min[index];
  });
  this.component_index = Number(this.component_index[0].toFixed(2));
  this.remainlife = Number(this.remainlife[0].toFixed(2));


  console.log('选中的 HI_norm 列表:', selectedHI);
  this.selectedHI = selectedHI;
  this.echarts_1();
},
     async handleSelectChange(selectedValue){
      console.log(selectedValue);
      console.log(this.options2);
      var selectedItem = this.options2.find(item => item.value === selectedValue);
      const selectedLabel = selectedItem ? selectedItem.label : '';
      console.log('选中的 label:', selectedLabel);
      try {
          const res = await axios.get(`http://localhost:8000/algorithm/para_csv/`, {
            params: { value: selectedValue, label: selectedLabel }
          });
          console.log("CSV数据:", res.data);
          this.paratime = res.data.time;
          this.paravalue = res.data.value;
          // 这里你可以调用 echart 绘图
          this.initChart();
        } catch (error) {
          console.error("读取CSV失败:", error);
        }

     },

     operate_troubleshoot(){

        // 判断数组是否为空
  if (!this.troubleshoot_table2 || this.troubleshoot_table2.length === 0) {
    if (this.progress.value !== 100) {
      this.$message.warning("维修排故算法未执行完毕");
    } else {
      this.$message.warning("维修排故算法已执行完毕");
    }
    return;
  }
 const nextItem = this.troubleshoot_table2[0];
  // 取出第一个元素
   this.troubleshoot_table.push(nextItem);
  // 移除第一个元素
  this.troubleshoot_table2.splice(0, 1);

     },

    async start_evaluate(){
      this.progress.value = 0;
      this.troubleshoot_table = [];
      this.troubleshoot_table2 = [];

    if (this.value3 === 'fault3') {
      await this.hier14Diagnosis();
    } else {
      await this.anomaly_detection();
      await this.fault_diagnosis();
      await this.GradientBoosting();
    }

     this.progress.value = 40;

     await this.Component_eval();

     this.progress.value = 80;

     await this.Subsystem_eval();

     await this.System_eval();

     await this.troubleshoot();

     this.progress.value = 100;
     this.$message.success('算法执行完毕!');

     },
    async anomaly_detection(){
      try {
    const res = await axios.get('http://localhost:8000/algorithm/anomaly/')
    console.log("异常检测结果:", res.data)
    //anomalyResults.value = res.data
    this.anomaly_handle(res.data);
    
    } catch (error) {
    console.error("调用异常检测接口失败:", error)
    }

     },
     anomaly_handle(data_list){
      this.P1 = false;
      this.P2 = false;
      this.P3 = false;
      this.P4 = false;
      this.P5 = false;
      this.P6 = false;
      this.P7 = false;
      this.P8 = false;
      this.P9 = false;
      this.P10 = false;
      this.P11 = false;
      this.P12 = false;
      this.P13 = false;
      this.P14 = false;
      this.P15 = false;
      this.P16 = false;
      this.P17 = false;
      this.anomaly_power=[0,0,0,0,0,0,0];
      this.anomaly_control=[0,0,0,0,0];
      data_list.forEach(item => {
        if (item.parameter === 'P1' && item.status === 1) {
            console.log('P1 异常');
            this.P1 = true;
            this.P7 = true;
            this.anomaly_power[0] = 1;
            this.anomaly_power[6] = 1;
          } else if (item.parameter === 'P2' && item.status === 1) {
            console.log('P2 异常');
            this.P1 = true;
            this.P2 = true;
            this.P7 = true;
            this.anomaly_power[0] = 1;
            this.anomaly_power[1] = 1;
            this.anomaly_power[6] = 1;
          } else if (item.parameter === 'P3' && item.status === 1) {
            console.log('P3 异常');
            this.P3 = true;
            this.P7 = true;
            this.anomaly_power[2] = 1;
            this.anomaly_power[6] = 1;
          }else if (item.parameter === 'P4' && item.status === 1) {
            console.log('P4 异常');
            this.P3 = true;
            this.P4 = true;
            this.P7 = true;
            this.anomaly_power[2] = 1;
            this.anomaly_power[3] = 1;
            this.anomaly_power[6] = 1;
          }else if (item.parameter === 'P5' && item.status === 1) {
            console.log('P5 异常');
            this.P5 = true;
            this.P7 = true;
            this.anomaly_power[4] = 1;
            this.anomaly_power[6] = 1;
          }else if (item.parameter === 'P6' && item.status === 1) {
            console.log('P6 异常');
            this.P6 = true
            this.P7 = true
            this.anomaly_power[5] = 1;
            this.anomaly_power[6] = 1;
          }else if (item.parameter === 'P7' && item.status === 1) {
            console.log('P7 异常')
            this.P7 = true
            this.anomaly_power[6] = 1;
          }else if (item.parameter === 'P8' && item.status === 1) {
            console.log('P8 异常');
            this.P8 = true;
            this.P12 = true;
            this.anomaly_control[0] = 1;
            this.anomaly_control[4] = 1;
          }else if (item.parameter === 'P9' && item.status === 1) {
            console.log('P9 异常');
            this.P9 = true;
            this.P12 = true;
            this.anomaly_control[1] = 1;
            this.anomaly_control[4] = 1;
          }else if (item.parameter === 'P10' && item.status === 1) {
            console.log('P10 异常');
            this.P10 = true;
            this.P12 = true;
            this.anomaly_control[2] = 1;
            this.anomaly_control[4] = 1;
          }else if (item.parameter === 'P11' && item.status === 1) {
            console.log('P11 异常')
            this.P10 = true;
            this.P11 = true;
            this.P12 = true;
            this.anomaly_control[2] = 1;
            this.anomaly_control[3] = 1;
            this.anomaly_control[4] = 1;
          }else if (item.parameter === 'P12' && item.status === 1) {
            console.log('P12 异常')
            this.P12 = true
            this.anomaly_control[4] = 1;
          }else if (item.parameter === 'P13' && item.status === 1) {
            console.log('P13 异常')
            this.P12 = true
            this.anomaly_control[4] = 1;
          }else if (item.parameter === 'P14' && item.status === 1) {
            console.log('P14 异常')
            this.P14 = true
            this.P7 = true
          }else if (item.parameter === 'P14' && item.status === 1) {
            console.log('P14 异常')
            this.P14 = true
            this.P7 = true
          }else if (item.parameter === 'P15' && item.status === 1) {
            console.log('P15 异常')
            this.P15 = true
            this.P7 = true
          }else if (item.parameter === 'P16' && item.status === 1) {
            console.log('P16 异常')
            this.P16 = true
            this.P7 = true
          }else if (item.parameter === 'P17' && item.status === 1) {
            console.log('P17 异常')
            this.P17 = true
            this.P7 = true
          }
        })


     },
     async fault_diagnosis() {
  try {
    this.unknown = [];
    this.good = [];
    this.bad = [];
    this.suspect = [];

    // 🔸 Power 请求
    const resPower = await axios.get('http://localhost:8000/algorithm/diagnosis/', {
      params: {
        D: JSON.stringify(this.D_power),
        T: JSON.stringify(this.anomaly_power)
      }
    });

    console.log('Power 诊断结果:', resPower.data);
    this.unknown = resPower.data.Unknown || [];
    this.good = resPower.data.Good || [];
    this.bad = resPower.data.Bad || [];
    this.suspect = resPower.data.Suspected || [];

    // 🔸 Control 请求
    const resControl = await axios.get('http://localhost:8000/algorithm/diagnosis/', {
      params: {
        D: JSON.stringify(this.D_control),
        T: JSON.stringify(this.anomaly_control)
      }
    });

    console.log('Control 诊断结果:', resControl.data);

    const offset = 7;
    const unknown_c = (resControl.data.Unknown || []).map(x => x + offset);
    const good_c = (resControl.data.Good || []).map(x => x + offset);
    const bad_c = (resControl.data.Bad || []).map(x => x + offset);
    const suspect_c = (resControl.data.Suspected || []).map(x => x + offset);

    this.unknown = [...this.unknown, ...unknown_c];
    this.good = [...this.good, ...good_c];
    this.bad = [...this.bad, ...bad_c];
    this.suspect = [...this.suspect, ...suspect_c];

    // ✅ 打印结果
    console.log("good集合:", this.good);
    console.log("bad集合:", this.bad);
    console.log("suspect集合:", this.suspect);
    console.log("unknown集合:", this.unknown);

  } catch (error) {
    console.error('诊断请求错误:', error);
  }

  const mapIndexToName = (indexArray) => {
  return indexArray.map(i => {
    // 索引是从 1 开始的,所以要减 1
    const idx = i - 1;
    return this.fault_all[idx] || `未知故障(${i})`;
  });
};

// 映射到名称集合
this.U_faults = mapIndexToName(this.unknown);
this.G_faults = mapIndexToName(this.good);
this.B_faults = mapIndexToName(this.bad);
this.S_faults = mapIndexToName(this.suspect);

console.log("🔸 U集合(未知):", this.U_faults);
console.log("🟢 G集合(良好):", this.G_faults);
console.log("🔴 B集合(故障):", this.B_faults);
console.log("🟡 S集合(怀疑):", this.S_faults);
},

mapIndexToName(indexArray) {
      return indexArray.map(i => {
        if (i === 0) {
          return '无故障';
        }
        const idx = i - 1;
        return this.fault_all[idx] || `未知故障(${i})`;
      });
    },

async GradientBoosting(){

  this.fuzzy = [...this.bad, ...this.suspect].sort((a, b) => a - b);

   try {
        const response = await axios.post(
          'http://localhost:8000/algorithm/gradientboost/',
          { fuzzy: this.fuzzy },
          { headers: { 'Content-Type': 'application/json' } }
        );

        this.applyFaultRanking(response.data);
      } catch (error) {
        console.error('请求失败:', error);
      }
  
},

async hier14Diagnosis() {
  try {
    const response = await axios.get('http://localhost:8000/algorithm/hier14/');
    console.log('Hier14 诊断结果:', response.data);
    this.hier14WindowSeries = response.data.window_series || [];
    this.applyFaultRanking(response.data, { allClasses: true });
    this.fault_name = response.data.pred_name || '无故障';
    this.U_faults = [];
    this.G_faults = [];
    this.B_faults = [];
    this.S_faults = [];

    const pred = response.data.pred_label;
    if (pred === 0) {
      this.G_faults = ['正常'];
    } else if (pred >= 1 && pred <= this.fault_all.length) {
      this.B_faults = [response.data.pred_name];
    } else {
      this.B_faults = [response.data.pred_name || '未知故障'];
    }

    this.$nextTick(() => {
      this.renderHier14Chart('echart_hier14', false);
    });
  } catch (error) {
    console.error('Hier14 诊断请求失败:', error);
    this.hier14WindowSeries = [];
    this.$message.error('Hier14 诊断失败,请检查后端与 scope_data.csv');
  }
},

renderHier14Chart(domId = 'echart_hier14', isDialog = false) {
  if (!this.hier14WindowSeries.length) {
    return;
  }
  const chartDom = document.getElementById(domId);
  if (!chartDom) {
    return;
  }
  const instanceKey = isDialog ? 'hier14DialogEchartsInstance' : 'hier14EchartsInstance';
  if (this[instanceKey]) {
    this[instanceKey].dispose();
  }
  this[instanceKey] = echarts.init(chartDom);

  const times = this.hier14WindowSeries.map(item => Number(item.time_end.toFixed(1)));
  const pNormal = this.hier14WindowSeries.map(item => Number((item.p_normal * 100).toFixed(2)));

  const option = {
    title: {
      text: '滑窗诊断(窗口末时刻)',
      textStyle: { color: isDialog ? '#333' : '#fff', fontSize: 14 },
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const idx = params[0]?.dataIndex ?? 0;
        const win = this.hier14WindowSeries[idx];
        if (!win) return '';
        const top3 = (win.top3 || [])
          .map(item => `${item.name}: ${(item.prob * 100).toFixed(1)}%`)
          .join('<br/>');
        return [
          `窗口 #${win.window_index}`,
          `时间: ${win.time_start.toFixed(1)}s - ${win.time_end.toFixed(1)}s`,
          `预测: ${win.pred_name} (${(win.confidence * 100).toFixed(1)}%)`,
          `P(正常): ${(win.p_normal * 100).toFixed(1)}%`,
          top3 ? `Top3:<br/>${top3}` : '',
        ].join('<br/>');
      },
    },
    legend: {
      data: ['P(正常)', '故障点'],
      textStyle: { color: isDialog ? '#333' : '#fff' },
    },
    grid: { left: 50, right: 20, top: 50, bottom: 40 },
    xAxis: {
      type: 'category',
      name: '时间(s)',
      data: times,
      axisLabel: { color: isDialog ? '#333' : '#fff' },
      axisLine: { lineStyle: { color: '#aaa' } },
    },
    yAxis: {
      type: 'value',
      name: 'P(正常)%',
      min: 0,
      max: 100,
      axisLabel: { color: isDialog ? '#333' : '#fff' },
      axisLine: { lineStyle: { color: '#aaa' } },
      splitLine: { lineStyle: { color: isDialog ? '#ddd' : '#444' } },
    },
    series: [
      {
        name: 'P(正常)',
        type: 'line',
        smooth: true,
        showSymbol: false,
        data: pNormal,
        lineStyle: { color: '#4cb9cf' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(76, 185, 207, 0.45)' },
            { offset: 1, color: 'rgba(76, 185, 207, 0.05)' },
          ]),
        },
      },
      {
        name: '故障点',
        type: 'scatter',
        data: this.hier14WindowSeries
          .filter(item => item.pred_label !== 0)
          .map(item => [Number(item.time_end.toFixed(1)), Number((item.p_normal * 100).toFixed(2))]),
        symbolSize: 10,
        itemStyle: { color: '#ff6b6b' },
        label: {
          show: true,
          position: 'top',
          color: '#c0392b',
          fontSize: 10,
          formatter: (param) => {
            const win = this.hier14WindowSeries.find(
              item => Number(item.time_end.toFixed(1)) === param.value[0]
                && item.pred_label !== 0
            );
            return win ? win.pred_name : '';
          },
        },
      },
    ],
  };

  this[instanceKey].setOption(option);
},

applyFaultRanking(responseData, options = {}) {
  const allClasses = options.allClasses === true;
  this.fuzzyProbs = responseData.fuzzy_probs || {};
  this.predLabel = responseData.pred_label;

  let newData;
  if (allClasses && Array.isArray(responseData.class_probs)) {
    newData = responseData.class_probs
      .filter(item => item.class_id !== 0)
      .map(item => ({
        name: item.name,
        value: (item.prob * 100).toFixed(2),
      }));
    if (responseData.pred_label === 0) {
      newData = [{ name: '正常', value: (responseData.class_probs[0].prob * 100).toFixed(2) }];
    }
  } else {
    newData = Object.entries(this.fuzzyProbs).map(([idxStr, prob]) => {
      const idx = parseInt(idxStr, 10);
      const name = this.mapIndexToName([idx])[0];
      const value = (prob * 100).toFixed(2);
      return { name, value };
    });
  }

  this.faultlist.data = newData;
  if (this.faultlist.data.length === 0) {
    this.faultlist.data.push({ name: '无故障', value: 100 });
  }

  const maxName = this.faultlist.data.length
    ? this.faultlist.data.reduce((prev, current) => current.value > prev.value ? current : prev).name
    : null;

  console.log('✅ 故障名称:', maxName);
  this.fault_name = maxName;

  const faultToOptionLabelMap = {
    '泵气蚀': '液氧泵',
    '涡轮转速下降': '液氧涡轮',
    '管路堵塞': '煤油管路',
    '主阀门卡滞': '煤油阀门',
    '燃气泄漏': '燃气发生器',
    '燃烧不稳定': '燃烧室',
    '喷管堵塞': '喷管',
    'TVC偏角不足': 'TVC',
    'RCS推力不足': 'RCS',
    '栅格舵偏角不足': '栅格舵',
    '控制器无信号': '无',
    '陀螺仪恒偏差': '传感器',
    '陀螺仪卡死': '传感器',
    '正常': '无',
  };

  const mappedLabel = faultToOptionLabelMap[maxName];
  this.options.forEach(opt => {
    opt.disabled = false;
    if (mappedLabel && mappedLabel !== '无' && opt.label === mappedLabel) {
      opt.disabled = true;
      console.log(opt.label);
    }
  });

  console.log('✅ 故障概率列表:', this.faultlist.data);
},

async Component_eval(){

  try {
          const res = await axios.get(`http://localhost:8000/algorithm/component_eval/`, {
           
          });
          console.log("返回数据:", res.data);
          this.HI_norm = res.data.hi_norm_values;
          this.HI_min = res.data.hi_min_values;
          this.life_list = res.data.final_last_frame_results['RF'];
          this.options.forEach((opt, idx) => {
              if (opt.disabled === true) {
                this.HI_min[idx] = 0;
                this.life_list[idx] = 0;
              }
            });
          console.log('✅ 部件健康度:', this.HI_min);
          console.log('✅ 部件剩余寿命:', this.life_list);
          const originalArray = this.HI_min;

          const firstSeven = originalArray.slice(0, 7);
          const middleStart = 7;
          // 计算中间部分的结束索引(总长度减去后4个)
          const middleEnd = originalArray.length - 4;
          this.control_comindex = originalArray.slice(middleStart, middleEnd);
          if (this.fault_name === '控制器无信号') {
              // 是则往control_comindex列表末尾添加0
              this.control_comindex.push(0);
            } else {
              // 否则添加1
              this.control_comindex.push(1);
            }

          const lastFour = originalArray.slice(-4);

          this.power_comindex = [...firstSeven, ...lastFour];

          console.log("动力系统健康度列表:",this.power_comindex)
          console.log("飞控系统健康度列表:",this.control_comindex)
          // 这里你可以调用 echart 绘图
          //this.initChart();
        } catch (error) {
          console.error("返回数据失败:", error);
        }

},

async Subsystem_eval(){
   try {
        const response = await axios.post('http://localhost:8000/algorithm/subsystem_eval/', {
          power: this.power_comindex,
          control: this.control_comindex
        });

        console.log('✅ 后端返回:', response.data);
        // 这里可以根据返回结果提示用户
        this.powersys.data[0] = Math.round(response.data.power_HI * 100);
        this.controlsys.data[0] = Math.round(response.data.control_HI * 100);
        // 定义故障名称分组
        const powerFaults = ['泵气蚀', '涡轮转速下降', '管路堵塞', '主阀门卡滞', '燃气泄漏', '燃烧不稳定', '喷管堵塞'];
        const controlFaults = ['TVC偏角不足', 'RCS推力不足', '栅格舵偏角不足', '控制器无信号', '陀螺仪恒偏差', '陀螺仪卡死'];

        // 检查并设置相应系统数据
        if (powerFaults.includes(this.fault_name)) {
            this.powersys.data[0] = Math.round(0 * 100);
        }

        if (controlFaults.includes(this.fault_name)) {
            this.controlsys.data[0] = Math.round(0 * 100);
        }
            
      } catch (error) {
        console.error('❌ 请求出错:', error);
        this.$message.error('提交失败,请检查后端服务是否正常');
      }

},

async System_eval(){

    try {
        const response = await axios.post('http://localhost:8000/algorithm/system_eval/', {
          power: this.powersys.data[0],
          control: this.controlsys.data[0]
        });

        //gaozeyu

        this.system_index = Math.round(response.data.weighted_value).toFixed(0);
        this.confidence = response.data.prob*100;

        if(response.data.prediction==1){
          this.finalresult = '是';
        }else{
          this.finalresult = '否';
        }
        const powerFaults = ['泵气蚀', '涡轮转速下降', '管路堵塞', '主阀门卡滞', '燃气泄漏', '燃烧不稳定', '喷管堵塞'];
        const controlFaults = ['TVC偏角不足', 'RCS推力不足', '栅格舵偏角不足', '控制器无信号', '陀螺仪恒偏差', '陀螺仪卡死'];

        if (powerFaults.includes(this.fault_name)||controlFaults.includes(this.fault_name)) {
            this.confidence = 0.05*100;
            this.system_index = Math.round(10).toFixed(0);
            this.finalresult = '否';
        }

        console.log('✅ 后端返回:', response.data);
        
      } catch (error) {
        console.error('❌ 请求出错:', error);
        this.$message.error('提交失败,请检查后端服务是否正常');
      }


},

async troubleshoot(){

  console.log("调用双Q维修排故");
  // this.showdiagtroubleshoot = true;


   try {
          const res = await axios.post(`http://localhost:8000/algorithm/troubleshoot/`, {
           fault_name:this.fault_name
          });
          console.log("返回数据:", res.data.fault_plan);
          this.troubleshoot_table2 = res.data.fault_plan;

          // 这里你可以调用 echart 绘图
          //this.initChart();
        } catch (error) {
          console.error("返回数据失败:", error);
        }
 

},

confirmDialog_knowledge(){

  this.showkonwledge = false;

},

show_knowledge(){
  if(this.currentRole !== '管理员'){
   this.$message.error("该用户无此权限");
   return;
  }

  this.showkonwledge = true;

},

cancelDialog_knowledge(){
this.showkonwledge = false;
},

echarts_3(){
 var chartDom = document.getElementById('echart3');
            const myChart = echarts.init(chartDom);
            var option = {
              // title: {text: '多信号流图'},
              tooltip: {},
              animationDurationUpdate: 1500,
              animationEasingUpdate: 'quinticInOut',
              series: [
              {
                type: 'graph',
                layout: 'none',
                symbolSize: 35,
                roam: true,
                label: {
                  show: true
                },
                edgeSymbol: ['circle', 'arrow'],
                edgeSymbolSize: [4, 10],
                edgeLabel: {
                  fontSize: 20
                },
                data: [
                  {
                    name: 'C1',
                    x: -550,
                    y: 300,
                    symbol:'rect'
                  },
                  {
                    name: 'T5',
                    x: -500,
                    y: 300,
                    symbol:'circle'
                  },
                  {
                    name: 'C2',
                    x: -500,
                    y: 250,
                    symbol:'rect'
                  },
                  {
                    name: 'T1',
                    x: -450,
                    y: 300,
                    symbol:'circle'
                  },
                  {
                    name: 'C3',
                    x: -500,
                    y: 350,
                    symbol:'rect'
                  },
                  {
                    name: 'C4',
                    x: -450,
                    y: 250,
                    symbol:'rect'
                  },
                  {
                    name: 'C5',
                    x: -450,
                    y: 350,
                    symbol:'rect'
                  },
                  {
                    name: 'C6',
                    x: -400,
                    y: 250,
                    symbol:'rect'
                  },
                  {
                    name: 'T2',
                    x: -400,
                    y: 300,
                    symbol:'circle'
                  },
                  {
                    name: 'C7',
                    x: -400,
                    y: 350,
                    symbol:'rect'
                  },
                  {
                    name: 'C8',
                    x: -350,
                    y: 250,
                    symbol:'rect'
                  },
                  {
                    name: 'C9',
                    x: -350,
                    y: 350,
                    symbol:'rect'
                  },
                  {
                    name: 'T3',
                    x: -300,
                    y: 300,
                    symbol:'circle'
                  },
                  {
                    name: 'T4',
                    x: -300,
                    y: 400,
                    symbol:'circle'
                  },
                  {
                    name: 'C10',
                    x: -400,
                    y: 400,
                    symbol:'rect'
                  },
                  {
                    name: 'T6',
                    x: -450,
                    y: 400,
                    symbol:'circle'
                  },
                  {
                    name: 'C11',
                    x: -400,
                    y: 450,
                    symbol:'rect'
                  },
                  {
                    name: 'T7',
                    x: -450,
                    y: 450,
                    symbol:'circle'
                  },
                  


                ],
                links: [
                  {
                    source: 'Node 2',
                    target: 'Node 1',
                    label: {
                      show: true
                    },
                    lineStyle: {
                      curveness: 0.2
                    }
                  },
                  {
                    source: 'C1',
                    target: 'C2'
                  },
                  {
                    source: 'C1',
                    target: 'T5'
                  },
                  {
                    source: 'C1',
                    target: 'C3'
                  },
                  {
                    source: 'C2',
                    target: 'C4'
                  },
                  {
                    source: 'C2',
                    target: 'T1'
                  },
                  {
                    source: 'C3',
                    target: 'C5'
                  },
                  {
                    source: 'C4',
                    target: 'C6'
                  },
                  {
                    source: 'C4',
                    target: 'T2'
                  },
                  {
                    source: 'C5',
                    target: 'C7'
                  },
                  {
                    source: 'C6',
                    target: 'C8'
                  },
                  {
                    source: 'C7',
                    target: 'C9'
                  },
                  {
                    source: 'C8',
                    target: 'C10',
                    lineStyle: {
                      curveness: 1
                    }
                  },
                  {
                    source: 'C9',
                    target: 'C10',
                    lineStyle: {
                      curveness: 1
                    }
                  },
                  {
                    source: 'C9',
                    target: 'T3'
                  },
                  {
                    source: 'C9',
                    target: 'T4'
                  },
                  {
                    source: 'C10',
                    target: 'C11'
                  },
                  {
                    source: 'C10',
                    target: 'T6'
                  },
                  {
                    source: 'C11',
                    target: 'T7'
                  },

                ],
                lineStyle: {
                        opacity: 0.9,
                        width: 2,
                        curveness: 0
                      }
                    }
                  ]
                
                
            };      
            option && myChart.setOption(option);

},
echarts_4(){

   var chartDom = document.getElementById('echart4');
            const myChart = echarts.init(chartDom);
            var option = {
              // title: {text: '多信号流图'},
              tooltip: {},
              animationDurationUpdate: 1500,
              animationEasingUpdate: 'quinticInOut',
              series: [
              {
                type: 'graph',
                layout: 'none',
                symbolSize: 35,
                roam: true,
                label: {
                  show: true
                },
                edgeSymbol: ['circle', 'arrow'],
                edgeSymbolSize: [4, 10],
                edgeLabel: {
                  fontSize: 20
                },
                data: [
                  {
                    name: 'C12',
                    x: -550,
                    y: 300,
                    symbol:'rect'
                  },
                  {
                    name: 'C13',
                    x: -525,
                    y: 300,
                    symbol:'rect'
                  },
                  {
                    name: 'T8',
                    x: -550,
                    y: 275,
                    symbol:'circle'
                  },
                  {
                    name: 'T9',
                    x: -525,
                    y: 275,
                    symbol:'circle'
                  },
                  {
                    name: 'C14',
                    x: -500,
                    y: 300,
                    symbol:'rect'
                  },
                  {
                    name: 'T10',
                    x: -495,
                    y: 285,
                    symbol:'circle'
                  },
                  {
                    name: 'C15',
                    x: -500,
                    y: 275,
                    symbol:'rect'
                  },
                  {
                    name: 'T11',
                    x: -475,
                    y: 275,
                    symbol:'circle'
                  },
                  {
                    name: 'C16',
                    x: -500,
                    y: 325,
                    symbol:'rect'
                  },
                  {
                    name: 'T12',
                    x: -475,
                    y: 325,
                    symbol:'circle'
                  },
                  {
                    name: 'C17',
                    x: -475,
                    y: 300,
                    symbol:'rect'
                  },
                  
                  


                ],
                links: [
                  {
                    source: 'Node 2',
                    target: 'Node 1',
                    label: {
                      show: true
                    },
                    lineStyle: {
                      curveness: 0.2
                    }
                  },
                  {
                    source: 'C12',
                    target: 'C13'
                  },
                  {
                    source: 'C13',
                    target: 'C15'
                  },
                  {
                    source: 'C13',
                    target: 'C14'
                  },
                  {
                    source: 'C13',
                    target: 'C16'
                  },
                  {
                    source: 'C15',
                    target: 'C17'
                  },
                  {
                    source: 'C14',
                    target: 'C17'
                  },
                  {
                    source: 'C16',
                    target: 'C17'
                  },
                  {
                    source: 'C12',
                    target: 'T8'
                  },
                  {
                    source: 'C13',
                    target: 'T9'
                  },
                   {
                    source: 'C14',
                    target: 'T10'
                  },
                   {
                    source: 'C15',
                    target: 'T11'
                  },
                   {
                    source: 'C16',
                    target: 'T12'
                  },

                  

                ],
                lineStyle: {
                        opacity: 0.9,
                        width: 2,
                        curveness: 0
                      }
                    }
                  ]
                
                
            };      
            option && myChart.setOption(option);

},
handleClick(tab) {
      if (tab.paneName === "second") {
        this.echarts_4();
      } else if (tab.paneName === "first") {
        this.echarts_3();
      }
    },
confirmDialog_model(){
this.showmodel = false;
},
show_model(){
  if(this.currentRole !== '管理员'){
   this.$message.error("该用户无此权限");
   return;
  }


  this.showmodel = true;

},
cancelDialog_model(){
this.showmodel = false;
},
confirmDialog_right(){
this.showright = false;
},
show_right(){
  if(this.currentRole !== '管理员'){
   this.$message.error("该用户无此权限");
   return;
  }
  this.showright = true;



},

cancelDialog_right(){
this.showright = false;
},

async confirmDialog_editfmeca(){

  try {
    const res = await axios.post('http://localhost:8000/algorithm/editfmeca/', {
      id: this.index_fmeca,               // 记录id
      component: this.input1,
      fault_name: this.input2,
      fault_prob: this.input3,
      fault_reason: this.input4,
      degree_harm: this.input5
    });

    this.$message.success(res.data.message);
    this.show_editfmeca = false;

    this.init_fmeca();

   
  } catch (error) {
    this.$message.error('修改失败: ' + (error.response?.data?.error || error.message));
  }
this.show_editfmeca = false;
},

 handleedit(row){
this.show_editfmeca = true;
  console.log('编辑行数据:', row);
  this.index_fmeca = row.id;
  this.input1 = row.component;
  this.input2 = row.fault_name;
  this.input3 = row.fault_prob;
  this.input4 = row.fault_reason;
  this.input5 = row.degree_harm;

},

cancelDialog_editfmeca(){
this.show_editfmeca = false;
},

async init_fmeca(){
console.log("初始化FMECA表格");
  try {
          const res = await axios.get(`http://localhost:8000/algorithm/fmeca/`, {

          });
          console.log("返回数据:", res.data.data);
          this.fmeca_table = res.data.data;

          // 这里你可以调用 echart 绘图
          //this.initChart();
        } catch (error) {
          console.error("返回数据失败:", error);
        }
 

},

async getMaxUserId() {
  try {
    const res = await axios.get("http://localhost:8000/algorithm/maxuserid/");
    if (res.data.success) {
      this.maxUserId = res.data.max_id;
      // this.$message.success(`当前最大用户ID为:${this.maxUserId}`);
    } else {
      this.$message.warning(res.data.message);
    }
  } catch (error) {
    this.$message.error("获取最大用户ID失败:" + error);
  }
}

    
    },
    components: {
    UserFilled, // 注册子组件
    ThreeModel,
  },

}

</script>


<style scoped>
.background{
     background: linear-gradient(25deg, #0f2249,#182e5a 20%,#0f2249 40%,#182e5a 60%,#0f2249 80%,#182e5a 100%);
     color:#fff;
    height: 100%; /* ⚡让背景铺满整个屏幕 */
    width: 100%;
}
.module-box {
  display:flex; 
  justify-content: start;
  margin:5px;
}
.module-box2{
     display:flex; 
  justify-content: start;
  margin:5px;
}
.d-flex {
  display: flex;
}
.dv-decoration-111{
color: white;
font-weight: bold;
font-size: 1.5rem;
}
.ate{
  color: white;
  font-size: 2rem;
  font-weight: bold;
  font-style: italic; 
  margin-left: 20px;
}
.date {
  color: white;
  font-size: 1rem;

}

.time {
  color: white;
  font-size: 1rem;
  margin-right: 20px;

}
.username{
  color: white;
  font-size: 1.5rem;
}
.content{
    font-size: 28px;
    text-shadow: 0 0 3px #7acaec;
  }
.boxall{ border: 1px solid #3486da; background: rgba(0,70,190,.1); padding:15px; position: relative; margin-bottom: 10px; z-index: 10;}
.boxall:before,
.boxall:after{ position:absolute; width: 15px; height: 15px; content: "";  border-top: 3px solid #3486da; top: -2px;}
.boxall:before,.boxfoot:before{border-left: 3px solid #3486da;left:-2px;}
.boxall:after,.boxfoot:after{border-right: 3px solid #3486da; right: -2px;}
.boxfoot{ position:absolute; bottom: 0; width: 100%; left:0;}
.boxfoot:before,
.boxfoot:after{ position:absolute; width: 15px; height: 15px;  content: "";border-bottom:3px solid #3486da; bottom:-2px;}
.tit01{background: linear-gradient(to right,rgba(48,82,174,1),rgba(48,82,174,0)); color: #fff; font-size: 17px; padding: 0.3px 1px;}

.containerselect{
  display: flex; /* 启用 flex 布局 */
  flex-direction: row; /* 横向排列 */
  justify-content: start; /* 从左到右排列 */
  align-items: center;
  gap: 20px; /* 子元素之间的间距 */
  padding: 10px; /* 可选,为容器添加内边距 */
  width: 600px;
}
.button-container {
  display: flex;
  flex-wrap: wrap; /* 允许按钮换行 */
  justify-content: flex-start; /* 按钮从容器的左侧开始排列 */
  gap: 10px; /* 控制按钮之间的间距 */
  align-items: flex-start; /* 确保按钮在竖直方向上对齐 */
  margin: 0; /* 重置外边距 */
  width: 100%; /* 使容器填满宽度 */
  padding-left: 0px; /* 调整左内边距 */
}

/* 全黑色边框样式 */
.black-border-table .el-table__header-wrapper th,
.black-border-table .el-table__body-wrapper td,
.black-border-table .el-table__row,
.black-border-table .el-table,
.black-border-table .el-table__header,
.black-border-table .el-table__body {
  border-color: black !important;
}

/* 让表格外边框也是黑色 */
.black-border-table .el-table--border,
.black-border-table .el-table__inner-wrapper {
  border: 1px solid black !important;
}

/* 控制内部网格线为黑色 */
.black-border-table .el-table td,
.black-border-table .el-table th.is-leaf {
  border-bottom: 10px solid black !important;
  border-right: 10px solid black !important;
}

.demo-tabs > .el-tabs__content {
  padding: 32px;
  color: #6b778c;
  font-size: 32px;
  font-weight: 600;
}
</style>
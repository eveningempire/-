<template>
  <div class="visual-page">
    <section class="topbar">
      <div>
        <span class="eyebrow">3D VISUALIZATION</span>
        <h2>三维可视化监控</h2>
        <p>面向仿真单元的空间结构展示、运行状态监控与关键部件联动分析。</p>
      </div>
      <div class="top-actions">
        <el-tag :type="currentUnit.stateType" effect="dark">{{ currentUnit.state }}</el-tag>
        <el-button :icon="RefreshRight" @click="resetCamera">重置视角</el-button>
        <el-button :icon="Aim" type="primary" @click="focusSelected" :disabled="!selectedPart">定位部件</el-button>
      </div>
    </section>

    <section class="status-strip">
      <div v-for="item in currentStatusCards" :key="item.label" class="status-card">
        <small>{{ item.label }}</small>
        <strong>{{ item.value }}</strong>
        <span>{{ item.detail }}</span>
      </div>
    </section>

    <section class="unit-switcher">
      <button
        v-for="unit in simulationUnits"
        :key="unit.key"
        :class="{ active: selectedUnitKey === unit.key }"
        @click="selectUnit(unit.key)"
      >
        <span>{{ unit.name }}</span>
        <strong>{{ unit.summary }}</strong>
        <small>{{ unit.state }} · {{ unit.health }}</small>
      </button>
    </section>

    <section class="workspace">
      <div class="viewer-panel">
        <div class="viewer-toolbar">
          <div class="viewer-title">
            <b>{{ currentUnit.name }}</b>
            <span>{{ renderModeLabel }} · {{ selectedPart ? selectedPart.name : '未选择部件' }}</span>
          </div>
          <el-button-group>
            <el-tooltip content="旋转/暂停" placement="top">
              <el-button :icon="Refresh" :type="autoRotate ? 'primary' : 'default'" @click="toggleAutoRotate" />
            </el-tooltip>
            <el-tooltip content="线框显示" placement="top">
              <el-button :icon="Grid" :type="wireframeMode ? 'primary' : 'default'" @click="toggleWireframe" />
            </el-tooltip>
            <el-tooltip content="清除高亮" placement="top">
              <el-button :icon="Close" @click="clearHighlight" />
            </el-tooltip>
          </el-button-group>
        </div>

        <div ref="threeContainer" class="three-container">
          <div v-if="loadingModel" class="loading-mask">
            <div class="spinner"></div>
            <span>模型加载中...</span>
          </div>
          <div v-if="modelError" class="error-mask">
            <b>模型加载失败</b>
            <span>{{ modelError }}</span>
          </div>
        </div>
      </div>

      <aside class="side-panel">
        <el-tabs v-model="activeTab" stretch>
          <el-tab-pane label="运行状态" name="status">
            <div class="section">
              <h3>仿真单元</h3>
              <dl class="kv">
                <div><dt>程序名称</dt><dd>{{ currentUnit.name }}</dd></div>
                <div><dt>运行状态</dt><dd><el-tag :type="currentUnit.stateType">{{ currentUnit.state }}</el-tag></dd></div>
                <div><dt>模型来源</dt><dd>{{ currentUnit.source }}</dd></div>
                <div><dt>前端渲染</dt><dd>Vue3 + Three.js</dd></div>
              </dl>
            </div>

            <div class="section">
              <h3>实时反馈</h3>
              <div class="telemetry-list">
                <div v-for="item in currentTelemetry" :key="item.key">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <el-progress :percentage="item.percent" :status="item.status" :stroke-width="8" />
                </div>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="模型链路" name="pipeline">
            <div class="section">
              <h3>轻量化流程</h3>
              <div class="pipeline">
                <div v-for="step in pipeline" :key="step.title" class="pipeline-step">
                  <span>{{ step.index }}</span>
                  <div>
                    <b>{{ step.title }}</b>
                    <small>{{ step.desc }}</small>
                  </div>
                </div>
              </div>
            </div>

            <div class="format-grid">
              <div v-for="item in formats" :key="item.name">
                <b>{{ item.name }}</b>
                <span>{{ item.desc }}</span>
              </div>
            </div>
          </el-tab-pane>

          <el-tab-pane label="部件信息" name="part">
            <div v-if="selectedPart" class="selected-card">
              <span class="part-badge">已选中</span>
              <h3>{{ selectedPart.name }}</h3>
              <dl class="kv">
                <div><dt>模型节点</dt><dd>{{ selectedPart.id }}</dd></div>
                <div><dt>健康状态</dt><dd><el-tag :type="selectedPart.healthType">{{ selectedPart.health }}</el-tag></dd></div>
                <div><dt>告警等级</dt><dd>{{ selectedPart.alarm }}</dd></div>
                <div><dt>数据联动</dt><dd>{{ selectedPart.signal }}</dd></div>
              </dl>
            </div>
            <el-empty v-else description="点击三维模型中的部件查看详情" />

            <div class="section">
              <h3>可选部件</h3>
              <div class="part-list">
                <button
                  v-for="part in currentParts"
                  :key="part.mesh"
                  :class="{ active: selectedPart?.id === part.mesh }"
                  @click="selectPartFromList(part)"
                >
                  <span>{{ part.name }}</span>
                  <small>{{ part.metric }}</small>
                </button>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </aside>
    </section>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Aim, Close, Grid, Refresh, RefreshRight } from '@element-plus/icons-vue'
import * as THREE from 'three'
import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader.js'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const threeContainer = ref(null)
const selectedPart = ref(null)
const activeTab = ref('status')
const loadingModel = ref(true)
const modelError = ref('')
const wireframeMode = ref(false)
const autoRotate = ref(true)

const selectedUnitKey = ref('vehicle')

const cmgParts = [
  { name: '低速框架作动电机', mesh: 'Fillet5', metric: '温升 42.1°C', health: '正常', healthType: 'success', alarm: '无', signal: 'Motor-L 温度/电流反馈' },
  { name: '低速框架转动装置', mesh: 'Boss-Extrude1', metric: '负载 63%', health: '正常', healthType: 'success', alarm: '无', signal: 'Gimbal-L 角速度反馈' },
  { name: '低速框架', mesh: 'Cut-Extrude2', metric: '姿态误差 0.18°', health: '关注', healthType: 'warning', alarm: '轻微偏差', signal: 'Frame-L 姿态反馈' },
  { name: '高速转子轴系', mesh: 'T-Motor F80Pro.step<1>[2]', metric: '转速 8200 rpm', health: '正常', healthType: 'success', alarm: '无', signal: 'Rotor-H 转速反馈' },
  { name: '高速转子电机', mesh: 'T-Motor F80Pro.step<1>[3]', metric: '电流 2.8 A', health: '正常', healthType: 'success', alarm: '无', signal: 'Motor-H 电流反馈' },
]

const simulationUnits = [
  {
    key: 'vehicle',
    name: '可回收运载器总体状态',
    summary: '整器健康总览',
    state: 'RUNNING',
    stateType: 'success',
    health: '健康 92%',
    source: '总体构型示意 / Three.js 程序化模型',
    modelType: 'rocket',
    statusCards: [
      { label: '飞行阶段', value: '再入返回', detail: '姿态稳定，准备着陆' },
      { label: '总体健康', value: '92%', detail: '动力/结构/控制综合评估' },
      { label: '可复用裕度', value: '87%', detail: '热防护与结构寿命联合判据' },
      { label: '告警状态', value: '1 项', detail: '热防护局部温升关注' },
    ],
    telemetry: [
      { key: 'altitude', label: '高度', value: '18.6 km', percent: 64, status: 'success' },
      { key: 'velocity', label: '速度', value: 'Mach 1.8', percent: 58, status: 'success' },
      { key: 'attitude', label: '姿态稳定裕度', value: '91%', percent: 91, status: 'success' },
      { key: 'thermal', label: '热防护裕度', value: '76%', percent: 76, status: 'warning' },
    ],
    parts: [
      { name: '箭体结构', mesh: 'vehicle-body', metric: '载荷 61%', health: '正常', healthType: 'success', alarm: '无', signal: '结构载荷 / 振动反馈' },
      { name: '栅格舵/气动控制', mesh: 'grid-fins', metric: '舵偏 4.2°', health: '正常', healthType: 'success', alarm: '无', signal: '舵面角度 / 气动载荷反馈' },
      { name: '主发动机组', mesh: 'main-engines', metric: '推力 68%', health: '正常', healthType: 'success', alarm: '无', signal: '推力室压力 / 涡泵转速' },
      { name: '着陆支腿', mesh: 'landing-legs', metric: '锁定就绪', health: '正常', healthType: 'success', alarm: '无', signal: '支腿锁定 / 缓冲状态' },
      { name: '热防护区域', mesh: 'thermal-shield', metric: '温升关注', health: '关注', healthType: 'warning', alarm: '局部温升', signal: 'TPS 温度阵列反馈' },
    ],
  },
  {
    key: 'cmg',
    name: 'CMG 姿控执行机构三维仿真单元',
    summary: '姿态控制单机',
    state: 'RUNNING',
    stateType: 'success',
    health: '健康 94%',
    source: 'CATIA CATProduct / CATPart',
    modelType: 'obj',
    statusCards: [
      { label: '模型文件', value: 'OBJ / MTL', detail: '由 STP/CGR 链路转换' },
      { label: '渲染状态', value: 'WebGL', detail: '浏览器原生交互' },
      { label: '数据反馈', value: '5 路', detail: '温度/电流/姿态/转速' },
      { label: '轻量化策略', value: '混合格式', detail: '结构保真 + 外形压缩' },
    ],
    telemetry: [
      { key: 'temperature', label: '关键部件温度', value: '42.1°C', percent: 42, status: 'success' },
      { key: 'load', label: '低速框架负载', value: '63%', percent: 63, status: 'success' },
      { key: 'speed', label: '高速转子转速', value: '8200 rpm', percent: 72, status: 'success' },
      { key: 'attitude', label: '姿态误差裕度', value: '82%', percent: 82, status: 'warning' },
    ],
    parts: cmgParts,
  },
  {
    key: 'propulsion',
    name: '动力与推进仿真单元',
    summary: '发动机与管路',
    state: 'MONITORING',
    stateType: 'warning',
    health: '健康 89%',
    source: 'STP 主结构 + CGR 外形轻量化',
    modelType: 'propulsion',
    statusCards: [
      { label: '发动机状态', value: '3/3', detail: '主发动机均在线' },
      { label: '推力一致性', value: '96%', detail: '发动机推力偏差可控' },
      { label: '管路压力', value: '稳定', detail: '无快速跌落趋势' },
      { label: '告警状态', value: '1 项', detail: '涡泵振动轻微升高' },
    ],
    telemetry: [
      { key: 'thrust', label: '总推力水平', value: '68%', percent: 68, status: 'success' },
      { key: 'pressure', label: '推进剂管路压力', value: '7.4 MPa', percent: 74, status: 'success' },
      { key: 'vibration', label: '涡泵振动裕度', value: '71%', percent: 71, status: 'warning' },
      { key: 'temp', label: '喷管温度裕度', value: '79%', percent: 79, status: 'success' },
    ],
    parts: [
      { name: '主发动机 1', mesh: 'engine-1', metric: '推力 67%', health: '正常', healthType: 'success', alarm: '无', signal: '推力室压力' },
      { name: '主发动机 2', mesh: 'engine-2', metric: '推力 69%', health: '正常', healthType: 'success', alarm: '无', signal: '喷管温度' },
      { name: '主发动机 3', mesh: 'engine-3', metric: '振动关注', health: '关注', healthType: 'warning', alarm: '涡泵振动', signal: '涡泵振动谱' },
      { name: '推进剂输送管路', mesh: 'feed-lines', metric: '压力 7.4 MPa', health: '正常', healthType: 'success', alarm: '无', signal: '管路压力' },
    ],
  },
  {
    key: 'thermal',
    name: '结构与热防护仿真单元',
    summary: '结构/TPS',
    state: 'MONITORING',
    stateType: 'warning',
    health: '健康 86%',
    source: 'CGR 外形轻量化 + 区域传感器映射',
    modelType: 'thermal',
    statusCards: [
      { label: '结构载荷', value: '61%', detail: '低于限制载荷' },
      { label: 'TPS 裕度', value: '76%', detail: '再入热流关注' },
      { label: '疲劳寿命', value: '88%', detail: '可复用周期评估' },
      { label: '异常区域', value: '1 个', detail: '尾段热防护局部关注' },
    ],
    telemetry: [
      { key: 'load', label: '箭体结构载荷', value: '61%', percent: 61, status: 'success' },
      { key: 'thermal', label: '热防护温度裕度', value: '76%', percent: 76, status: 'warning' },
      { key: 'fatigue', label: '结构疲劳寿命', value: '88%', percent: 88, status: 'success' },
      { key: 'vibration', label: '回收段振动裕度', value: '83%', percent: 83, status: 'success' },
    ],
    parts: [
      { name: '前段承力结构', mesh: 'front-structure', metric: '载荷 52%', health: '正常', healthType: 'success', alarm: '无', signal: '应变片阵列' },
      { name: '中段贮箱结构', mesh: 'tank-section', metric: '载荷 61%', health: '正常', healthType: 'success', alarm: '无', signal: '压力/应变反馈' },
      { name: '尾段热防护', mesh: 'aft-thermal', metric: '温升关注', health: '关注', healthType: 'warning', alarm: '局部温升', signal: 'TPS 温度阵列' },
      { name: '着陆缓冲结构', mesh: 'landing-buffer', metric: '锁定就绪', health: '正常', healthType: 'success', alarm: '无', signal: '支腿锁定状态' },
    ],
  },
]

const currentUnit = computed(() => simulationUnits.find((item) => item.key === selectedUnitKey.value) || simulationUnits[0])
const currentParts = computed(() => currentUnit.value.parts)
const currentTelemetry = computed(() => currentUnit.value.telemetry)
const currentStatusCards = computed(() => currentUnit.value.statusCards)
const partByMesh = computed(() => Object.fromEntries(currentParts.value.map((item) => [item.mesh, item])))

const pipeline = [
  { index: '01', title: 'CATIA 建模', desc: '保留 CATProduct/CATPart 设计装配关系与参数化模型来源。' },
  { index: '02', title: 'STP 结构分解', desc: '对需要结构分解的单机模型使用 STP，降低跨平台信息损失。' },
  { index: '03', title: 'CGR 轻量化', desc: '其余外形部件采用 CGR 压缩，减少模型体量。' },
  { index: '04', title: 'Inventor 转换', desc: '将 STP/CGR 资源转为 Web 端可加载的 OBJ/MTL 或 FBX。' },
  { index: '05', title: 'Three.js 渲染', desc: '在 Vue 页面中完成模型加载、交互、选中高亮和数据联动。' },
]

const formats = [
  { name: 'STP', desc: '适合保留零部件装配和结构分解信息。' },
  { name: 'CGR', desc: '适合只保留外形信息的大规模轻量化显示。' },
  { name: 'OBJ/MTL', desc: '当前页面实际加载格式，便于 Web 端稳定预览。' },
  { name: 'FBX', desc: '预留格式，可通过 FBXLoader 接入动画和复杂层级。' },
]

const renderModeLabel = computed(() => (wireframeMode.value ? '线框模式' : '实体渲染'))
const assetBase = `${import.meta.env.BASE_URL}3dmodel/`

let scene
let camera
let renderer
let controls
let model
let animationId
let raycaster
let mouse
let selectedMesh
let resizeObserver

onMounted(async () => {
  await nextTick()
  initThree()
  loadCurrentUnitModel()
  animate()
})

onBeforeUnmount(() => {
  if (animationId) cancelAnimationFrame(animationId)
  if (resizeObserver) resizeObserver.disconnect()
  if (renderer?.domElement) renderer.domElement.removeEventListener('click', onMouseClick)
  controls?.dispose()
  disposeObject(model)
  renderer?.dispose()
})

function initThree() {
  const container = threeContainer.value
  const width = container.clientWidth
  const height = container.clientHeight

  scene = new THREE.Scene()
  scene.background = new THREE.Color(0xf7f9fc)

  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000)
  camera.position.set(6, 5, 7)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(width, height)
  renderer.outputColorSpace = THREE.SRGBColorSpace
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.12
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  container.appendChild(renderer.domElement)

  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.08
  controls.autoRotate = autoRotate.value
  controls.autoRotateSpeed = 0.8
  controls.minDistance = 2
  controls.maxDistance = 60

  raycaster = new THREE.Raycaster()
  mouse = new THREE.Vector2()

  addLights()
  addSceneHelpers()

  renderer.domElement.addEventListener('click', onMouseClick)
  resizeObserver = new ResizeObserver(onResize)
  resizeObserver.observe(container)
}

function addLights() {
  scene.add(new THREE.HemisphereLight(0xffffff, 0xd7e4f5, 1.3))

  const keyLight = new THREE.DirectionalLight(0xffffff, 1.6)
  keyLight.position.set(8, 10, 6)
  keyLight.castShadow = true
  keyLight.shadow.mapSize.width = 2048
  keyLight.shadow.mapSize.height = 2048
  scene.add(keyLight)

  const fillLight = new THREE.DirectionalLight(0x8fc7ff, 0.8)
  fillLight.position.set(-7, 5, -4)
  scene.add(fillLight)
}

function addSceneHelpers() {
  const grid = new THREE.GridHelper(18, 36, 0x6e8eaf, 0xd5dde8)
  grid.position.y = -0.02
  grid.material.transparent = true
  grid.material.opacity = 0.42
  scene.add(grid)

  const axes = new THREE.AxesHelper(2.8)
  axes.position.set(-6.8, 0.05, -6.8)
  scene.add(axes)

  const ring = new THREE.Mesh(
    new THREE.RingGeometry(2.1, 2.16, 96),
    new THREE.MeshBasicMaterial({ color: 0x55a8ff, transparent: true, opacity: 0.22, side: THREE.DoubleSide }),
  )
  ring.rotation.x = -Math.PI / 2
  ring.position.y = 0.03
  scene.add(ring)
}

function selectUnit(unitKey) {
  if (selectedUnitKey.value === unitKey) return
  selectedUnitKey.value = unitKey
  clearHighlight()
  loadCurrentUnitModel()
}

function loadCurrentUnitModel() {
  loadingModel.value = true
  modelError.value = ''
  removeCurrentModel()

  if (currentUnit.value.modelType === 'obj') {
    loadObjModel()
    return
  }

  model = createProceduralModel(currentUnit.value.modelType)
  prepareModel(model)
  scene.add(model)
  fitCameraToModel()
  loadingModel.value = false
}

function removeCurrentModel() {
  if (!model) return
  scene.remove(model)
  disposeObject(model)
  model = null
  selectedMesh = null
}

function loadObjModel() {
  loadingModel.value = true
  modelError.value = ''

  const mtlLoader = new MTLLoader()
  mtlLoader.setPath(assetBase)
  mtlLoader.load(
    '3D模型材料.mtl',
    (materials) => {
      materials.preload()
      const objLoader = new OBJLoader()
      objLoader.setMaterials(materials)
      objLoader.setPath(assetBase)
      objLoader.load(
        '3D模型网格.obj',
        (object) => {
          model = object
          prepareModel(model)
          scene.add(model)
          fitCameraToModel()
          loadingModel.value = false
        },
        undefined,
        (error) => {
          console.error('OBJ 模型加载失败:', error)
          modelError.value = 'OBJ 模型文件未能加载，请检查 /3dmodel/3D模型网格.obj。'
          loadingModel.value = false
        },
      )
    },
    undefined,
    (error) => {
      console.error('MTL 材质加载失败:', error)
      modelError.value = 'MTL 材质文件未能加载，请检查 /3dmodel/3D模型材料.mtl。'
      loadingModel.value = false
    },
  )
}

function createProceduralModel(type) {
  if (type === 'rocket') return createRocketModel()
  if (type === 'propulsion') return createPropulsionModel()
  if (type === 'thermal') return createThermalModel()
  return createRocketModel()
}

function createRocketModel() {
  const group = new THREE.Group()
  group.name = 'ReusableLaunchVehicle'

  const bodyMat = new THREE.MeshStandardMaterial({ color: 0xd9e2ec, metalness: 0.32, roughness: 0.42 })
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x223146, metalness: 0.45, roughness: 0.36 })
  const accentMat = new THREE.MeshStandardMaterial({ color: 0x2b78c6, metalness: 0.2, roughness: 0.5 })
  const heatMat = new THREE.MeshStandardMaterial({ color: 0xd46b3d, metalness: 0.18, roughness: 0.55 })
  const whiteMat = new THREE.MeshStandardMaterial({ color: 0xf4f7fb, metalness: 0.2, roughness: 0.32 })
  const glassMat = new THREE.MeshPhysicalMaterial({ color: 0x142a43, metalness: 0.2, roughness: 0.18, clearcoat: 0.8, clearcoatRoughness: 0.12 })
  const nozzleMat = new THREE.MeshStandardMaterial({ color: 0x8a9caf, metalness: 0.78, roughness: 0.28 })

  const body = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.86, 7.4, 48), bodyMat)
  body.name = 'vehicle-body'
  body.position.y = 1.2
  group.add(body)

  const nose = new THREE.Mesh(new THREE.ConeGeometry(0.72, 1.55, 48), bodyMat)
  nose.name = 'vehicle-body'
  nose.position.y = 5.68
  group.add(nose)

  const band1 = new THREE.Mesh(new THREE.CylinderGeometry(0.73, 0.73, 0.18, 48), accentMat)
  band1.name = 'vehicle-body'
  band1.position.y = 3.25
  group.add(band1)

  const interstage = new THREE.Mesh(new THREE.CylinderGeometry(0.78, 0.78, 0.42, 48), darkMat)
  interstage.name = 'vehicle-body'
  interstage.position.y = -1.98
  group.add(interstage)

  for (const y of [-2.38, 0.15, 3.08]) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.77, 0.045, 12, 48), whiteMat)
    ring.name = 'vehicle-body'
    ring.rotation.x = Math.PI / 2
    ring.position.y = y
    group.add(ring)
  }

  for (const y of [2.15, 2.52]) {
    const windowBand = new THREE.Mesh(new THREE.CylinderGeometry(0.735, 0.735, 0.18, 48), glassMat)
    windowBand.name = 'vehicle-body'
    windowBand.position.y = y
    group.add(windowBand)
  }

  const thermal = new THREE.Mesh(new THREE.CylinderGeometry(0.88, 0.92, 0.82, 48), heatMat)
  thermal.name = 'thermal-shield'
  thermal.position.y = -2.92
  group.add(thermal)

  for (let i = 0; i < 4; i += 1) {
    const angle = (Math.PI / 2) * i
    const fin = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.92, 0.62), darkMat)
    fin.name = 'grid-fins'
    fin.position.set(Math.cos(angle) * 0.84, 3.82, Math.sin(angle) * 0.84)
    fin.rotation.y = -angle
    group.add(fin)

    const leg = new THREE.Mesh(new THREE.BoxGeometry(0.11, 1.35, 0.16), darkMat)
    leg.name = 'landing-legs'
    leg.position.set(Math.cos(angle) * 1.18, -2.85, Math.sin(angle) * 1.18)
    leg.rotation.z = Math.cos(angle) * 0.28
    leg.rotation.x = -Math.sin(angle) * 0.28
    group.add(leg)
  }

  for (let i = 0; i < 3; i += 1) {
    const angle = (Math.PI * 2 * i) / 3
    const engine = new THREE.Mesh(new THREE.CylinderGeometry(0.19, 0.28, 0.55, 32), nozzleMat)
    engine.name = 'main-engines'
    engine.position.set(Math.cos(angle) * 0.38, -3.65, Math.sin(angle) * 0.38)
    group.add(engine)
    const throat = new THREE.Mesh(new THREE.ConeGeometry(0.18, 0.32, 32), darkMat)
    throat.name = 'main-engines'
    throat.position.set(Math.cos(angle) * 0.38, -3.94, Math.sin(angle) * 0.38)
    throat.rotation.x = Math.PI
    group.add(throat)
  }

  // 两个外挂推进剂舱，提升总体构型辨识度。
  for (const side of [-1, 1]) {
    const tank = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.28, 5.8, 32), whiteMat)
    tank.name = 'vehicle-body'
    tank.position.set(side * 0.98, 0.78, 0)
    group.add(tank)
    const tankNose = new THREE.Mesh(new THREE.ConeGeometry(0.22, 0.65, 32), whiteMat)
    tankNose.name = 'vehicle-body'
    tankNose.position.set(side * 0.98, 3.98, 0)
    group.add(tankNose)
  }

  const flame = new THREE.Mesh(
    new THREE.ConeGeometry(0.48, 1.25, 32),
    new THREE.MeshStandardMaterial({ color: 0xffa447, emissive: 0x662200, transparent: true, opacity: 0.58 }),
  )
  flame.name = 'main-engines'
  flame.position.y = -4.45
  flame.rotation.x = Math.PI
  group.add(flame)

  group.rotation.z = -0.18
  return group
}

function createPropulsionModel() {
  const group = new THREE.Group()
  const engineMat = new THREE.MeshStandardMaterial({ color: 0x394b61, metalness: 0.55, roughness: 0.34 })
  const pipeMat = new THREE.MeshStandardMaterial({ color: 0x2d88cf, metalness: 0.35, roughness: 0.4 })
  const warnMat = new THREE.MeshStandardMaterial({ color: 0xf39c35, emissive: 0x3b1c00, roughness: 0.48 })

  const line = new THREE.Mesh(new THREE.BoxGeometry(3.8, 0.12, 0.12), pipeMat)
  line.name = 'feed-lines'
  line.position.y = 0.9
  group.add(line)

  for (let i = 0; i < 3; i += 1) {
    const x = (i - 1) * 1.25
    const engine = new THREE.Mesh(new THREE.CylinderGeometry(0.33, 0.52, 1.25, 40), i === 2 ? warnMat : engineMat)
    engine.name = `engine-${i + 1}`
    engine.position.set(x, 0, 0)
    engine.rotation.x = Math.PI
    group.add(engine)

    const chamber = new THREE.Mesh(new THREE.SphereGeometry(0.38, 32, 16), engineMat)
    chamber.name = `engine-${i + 1}`
    chamber.position.set(x, 0.75, 0)
    group.add(chamber)
  }

  return group
}

function createThermalModel() {
  const group = new THREE.Group()
  const structureMat = new THREE.MeshStandardMaterial({ color: 0xdbe5ef, metalness: 0.25, roughness: 0.5 })
  const tankMat = new THREE.MeshStandardMaterial({ color: 0x9fb7cf, metalness: 0.18, roughness: 0.56 })
  const thermalMat = new THREE.MeshStandardMaterial({ color: 0xe0763d, emissive: 0x301000, roughness: 0.58 })
  const darkMat = new THREE.MeshStandardMaterial({ color: 0x2f4157, metalness: 0.35, roughness: 0.45 })

  const front = new THREE.Mesh(new THREE.CylinderGeometry(0.64, 0.7, 1.8, 40), structureMat)
  front.name = 'front-structure'
  front.position.y = 2.15
  group.add(front)

  const tank = new THREE.Mesh(new THREE.CylinderGeometry(0.82, 0.82, 2.4, 48), tankMat)
  tank.name = 'tank-section'
  tank.position.y = 0.1
  group.add(tank)

  const aft = new THREE.Mesh(new THREE.CylinderGeometry(0.86, 0.92, 1.1, 48), thermalMat)
  aft.name = 'aft-thermal'
  aft.position.y = -1.75
  group.add(aft)

  for (let i = 0; i < 4; i += 1) {
    const angle = (Math.PI / 2) * i
    const strut = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.1, 0.14), darkMat)
    strut.name = 'landing-buffer'
    strut.position.set(Math.cos(angle) * 1.08, -2.25, Math.sin(angle) * 1.08)
    strut.rotation.z = Math.cos(angle) * 0.22
    strut.rotation.x = -Math.sin(angle) * 0.22
    group.add(strut)
  }

  return group
}

function prepareModel(root) {
  root.traverse((child) => {
    if (!child.isMesh) return

    child.castShadow = true
    child.receiveShadow = true

    if (Array.isArray(child.material)) {
      child.material = child.material.map((material) => material.clone())
    } else if (child.material) {
      child.material = child.material.clone()
    }

    const material = Array.isArray(child.material) ? child.material[0] : child.material
    const matchedPart = partByMesh.value[child.name]
    const partMeta = matchedPart ? { ...matchedPart, id: matchedPart.mesh } : {
      name: child.name || '未命名部件',
      id: child.name,
      mesh: child.name,
      metric: '待绑定数据',
      health: '未评估',
      healthType: 'info',
      alarm: '未配置',
      signal: '待绑定',
    }

    child.userData.partMeta = partMeta
    child.userData.originalColor = material?.color?.clone()
    child.userData.originalEmissive = material?.emissive?.clone()
  })
}

function onMouseClick(event) {
  if (!model) return

  const rect = renderer.domElement.getBoundingClientRect()
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const intersects = raycaster.intersectObject(model, true)
  const hit = intersects.find((item) => item.object?.isMesh)
  if (!hit) return

  selectMesh(hit.object)
}

function selectPartFromList(part) {
  const mesh = findMeshByName(part.mesh)
  if (mesh) {
    selectMesh(mesh)
    focusMesh(mesh)
  } else {
    selectedPart.value = { ...part, id: part.mesh }
    ElMessage.warning('当前模型中未找到该部件节点')
  }
}

function selectMesh(mesh) {
  selectedMesh = mesh
  selectedPart.value = mesh.userData.partMeta
  activeTab.value = 'part'
  highlightPart(mesh)
}

function highlightPart(mesh) {
  restoreMaterials()

  const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material]
  materials.forEach((material) => {
    if (!material) return
    if (material.color) material.color.set(0xff8a34)
    if (material.emissive) material.emissive.set(0x332000)
    material.needsUpdate = true
  })
}

function restoreMaterials() {
  if (!model) return
  model.traverse((child) => {
    if (!child.isMesh) return
    const materials = Array.isArray(child.material) ? child.material : [child.material]
    materials.forEach((material) => {
      if (!material) return
      if (material.color && child.userData.originalColor) material.color.copy(child.userData.originalColor)
      if (material.emissive && child.userData.originalEmissive) material.emissive.copy(child.userData.originalEmissive)
      material.wireframe = wireframeMode.value
      material.needsUpdate = true
    })
  })
}

function findMeshByName(name) {
  let found = null
  model?.traverse((child) => {
    if (!found && child.isMesh && child.name === name) found = child
  })
  return found
}

function fitCameraToModel(target = model) {
  if (!target) return

  const box = new THREE.Box3().setFromObject(target)
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  const maxDim = Math.max(size.x, size.y, size.z) || 1
  const distance = maxDim * 1.28

  camera.position.set(center.x + distance * 0.95, center.y + distance * 0.58, center.z + distance * 0.95)
  camera.near = Math.max(maxDim / 100, 0.01)
  camera.far = maxDim * 100
  camera.updateProjectionMatrix()
  controls.target.copy(center)
  controls.update()
}

function focusMesh(mesh) {
  const box = new THREE.Box3().setFromObject(mesh)
  const center = box.getCenter(new THREE.Vector3())
  const size = box.getSize(new THREE.Vector3())
  const maxDim = Math.max(size.x, size.y, size.z) || 1
  const distance = Math.max(maxDim * 3.4, 2)

  controls.target.copy(center)
  camera.position.set(center.x + distance, center.y + distance * 0.7, center.z + distance)
  camera.lookAt(center)
  controls.update()
}

function focusSelected() {
  if (selectedMesh) focusMesh(selectedMesh)
}

function resetCamera() {
  fitCameraToModel()
}

function toggleWireframe() {
  wireframeMode.value = !wireframeMode.value
  if (!model) return
  model.traverse((child) => {
    if (!child.isMesh) return
    const materials = Array.isArray(child.material) ? child.material : [child.material]
    materials.forEach((material) => {
      if (material) {
        material.wireframe = wireframeMode.value
        material.needsUpdate = true
      }
    })
  })
}

function toggleAutoRotate() {
  autoRotate.value = !autoRotate.value
  if (controls) controls.autoRotate = autoRotate.value
}

function clearHighlight() {
  restoreMaterials()
  selectedPart.value = null
  selectedMesh = null
}

function onResize() {
  const container = threeContainer.value
  if (!container || !camera || !renderer) return

  const width = container.clientWidth
  const height = container.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

function animate() {
  animationId = requestAnimationFrame(animate)
  controls?.update()
  renderer?.render(scene, camera)
}

function disposeObject(object) {
  if (!object) return
  object.traverse((child) => {
    if (child.geometry) child.geometry.dispose()
    const materials = Array.isArray(child.material) ? child.material : [child.material]
    materials.forEach((material) => material?.dispose?.())
  })
}
</script>

<style scoped>
.visual-page {
  min-height: calc(100vh - 126px);
  display: flex;
  flex-direction: column;
  gap: 16px;
  color: #172335;
}

.topbar,
.status-card,
.viewer-panel,
.side-panel {
  background: #ffffff;
  border: 1px solid #dfe7f0;
  border-radius: 8px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 20px;
}

.eyebrow {
  display: block;
  margin-bottom: 6px;
  color: #2563a6;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
}

.topbar h2 {
  margin: 0;
  font-size: 22px;
  line-height: 1.25;
}

.topbar p {
  margin: 6px 0 0;
  color: #66788f;
  font-size: 13px;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.unit-switcher {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.unit-switcher button {
  min-height: 92px;
  padding: 14px 16px;
  border: 1px solid #dfe7f0;
  border-radius: 8px;
  background: #fff;
  color: #172335;
  text-align: left;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
}

.unit-switcher button:hover,
.unit-switcher button.active {
  border-color: #2563a6;
  background: #eef6ff;
}

.unit-switcher span {
  color: #5d7189;
  font-size: 12px;
}

.unit-switcher strong {
  font-size: 16px;
}

.unit-switcher small {
  color: #6a7b90;
  font-size: 12px;
}

.status-card {
  min-height: 86px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.status-card small,
.viewer-title span,
.pipeline-step small,
.format-grid span,
.part-list small {
  color: #6a7b90;
  font-size: 12px;
}

.status-card strong {
  margin: 5px 0 3px;
  font-size: 20px;
}

.workspace {
  flex: 1;
  min-height: 620px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: 16px;
}

.viewer-panel {
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.viewer-toolbar {
  height: 58px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 0 14px 0 18px;
  border-bottom: 1px solid #dfe7f0;
}

.viewer-title {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.viewer-title b,
.viewer-title span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.three-container {
  position: relative;
  flex: 1;
  min-height: 560px;
  overflow: hidden;
}

.three-container :deep(canvas) {
  display: block;
  width: 100%;
  height: 100%;
}

.loading-mask,
.error-mask {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(247, 249, 252, 0.86);
  color: #46566a;
}

.error-mask {
  color: #b42318;
  padding: 24px;
  text-align: center;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #cbd7e6;
  border-top-color: #2563a6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.side-panel {
  min-width: 0;
  padding: 12px;
  overflow: auto;
}

.section {
  padding: 10px 2px 16px;
  border-bottom: 1px solid #edf1f6;
}

.section:last-child {
  border-bottom: 0;
}

.section h3,
.selected-card h3 {
  margin: 0 0 12px;
  font-size: 15px;
}

.kv {
  margin: 0;
  display: grid;
  gap: 10px;
}

.kv div {
  display: grid;
  grid-template-columns: 92px minmax(0, 1fr);
  gap: 10px;
  align-items: center;
}

.kv dt {
  color: #6a7b90;
  font-size: 12px;
}

.kv dd {
  margin: 0;
  min-width: 0;
  color: #172335;
  font-size: 13px;
  word-break: break-word;
}

.telemetry-list {
  display: grid;
  gap: 14px;
}

.telemetry-list > div {
  display: grid;
  gap: 6px;
}

.telemetry-list span {
  color: #5f7085;
  font-size: 12px;
}

.telemetry-list strong {
  font-size: 18px;
}

.pipeline {
  display: grid;
  gap: 10px;
}

.pipeline-step {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 10px;
  align-items: start;
}

.pipeline-step > span {
  display: inline-flex;
  width: 32px;
  height: 32px;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #e8f1fb;
  color: #2563a6;
  font-size: 12px;
  font-weight: 700;
}

.pipeline-step div {
  display: grid;
  gap: 3px;
}

.format-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  padding-top: 12px;
}

.format-grid div {
  min-height: 94px;
  padding: 12px;
  border: 1px solid #dfe7f0;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.selected-card {
  position: relative;
  padding: 14px;
  border: 1px solid #d9e6f5;
  border-radius: 8px;
  background: #f7fbff;
}

.part-badge {
  display: inline-flex;
  margin-bottom: 8px;
  color: #2563a6;
  font-size: 12px;
  font-weight: 700;
}

.part-list {
  display: grid;
  gap: 8px;
}

.part-list button {
  min-height: 52px;
  padding: 9px 11px;
  border: 1px solid #dfe7f0;
  border-radius: 8px;
  background: #fff;
  color: #172335;
  text-align: left;
  cursor: pointer;
  display: grid;
  gap: 4px;
}

.part-list button:hover,
.part-list button.active {
  border-color: #2563a6;
  background: #eef6ff;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 1180px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .unit-switcher {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .side-panel {
    max-height: none;
  }
}

@media (max-width: 760px) {
  .topbar {
    align-items: stretch;
    flex-direction: column;
  }

  .top-actions {
    justify-content: flex-start;
  }

  .status-strip,
  .unit-switcher,
  .format-grid {
    grid-template-columns: 1fr;
  }

  .workspace {
    min-height: 0;
  }

  .three-container {
    min-height: 420px;
  }

  .viewer-toolbar {
    height: auto;
    align-items: stretch;
    flex-direction: column;
    padding: 12px;
  }
}
</style>

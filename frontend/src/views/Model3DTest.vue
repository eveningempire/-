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
    name: '甲烷可回收运载器总体状态',
    summary: '单芯级复用构型',
    state: 'RUNNING',
    stateType: 'success',
    health: '健康 92%',
    source: '朱雀三号 / 新一代甲烷复用火箭风格通用示意（非官方模型）',
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
      { name: '一二级箭体与贮箱', mesh: 'vehicle-body', metric: '载荷 61%', health: '正常', healthType: 'success', alarm: '无', signal: '结构载荷 / 贮箱压力 / 振动反馈' },
      { name: '级间段与分离机构', mesh: 'interstage', metric: '分离回路就绪', health: '正常', healthType: 'success', alarm: '无', signal: '分离回路 / 锁紧机构状态' },
      { name: '栅格舵/气动控制', mesh: 'grid-fins', metric: '舵偏 4.2°', health: '正常', healthType: 'success', alarm: '无', signal: '舵面角度 / 气动载荷反馈' },
      { name: '液氧甲烷发动机簇', mesh: 'main-engines', metric: '7/7 在线 · 推力68%', health: '正常', healthType: 'success', alarm: '无', signal: '推力室压力 / 涡泵转速 / 混合比' },
      { name: '展开式着陆机构', mesh: 'landing-legs', metric: '四腿展开锁定', health: '正常', healthType: 'success', alarm: '无', signal: '展开角 / 锁定 / 缓冲器行程' },
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
  group.name = 'MethaloxReusableLaunchVehicle'

  const steel = new THREE.MeshPhysicalMaterial({ color: 0xcbd3da, metalness: .78, roughness: .24, clearcoat: .45, clearcoatRoughness: .2 })
  const steelLight = new THREE.MeshStandardMaterial({ color: 0xe9eef2, metalness: .58, roughness: .3 })
  const dark = new THREE.MeshStandardMaterial({ color: 0x202a35, metalness: .72, roughness: .28 })
  const black = new THREE.MeshStandardMaterial({ color: 0x0c1218, metalness: .45, roughness: .45 })
  const accent = new THREE.MeshStandardMaterial({ color: 0x2368a2, metalness: .3, roughness: .42 })
  const heat = new THREE.MeshStandardMaterial({ color: 0x9c4b2f, metalness: .28, roughness: .56 })
  const nozzle = new THREE.MeshStandardMaterial({ color: 0x65717c, metalness: .9, roughness: .22 })

  // 单芯级大直径两级液氧甲烷构型，参考新一代可回收火箭比例。
  const firstStage = new THREE.Mesh(new THREE.CylinderGeometry(1.02, 1.08, 6.9, 64), steel)
  firstStage.name = 'vehicle-body'; firstStage.position.y = -.55; group.add(firstStage)
  const secondStage = new THREE.Mesh(new THREE.CylinderGeometry(.82, .98, 3.05, 64), steelLight)
  secondStage.name = 'vehicle-body'; secondStage.position.y = 4.42; group.add(secondStage)
  const shoulder = new THREE.Mesh(new THREE.CylinderGeometry(.82, 1.02, .72, 64), steelLight)
  shoulder.name = 'interstage'; shoulder.position.y = 2.54; group.add(shoulder)
  const interstage = new THREE.Mesh(new THREE.CylinderGeometry(1.025, 1.025, .62, 64), dark)
  interstage.name = 'interstage'; interstage.position.y = 2.12; group.add(interstage)
  const fairing = new THREE.Mesh(new THREE.ConeGeometry(.82, 2.35, 64), steelLight)
  fairing.name = 'vehicle-body'; fairing.position.y = 7.12; group.add(fairing)

  // 蒙皮焊缝、级间标识带和纵向管线整流罩。
  for (const y of [-3.55, -2.25, -.9, .45, 1.75, 3.16, 4.25, 5.55]) {
    const seam = new THREE.Mesh(new THREE.TorusGeometry(y > 2.7 ? .825 : 1.025, .025, 10, 64), y === 1.75 ? accent : dark)
    seam.name = y === 1.75 ? 'interstage' : 'vehicle-body'; seam.rotation.x = Math.PI / 2; seam.position.y = y; group.add(seam)
  }
  const raceway = new THREE.Mesh(new THREE.BoxGeometry(.12, 6.1, .12), dark)
  raceway.name = 'vehicle-body'; raceway.position.set(1.02, -.35, 0); group.add(raceway)
  const mark = new THREE.Mesh(new THREE.BoxGeometry(.018, 1.7, .44), accent)
  mark.name = 'vehicle-body'; mark.position.set(1.025, .7, 0); group.add(mark)

  // 四片可动栅格舵，采用格栅板而非简单实心方块。
  for (let i = 0; i < 4; i += 1) {
    const angle = i * Math.PI / 2
    const finGroup = new THREE.Group(); finGroup.name = 'grid-fins'
    const frame = new THREE.Mesh(new THREE.BoxGeometry(.12, 1.1, .82), dark); frame.name = 'grid-fins'; finGroup.add(frame)
    for (let n = -2; n <= 2; n += 1) {
      const bar = new THREE.Mesh(new THREE.BoxGeometry(.14, .055, .72), black); bar.name = 'grid-fins'; bar.position.y = n * .18; finGroup.add(bar)
    }
    finGroup.position.set(Math.cos(angle) * 1.12, 1.28, Math.sin(angle) * 1.12); finGroup.rotation.y = -angle; group.add(finGroup)

    // 展开式支腿：主支柱、斜撑和着陆脚垫。
    const legGroup = new THREE.Group(); legGroup.name = 'landing-legs'
    const strut = new THREE.Mesh(new THREE.BoxGeometry(.14, 2.65, .18), dark); strut.name = 'landing-legs'; strut.position.y = -.3; strut.rotation.z = .34; legGroup.add(strut)
    const brace = new THREE.Mesh(new THREE.BoxGeometry(.09, 1.75, .11), steelLight); brace.name = 'landing-legs'; brace.position.set(-.28, .15, 0); brace.rotation.z = -.38; legGroup.add(brace)
    const foot = new THREE.Mesh(new THREE.CylinderGeometry(.34, .42, .12, 28), black); foot.name = 'landing-legs'; foot.position.set(.44, -1.62, 0); legGroup.add(foot)
    legGroup.position.set(Math.cos(angle) * 1.15, -3.22, Math.sin(angle) * 1.15); legGroup.rotation.y = -angle; group.add(legGroup)
  }

  const engineDeck = new THREE.Mesh(new THREE.CylinderGeometry(1.08, 1.08, .48, 64), heat)
  engineDeck.name = 'thermal-shield'; engineDeck.position.y = -4.2; group.add(engineDeck)
  const enginePositions = [[0,0], [.54,0], [-.54,0], [.27,.47], [.27,-.47], [-.27,.47], [-.27,-.47]]
  for (const [x,z] of enginePositions) {
    const chamber = new THREE.Mesh(new THREE.CylinderGeometry(.16, .2, .36, 32), dark); chamber.name = 'main-engines'; chamber.position.set(x,-4.48,z); group.add(chamber)
    const bell = new THREE.Mesh(new THREE.CylinderGeometry(.17, .3, .62, 32, 1, true), nozzle); bell.name = 'main-engines'; bell.position.set(x,-4.86,z); group.add(bell)
  }
  const plume = new THREE.Mesh(new THREE.ConeGeometry(.56, 1.65, 40), new THREE.MeshStandardMaterial({ color:0x8fd8ff, emissive:0x246fb5, transparent:true, opacity:.46 }))
  plume.name = 'main-engines'; plume.position.y = -5.78; plume.rotation.x = Math.PI; group.add(plume)

  group.rotation.z = -0.105
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

<template>
  <div class="page">
    <!-- 顶部栏 -->
    <header class="topbar">
      <div class="title">
        <span class="title-glow"></span>
        在轨管理数字孪生系统
      </div>
      <div class="top-right">
        <div class="system-info">
          <div class="info-item">
            <i class="icon-clock"></i>
            <span>{{ nowText }}</span>
          </div>
          <div class="info-item">
            <i class="icon-weather"></i>
            <span>20~28℃ 晴转多云 优</span>
          </div>
        </div>
      </div>
    </header>

    <div class="layout">
      <!-- 左侧：卫星列表 -->
      <aside class="panel left-panel">
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <i class="icon-folder"></i>
              <span>卫星列表</span>
            </div>
            <div class="panel-actions">
              <span class="act-dot"></span><span class="act-dot"></span><span class="act-dot"></span>
            </div>
          </div>
          <div class="tree">
            <TreeGroup label="高轨卫星" :items="highOrbitSatellites" open />
            <TreeGroup label="低轨卫星" :items="leoSatellites" open />
            <TreeGroup label="环境卫星" :items="envSatellites" />
          </div>
        </div>

        <div class="panel panel-sub">
          <div class="panel-head small">
            <div class="panel-title"><span>智能体问答</span></div>
            <div class="panel-actions"><span class="act-dot"></span><span class="act-dot"></span></div>
          </div>
          <div class="bot">
            <div class="bot-avatar"></div>
            <div class="bot-lines">
              <div class="bot-line"></div>
              <div class="bot-line short"></div>
            </div>
          </div>
          <div class="video-player">
            <div class="video-controls">
              <button class="play-btn">▶</button>
              <div class="time-display">00:01</div>
              <div class="progress-bar">
                <div class="progress-fill"></div>
              </div>
              <div class="duration">00:29</div>
              <button class="volume-btn">🔊</button>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间 Three.js 场景 -->
      <main class="center">
        <div ref="threeRoot" class="three-root"></div>
        <div class="glow-arc"></div>
      </main>

      <!-- 右侧：参数趋势 & 健康评估 -->
      <aside class="panel right-panel">
        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <i class="icon-stats"></i><span>核心参数变化趋势</span>
            </div>
            <div class="panel-actions">
              <span class="act-dot"></span><span class="act-dot"></span><span class="act-dot"></span>
            </div>
          </div>

          <div class="kpi-bars">
            <div v-for="(k,i) in kpi" :key="k.name" class="kpi-row">
              <div class="kpi-name">{{ k.name }}</div>
              <div class="kpi-bar"><div class="kpi-bar-fill" :style="{ width: k.value+'px' }"></div></div>
              <div class="kpi-val">{{ k.value }}</div>
            </div>
          </div>

          <div class="chart" ref="lineRef"></div>
          <div class="legend">
            <span v-for="(l,i) in legend" :key="l" class="legend-item">
              <span class="legend-dot" :style="{ background: colors[i] }"></span>{{ l }}
            </span>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head">
            <div class="panel-title">
              <i class="icon-analysis"></i><span>关键单机健康指标</span><span class="ghost">Data Analysis</span>
            </div>
            <div class="panel-actions">
              <span class="act-dot"></span><span class="act-dot"></span><span class="act-dot"></span>
            </div>
          </div>

          <HealthCard name="推力器" desc="推力器爆燃情况:正常" status-text="正常" :percent="75" color="#45e18c" />
          <HealthCard name="SADA" desc="SADA燃情况:异常" status-text="异常" :percent="43" color="#ff5b5b" />
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
/** 依赖：
 *  npm i three echarts
 */
import * as echarts from 'echarts';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { onMounted, onBeforeUnmount, ref, computed } from 'vue';

/* ===== 顶部时间文本 ===== */
const nowText = computed(() => {
  const d = new Date();
  const pad = (n:number)=> String(n).padStart(2,'0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
});

/* ===== 左侧数据 ===== */
const highOrbitSatellites = [
  { name: '风云四号', active: true },
  { name: '北斗G1' },
  { name: '通信卫星三号' },
  { name: '高分卫星' },
];
const leoSatellites = [
  { name: '天宫空间站' }, 
  { name: '星链-124' }, 
  { name: '资源三号' }
];
const envSatellites = [{ name: '环境卫星' }];

/* ===== 右侧图表数据 ===== */
const kpi = [
  { name: 'AB1方差', value: 1900 },
  { name: 'AB2方差', value: 1800 },
  { name: 'AB3方差', value: 1700 },
  { name: 'AB4方差', value: 1600 },
];
const legend = ['AB1','AB2','AB3','AB4'];
const colors = ['#2bd4ff','#ffe44f','#a58bff','#ff70c2'];
const lineRef = ref<HTMLDivElement>();
onMounted(() => {
  if (lineRef.value) {
    const chart = echarts.init(lineRef.value);
    chart.setOption({
      grid: { left: 40, right: 10, top: 10, bottom: 25 },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: Array.from({length:24},(_,i)=>i+':00'),
        axisLine:{ lineStyle:{ color:'rgba(255,255,255,.15)'}},
        axisLabel:{ color:'rgba(255,255,255,.65)', fontSize:10 }, boundaryGap:false },
      yAxis: { type: 'value', axisLine:{show:false}, splitLine:{ lineStyle:{ color:'rgba(255,255,255,.08)'}},
        axisLabel:{ color:'rgba(255,255,255,.65)', fontSize:10 } },
      series: legend.map((name, idx) => ({
        type: 'line', name, data: mockWave(idx), smooth: true, symbol: 'none',
        lineStyle: { width: 2, color: colors[idx] },
        areaStyle: { color: colors[idx], opacity: .15 }
      }))
    });
    window.addEventListener('resize', () => chart.resize());
  }
});
function mockWave(seed=0){ const arr:number[]=[]; let base=0.5+seed*0.08; for(let i=0;i<24;i++){ base+=(Math.sin((i+seed)/3)+Math.random()*0.5)*0.05; arr.push(Math.max(0.1,+(base*10).toFixed(2))); } return arr; }

/* ===== Three.js 场景 ===== */
const threeRoot = ref<HTMLDivElement>();
let renderer: THREE.WebGLRenderer | null = null;
let scene: THREE.Scene, camera: THREE.PerspectiveCamera, controls: OrbitControls;
let raf = 0;

// 卫星与轨道的描述
type OrbitSpec = {
  color: string;
  a: number;       // 长半轴
  b: number;       // 短半轴
  tiltX: number;   // 绕 X 倾角（度）
  tiltZ: number;   // 绕 Z 倾角（度）
  speed: number;   // 角速度（弧度/秒）
  startPhase?: number; // 初始相位
};
type Flyer = { mesh: THREE.Object3D, orbit: OrbitSpec, t: number };

const flyers: Flyer[] = [];

onMounted(() => {
  initThree();
  animate();
  window.addEventListener('resize', onResize);
});

onBeforeUnmount(() => {
  cancelAnimationFrame(raf);
  window.removeEventListener('resize', onResize);
  if (renderer) { renderer.dispose(); renderer.forceContextLoss(); renderer.domElement.remove(); }
});

function initThree(){
  if (!threeRoot.value) return;

  // 1) Renderer
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(threeRoot.value.clientWidth, threeRoot.value.clientHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  threeRoot.value.appendChild(renderer.domElement);

  // 2) Scene & Camera
  scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2(0x02050a, 0.003);
  camera = new THREE.PerspectiveCamera(45, threeRoot.value.clientWidth / threeRoot.value.clientHeight, 0.1, 2000);
  camera.position.set(0, 140, 360);
  scene.add(camera);

  // 3) Controls
  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.minDistance = 160;
  controls.maxDistance = 700;

  // 4) 灯光
  const ambient = new THREE.AmbientLight(0x6699ff, 0.6);
  const sun = new THREE.DirectionalLight(0xffffff, 1.0);
  sun.position.set(200, 100, 150);
  scene.add(ambient, sun);

  // 5) 星空背景
  addStars(1200);

  // 6) 地球
  addEarth();

  // 7) 轨道与卫星
  const orbits: OrbitSpec[] = [
    { color:'#f7e23a', a:220, b:200, tiltX:60, tiltZ:15, speed: 0.35, startPhase: 0.0 },
    { color:'#b657ff', a:260, b:140, tiltX:65, tiltZ:-10, speed: 0.25, startPhase: 1.0 },
    { color:'#ff4b6e', a:300, b:240, tiltX:52, tiltZ:28, speed: 0.20, startPhase: 2.0 },
    { color:'#2bd4ff', a:180, b:320, tiltX:70, tiltZ:40, speed: 0.42, startPhase: 0.5 },
    { color:'#ff70c2', a:330, b:210, tiltX:58, tiltZ:-35, speed: 0.18, startPhase: -0.5 },
  ];
  orbits.forEach((o,i) => {
    const ring = createOrbit(o);
    scene.add(ring);

    // 卫星（彩色+小机翼）
    const sat = createSatellite(['#2bd4ff','#ffd52b','#67ff2b','#ff47a1','#6b5bff'][i%5]);
    scene.add(sat);
    flyers.push({ mesh: sat, orbit: o, t: o.startPhase ?? 0 });
  });
}

function addStars(count=800){
  const g = new THREE.BufferGeometry();
  const pos = new Float32Array(count*3);
  for(let i=0;i<count;i++){
    const r = 900 + Math.random()*500;
    const theta = Math.random()*Math.PI*2;
    const phi = Math.acos(2*Math.random()-1);
    pos[i*3] = r * Math.sin(phi) * Math.cos(theta);
    pos[i*3+1] = r * Math.cos(phi);
    pos[i*3+2] = r * Math.sin(phi) * Math.sin(theta);
  }
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const m = new THREE.PointsMaterial({ size: 1.2, color: 0xffffff, transparent:true, opacity:0.85 });
  const points = new THREE.Points(g, m);
  scene.add(points);
}

function addEarth(){
  const group = new THREE.Group();
  scene.add(group);

  const loader = new THREE.TextureLoader();
  // 公共纹理（可换成本地）： 
  // 地表贴图：https://threejs.org/examples/textures/land_ocean_ice_cloud_2048.jpg
  // 夜晚灯光：https://threejs.org/examples/textures/planets/earth_atmos_2048.jpg （这里不用）
  const diffuse = loader.load('https://threejs.org/examples/textures/land_ocean_ice_cloud_2048.jpg');
  diffuse.colorSpace = THREE.SRGBColorSpace;

  const globe = new THREE.Mesh(
    new THREE.SphereGeometry(100, 64, 64),
    new THREE.MeshPhongMaterial({ map: diffuse, shininess: 8 })
  );
  group.add(globe);

  // 气辉（轻微发光）
  const glow = new THREE.Mesh(
    new THREE.SphereGeometry(103, 64, 64),
    new THREE.MeshBasicMaterial({ color: 0x3ec8ff, transparent: true, opacity: .08, blending: THREE.AdditiveBlending })
  );
  group.add(glow);

  // 自转
  const spin = () => { globe.rotation.y += 0.0008; glow.rotation.y += 0.0006; requestAnimationFrame(spin); };
  spin();
}

function createOrbit(o: OrbitSpec){
  const N = 512;
  const pts: THREE.Vector3[] = [];
  for(let i=0;i<N;i++){
    const t = i / N * Math.PI * 2;
    const x = o.a * Math.cos(t);
    const z = o.b * Math.sin(t);
    pts.push(new THREE.Vector3(x, 0, z));
  }
  const geo = new THREE.BufferGeometry().setFromPoints(pts);
  geo.attributes.position.needsUpdate = true;

  const mat = new THREE.LineBasicMaterial({ color: new THREE.Color(o.color), transparent:true, opacity: 0.95 });
  const ring = new THREE.LineLoop(geo, mat);

  // 倾角
  ring.rotation.x = THREE.MathUtils.degToRad(o.tiltX);
  ring.rotation.z = THREE.MathUtils.degToRad(o.tiltZ);

  // 柔和发光
  const glow = new THREE.Mesh(
    new THREE.RingGeometry(Math.min(o.a,o.b)-1, Math.max(o.a,o.b)+1, 128),
    new THREE.MeshBasicMaterial({ color: o.color, transparent: true, opacity: .08, side: THREE.DoubleSide })
  );
  glow.rotation.x = ring.rotation.x;
  glow.rotation.z = ring.rotation.z;
  glow.position.y = 0.01;
  scene.add(glow);

  return ring;
}

function createSatellite(color: string){
  const body = new THREE.Mesh(
    new THREE.BoxGeometry(8, 4, 4),
    new THREE.MeshStandardMaterial({ color, metalness: 0.4, roughness: 0.3 })
  );
  const wingMat = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: new THREE.Color(color).multiplyScalar(0.4) });
  const wingL = new THREE.Mesh(new THREE.BoxGeometry(10, 0.6, 3), wingMat);
  const wingR = wingL.clone();
  wingL.position.x = -9; wingR.position.x = 9;
  const tip = new THREE.Mesh(new THREE.ConeGeometry(1.8, 3, 8), new THREE.MeshStandardMaterial({ color: 0xcccccc }));
  tip.rotation.z = Math.PI/2; tip.position.x = 5.5;

  const sat = new THREE.Group();
  sat.add(body, wingL, wingR, tip);
  sat.userData.spin = (Math.random()*0.8+0.6) * (Math.random() > 0.5 ? 1 : -1);
  return sat;
}

function updateFlyer(f: Flyer, dt: number){
  f.t += f.orbit.speed * dt;
  const t = f.t;

  // 基本椭圆（XY 平面）
  const x = f.orbit.a * Math.cos(t);
  const z = f.orbit.b * Math.sin(t);
  let pos = new THREE.Vector3(x, 0, z);

  // 倾角旋转矩阵
  const qx = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1,0,0), THREE.MathUtils.degToRad(f.orbit.tiltX));
  const qz = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0,0,1), THREE.MathUtils.degToRad(f.orbit.tiltZ));
  pos.applyQuaternion(qx).applyQuaternion(qz);

  f.mesh.position.copy(pos);
  f.mesh.lookAt(0,0,0);
  f.mesh.rotateY(Math.PI/2);
  f.mesh.rotateZ(Math.sin(t*2)*0.02);
}

let last = performance.now();
function animate(){
  raf = requestAnimationFrame(animate);
  const now = performance.now();
  const dt = (now - last)/1000;
  last = now;

  flyers.forEach(f => updateFlyer(f, dt));
  controls.update();
  renderer?.render(scene, camera);
}
function onResize(){
  if (!renderer || !threeRoot.value) return;
  const w = threeRoot.value.clientWidth, h = threeRoot.value.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
</script>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

export default { name: 'OrbitTwinDashboard' };

export const TreeGroup = defineComponent({
  name: 'TreeGroup',
  props: {
    label: { type: String, required: true },
    items: { type: Array as PropType<Array<{name: string; active?: boolean}>>, default: () => [] },
    open: { type: Boolean, default: true }
  },
  data(){ return { isOpen: this.open }; },
  methods:{ toggle(){ this.isOpen = !this.isOpen; } },
  template: `
  <div class="tree-group">
    <div class="tree-group-head" @click="toggle">
      <i class="caret" :class="{open: isOpen}"></i><span>{{ label }}</span>
    </div>
    <div v-show="isOpen" class="tree-items">
      <div v-for="it in items" :key="it.name" class="tree-item" :class="{ active: it.active }">
        <i class="file"></i><span class="name">{{ it.name }}</span>
      </div>
    </div>
  </div>`
});

export const HealthCard = defineComponent({
  name: 'HealthCard',
  props: {
    name: { type: String, required: true },
    desc: { type: String, required: true },
    statusText: { type: String, required: true },
    percent: { type: Number, required: true },
    color: { type: String, default: '#45e18c' }
  },
  computed: {
    barStyle(): any { return { width: this.percent + '%', background: this.color }; },
    badgeClass(): any { return { ok: this.statusText === '正常', bad: this.statusText !== '正常' }; }
  },
  template: `
  <div class="health">
    <div class="health-head">
      <div class="left">
        <div class="name">{{ name }}</div>
        <div class="desc">{{ desc }}</div>
      </div>
      <div class="status" :class="badgeClass">{{ statusText }}</div>
    </div>
    <div class="bar"><div class="bar-fill" :style="barStyle"></div></div>
    <div class="percent">{{ percent }}%</div>
  </div>`
});
</script>

<style scoped>
/* ======= 基础与背景 ======= */
:root{
  --panel: rgba(25, 45, 75, 0.9);
  --panel-border: rgba(72, 203, 255, 0.25);
  --panel-head: rgba(20, 55, 95, 0.9);
  --text: #ffffff;
  --muted: #ffffff;
  --weak: rgba(255,255,255,0.8);
  --accent: #30c7ff;
  --glow-blue: #48c7ff;
  --glow-cyan: #2bd4ff;
}
*{ box-sizing: border-box; }
.page{ height:100vh; display:flex; flex-direction:column; color:var(--text); background:#0a1a2e; overflow:hidden; }
.page::before{
  content:""; position:absolute; inset:0;
  background:
    radial-gradient(1200px 600px at 60% -200px, rgba(48,199,255,.15), transparent 60%),
    radial-gradient(800px 400px at 20% 100%, rgba(120,80,255,.12), transparent 60%),
    radial-gradient(100% 100% at 50% 50%, rgba(10,26,46,0.8), rgba(15,35,55,0.95)),
    linear-gradient(135deg, #0a1a2e 0%, #16213e 50%, #0f2337 100%);
  pointer-events:none;
}

/* 顶部栏 */
.topbar{
  height:60px; display:flex; align-items:center; justify-content:space-between;
  padding: 0 18px 0 22px; border-bottom: 1px solid rgba(48,199,255,.15);
  background: linear-gradient(180deg, rgba(15,35,55,.85), rgba(10,26,46,.6));
  position: relative; z-index: 2;
}
.title{ position:relative; font-weight:700; letter-spacing:1px; padding-left:18px; color:#ffffff; text-shadow:0 0 18px rgba(48,199,255,.35); }
.title-glow{ position:absolute; left:0; top:50%; transform:translateY(-50%); width:8px; height:20px; border-radius:2px;
  background: linear-gradient(180deg, #30c7ff, #6c8bff); box-shadow:0 0 12px #30c7ff; }
.top-right{ display:flex; align-items:center; gap:10px; color:#ffffff; }
.system-info{ display:flex; align-items:center; gap:20px; }
.info-item{ display:flex; align-items:center; gap:6px; }
.icon-clock, .icon-weather{ width:16px; height:16px; background:var(--glow-cyan); border-radius:50%; }
.icon-clock::after{ content:"🕐"; font-size:12px; }
.icon-weather::after{ content:"🌤️"; font-size:12px; }

/* 三列布局 */
.layout{ flex:1; display:grid; grid-template-columns: 320px 1fr 380px; gap:14px; padding:14px; }

/* 面板通用 */
.panel{ background: var(--panel); border: 1px solid var(--panel-border); border-radius: 10px; backdrop-filter: blur(6px); padding:10px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
.panel-head{ height:36px; display:flex; align-items:center; justify-content:space-between; padding: 0 6px 0 8px; background: var(--panel-head); border: 1px solid rgba(48,199,255,.25); border-radius:8px; margin-bottom:10px; }
.panel-head.small{ height:32px; }
.panel-title{ display:flex; align-items:center; gap:8px; font-weight:600; color:#ffffff; }
.panel-title .ghost{ margin-left:10px; color:rgba(255,255,255,0.6); font-size:12px; opacity:.8 }
.panel-actions{ display:flex; gap:6px; }
.act-dot{ width:6px; height:6px; background:rgba(48,199,255,.6); border-radius:2px; }

/* 左侧 */
.left-panel{ display:flex; flex-direction:column; gap:12px; }
.icon-folder, .icon-stats, .icon-analysis{
  width:14px; height:14px; display:inline-block; background: linear-gradient(180deg, #30c7ff, #6c8bff);
  -webkit-mask: radial-gradient(circle at 50% 30%,#000 60%, transparent 61%) no-repeat 0/100% 100%;
  mask: radial-gradient(circle at 50% 30%,#000 60%, transparent 61%) no-repeat 0/100% 100%;
  border-radius:2px;
}
.tree{ padding:6px; }
.tree-group{ margin-bottom:10px; }
.tree-group-head{ display:flex; align-items:center; gap:6px; color:#ffffff; padding:6px 6px; border-radius:6px; cursor:pointer; user-select:none; }
.caret{ width:0; height:0; border-left:6px solid #ffffff; border-top:4px solid transparent; border-bottom:4px solid transparent; transform:rotate(-90deg); transition:.2s; }
.caret.open{ transform:rotate(0deg); }
.tree-items{ margin-left:16px; padding-bottom:4px; }
.tree-item{ display:flex; align-items:center; gap:8px; padding:6px 8px; border-radius:6px; color:#ffffff; }
.tree-item.active, .tree-item:hover{ background: rgba(48,199,255,.2); color:#ffffff; }
.file{ width:12px; height:12px; border:1px solid rgba(48,199,255,.55); border-radius:2px; position:relative; }
.file::after{ content:""; position:absolute; right:0; top:-2px; width:6px; height:4px; background:rgba(48,199,255,.6); border-radius:1px; }

.bot{ display:flex; align-items:center; gap:10px; padding:10px; }
.bot-avatar{ width:56px; height:56px; border-radius:10px;
  background: radial-gradient(circle at 60% 35%, #fff 10%, #8dd2ff 30%, transparent 45%), linear-gradient(180deg, #86e3ff, #2b6fff);
  box-shadow: 0 0 14px rgba(48,199,255,.45); border:1px solid rgba(48,199,255,.35);
}
.bot-lines .bot-line{ width:180px; height:10px; background:rgba(255,255,255,.15); border-radius:6px; margin:4px 0; }
.bot-lines .bot-line.short{ width:120px; }

/* 视频播放器 */
.video-player{ margin-top:10px; padding:8px; background:rgba(20,40,70,.4); border-radius:6px; border:1px solid rgba(48,199,255,.2); }
.video-controls{ display:flex; align-items:center; gap:8px; }
.play-btn, .volume-btn{ 
  width:24px; height:24px; border:none; background:rgba(48,199,255,.3); 
  color:var(--glow-cyan); border-radius:4px; cursor:pointer; 
  display:flex; align-items:center; justify-content:center; font-size:12px;
}
.play-btn:hover, .volume-btn:hover{ background:rgba(48,199,255,.5); }
.time-display, .duration{ font-size:12px; color:#ffffff; min-width:35px; }
.progress-bar{ flex:1; height:4px; background:rgba(255,255,255,.1); border-radius:2px; overflow:hidden; }
.progress-fill{ height:100%; width:20%; background:linear-gradient(90deg, #ffd700, #ffed4e); box-shadow:0 0 6px rgba(255,215,0,.6); }

/* 中间 Three.js 容器 */
.center{ position:relative; background: radial-gradient(1200px 800px at 50% 50%, rgba(15, 35, 55, .8), rgba(10,26,46,.9)); border: 1px solid var(--panel-border); border-radius: 12px; overflow:hidden; }
.three-root{ position:absolute; inset:0; }
.glow-arc{
  position:absolute; bottom:0; left:0; right:0; height:60px;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 215, 0, 0.8) 20%, 
    rgba(255, 215, 0, 1) 50%, 
    rgba(255, 215, 0, 0.8) 80%, 
    transparent 100%);
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.6);
  border-radius: 50% 50% 0 0;
  transform: translateY(50%);
  opacity: 0.8;
  animation: glow-pulse 3s ease-in-out infinite;
}
@keyframes glow-pulse {
  0%, 100% { opacity: 0.6; transform: translateY(50%) scaleX(1); }
  50% { opacity: 1; transform: translateY(50%) scaleX(1.1); }
}

/* 右侧 */
.right-panel{ display:flex; flex-direction:column; gap:14px; }
.kpi-bars{ padding:6px 4px 0; }
.kpi-row{ display:grid; grid-template-columns: 80px 1fr 50px; align-items:center; gap:8px; margin-bottom:8px; }
.kpi-name{ color: #ffffff; font-size:12px; }
.kpi-val{ text-align:right; color:#ffffff; }
.kpi-bar{ height:10px; background:rgba(255,255,255,.12); border-radius:10px; overflow:hidden; border:1px solid rgba(255,255,255,.15); }
.kpi-bar-fill{ height:100%; background: linear-gradient(90deg, var(--glow-blue), var(--glow-cyan)); box-shadow: 0 0 10px rgba(43,212,255,.65) inset; }

.chart{ height:160px; margin-top:8px; border:1px solid rgba(255,255,255,.15); border-radius:8px; background:rgba(20,40,70,.3); }
.legend{ display:flex; gap:12px; margin-top:8px; color:#ffffff; font-size:12px; }
.legend-item{ display:flex; align-items:center; gap:6px; }
.legend-dot{ width:10px; height:10px; border-radius:50%; box-shadow:0 0 6px rgba(255,255,255,.35); }

.health{ margin-top:10px; padding:10px; border-radius:10px; background: rgba(20,40,70,.5); border:1px solid rgba(48,199,255,.2); }
.health-head{ display:flex; align-items:center; justify-content:space-between; }
.health .name{ font-weight:700; color:#ffffff; }
.health .desc{ color: #ffffff; font-size:12px; margin-top:2px; }
.status{ padding:2px 8px; border-radius:4px; font-size:12px; font-weight:700; border:1px solid rgba(255,255,255,.2); }
.status.ok{ color:#18e07d; background: rgba(24,224,125,.15); }
.status.bad{ color:#ff6b6b; background: rgba(255,107,107,.15); }
.bar{ height:12px; background: rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.15); border-radius:10px; margin-top:10px; overflow:hidden; }
.bar-fill{ height:100%; border-radius:10px; box-shadow: 0 0 12px rgba(255,255,255,.25) inset; }
.percent{ text-align:right; margin-top:6px; color:#ffffff; }

/* 响应式 */
@media (max-width: 1280px){
  .layout{ grid-template-columns: 280px 1fr 360px; }
}
@media (max-width: 1024px){
  .layout{ grid-template-columns: 1fr; }
  .left-panel{ order:2; }
  .right-panel{ order:3; }
  .center{ order:1; height: 60vh; }
}
</style>

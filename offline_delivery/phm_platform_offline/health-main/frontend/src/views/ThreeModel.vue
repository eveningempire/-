<script setup>
import { onMounted, ref } from "vue";
import * as THREE from "three";
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {FBXLoader} from 'three/addons/loaders/FBXLoader.js';

const modelContainer = ref(null);

onMounted(() => {
  // const meshmaterial = new THREE.MeshLambertMaterial({ color: 0xffffff, opacity: 1, transparent: true });
  // 1. 创建场景
  const scene = new THREE.Scene();
    const manager = new THREE.LoadingManager();

  // 2. 添加光照
  const light = new THREE.PointLight(0x606060);
  light.position.set(300, 400, 200);
  
  scene.add(light);
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const spotLight = new THREE.SpotLight(0xffffff, 1);
    spotLight.position.set(10, 10, 10);
    scene.add(spotLight);

  const hemiLight = new THREE.HemisphereLight(0xffffff, 0x444444, 9);
    hemiLight.position.set(100, 100, 0);
    scene.add(hemiLight);
  // 3. 创建相机
  const width = modelContainer.value.clientWidth;
  const height = modelContainer.value.clientHeight;
  const camera = new THREE.PerspectiveCamera(45, width / height, 1, 1000);
  camera.position.set(100, 300, 100);
  camera.lookAt(scene.position);


  // 4. 创建渲染器
   const renderer = new THREE.WebGLRenderer({antialias: true, alpha: true});
  renderer.setSize(width, height);
  //renderer.setClearColor('0x0f2249');
  modelContainer.value.appendChild(renderer.domElement);
    renderer.setPixelRatio(window.devicePixelRatio);
  // 5. 轨道控制
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  const loader = new FBXLoader(manager);
    loader.load('/models/运载器.fbx', (group) => {
group.traverse((child) => {

        if (child.isMesh) {
          child.castShadow = true;
          child.receiveShadow = true;
          child.material.needsUpdate = true; // 标记材质需要更新
        }

      });
      // 🟡 放大模型
  group.scale.set(4, 4, 4)  // 根据模型实际情况调整这个比例

      scene.add(group);
    })
  // 7. 渲染循环
  function animate() {
    requestAnimationFrame(animate);
    controls.update();
 
    renderer.render(scene, camera);
    // console.log(
    //     `Rotation: X=${rotationX.toFixed(2)}, Y=${rotationY.toFixed(2)}, Z=${rotationZ.toFixed(2)} | ` +
    //     `Position: X=${positionX.toFixed(2)}, Y=${positionY.toFixed(2)}, Z=${positionZ.toFixed(2)}`
    // );
  }
  animate();
   // 窗口大小调整
   window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
  });
});

</script>

<template>
  <div ref="modelContainer" style="width: 52rem; display: flex; justify-content: center; align-items: center; height: 35rem;"></div>
</template>
<template>
  <div class="model-3d-test">
    <div class="header">
      <h1>3D模型测试页面</h1>
      <p>点击3D模型中的子部件查看名称</p>
    </div>
    
    <div class="model-container">
      <div ref="threeContainer" class="three-container"></div>
      
      <div class="info-panel">
        <h3>部件信息</h3>
        <div v-if="selectedPart" class="part-info">
          <p><strong>部件名称：</strong>{{ selectedPart.name }}</p>
          <p><strong>部件ID：</strong>{{ selectedPart.id }}</p>
        </div>
        <div v-else class="no-selection">
          <p>请点击3D模型中的部件</p>
        </div>
      </div>
    </div>
    
    <div class="controls">
      <button @click="resetCamera">重置视角</button>
      <button @click="toggleWireframe">切换线框模式</button>
      <button @click="toggleAutoRotate">切换自动旋转</button>
      <button @click="clearHighlight">清除高亮</button>
    </div>
  </div>
</template>

<script>
import * as THREE from 'three'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js'
import { MTLLoader } from 'three/examples/jsm/loaders/MTLLoader.js'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

export default {
  name: 'Model3DTest',
  data() {
    return {
      selectedPart: null,
      wireframeMode: false,
      autoRotate: false,
      partMapping: {
        'Fillet5': '低速框架作动电机',
        'Boss-Extrude1': '低速框架转动装置',
        'Cut-Extrude2': '低速框架',
        'T-Motor F80Pro.step<1>[2]': '高速转子轴系',
        'T-Motor F80Pro.step<1>[3]': '高速转子电机'
      }
    }
  },
  mounted() {
    // 将Three.js对象存储在组件实例上，避免响应式代理
    this.scene = new THREE.Scene()
    this.camera = null
    this.renderer = null
    this.controls = null
    this.model = null
    this.raycaster = new THREE.Raycaster()
    this.mouse = new THREE.Vector2()
    
    this.initThreeJS()
    this.loadModel()
    this.animate()
  },
  beforeUnmount() {
    if (this.renderer) {
      this.renderer.dispose()
    }
    // 清理事件监听器
    if (this.renderer && this.renderer.domElement) {
      this.renderer.domElement.removeEventListener('click', this.onMouseClick)
    }
    window.removeEventListener('resize', this.onWindowResize)
  },
  methods: {
    initThreeJS() {
      // 创建场景
      this.scene.background = new THREE.Color(0xf0f0f0)
      
      // 创建相机
      const container = this.$refs.threeContainer
      const width = container.clientWidth
      const height = container.clientHeight
      
      this.camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
      this.camera.position.set(5, 5, 5)
      
      // 创建渲染器
      this.renderer = new THREE.WebGLRenderer({ antialias: true })
      this.renderer.setSize(width, height)
      this.renderer.shadowMap.enabled = true
      this.renderer.shadowMap.type = THREE.PCFSoftShadowMap
      container.appendChild(this.renderer.domElement)
      
      // 添加控制器
      this.controls = new OrbitControls(this.camera, this.renderer.domElement)
      this.controls.enableDamping = true
      this.controls.dampingFactor = 0.05
      this.controls.enableZoom = true
      this.controls.enablePan = true
      
      // 添加光源
      this.addLights()
      
      // 添加点击事件监听
      this.renderer.domElement.addEventListener('click', this.onMouseClick)
      
      // 添加窗口大小变化监听
      window.addEventListener('resize', this.onWindowResize)
    },
    
    addLights() {
      // 环境光
      const ambientLight = new THREE.AmbientLight(0x404040, 0.6)
      this.scene.add(ambientLight)
      
      // 方向光
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
      directionalLight.position.set(10, 10, 5)
      directionalLight.castShadow = true
      directionalLight.shadow.mapSize.width = 2048
      directionalLight.shadow.mapSize.height = 2048
      this.scene.add(directionalLight)
      
      // 点光源
      const pointLight = new THREE.PointLight(0xffffff, 0.5)
      pointLight.position.set(-10, 10, -10)
      this.scene.add(pointLight)
    },
    
    loadModel() {
      // 加载材质文件
      const mtlLoader = new MTLLoader()
      mtlLoader.setPath('/3dmodel/')
      mtlLoader.load('3D模型材料.mtl', (materials) => {
        materials.preload()
        
        // 加载OBJ模型
        const objLoader = new OBJLoader()
        objLoader.setMaterials(materials)
        objLoader.setPath('/3dmodel/')
        objLoader.load('3D模型网格.obj', (object) => {
          this.model = object
          
          // 设置模型位置和缩放
          this.model.position.set(0, 0, 0)
          this.model.scale.set(1, 1, 1)
          
          // 为每个子对象添加用户数据，用于识别部件
          this.model.traverse((child) => {
            if (child.isMesh) {
              child.castShadow = true
              child.receiveShadow = true
              
              // 安全地保存原始材质属性
              let originalColor = 0xffffff // 默认白色
              let originalEmissive = 0x000000 // 默认无发光
              
              try {
                if (child.material && child.material.color) {
                  originalColor = child.material.color.getHex()
                }
                if (child.material && child.material.emissive) {
                  originalEmissive = child.material.emissive.getHex()
                }
              } catch (error) {
                console.warn('无法获取材质属性:', child.name, error)
              }
              
              // 添加用户数据，包含部件名称和原始材质属性
              const partName = this.getPartName(child.name)
              child.userData = {
                partName: partName,
                originalName: child.name,
                originalColor: originalColor,
                originalEmissive: originalEmissive
              }
            }
          })
          
          this.scene.add(this.model)
          
          // 调整相机位置以适应模型
          this.fitCameraToModel()
          
          console.log('3D模型加载成功')
        }, undefined, (error) => {
          console.error('OBJ模型加载失败:', error)
          this.showErrorMessage('3D模型加载失败，请检查文件路径')
        })
      }, undefined, (error) => {
        console.error('MTL材质加载失败:', error)
        this.showErrorMessage('材质文件加载失败，请检查文件路径')
      })
    },
    
    getPartName(originalName) {
      // 根据配置映射获取部件名称
      return this.partMapping[originalName] || originalName
    },
    
    fitCameraToModel() {
      if (!this.model) return
      
      const box = new THREE.Box3().setFromObject(this.model)
      const center = box.getCenter(new THREE.Vector3())
      const size = box.getSize(new THREE.Vector3())
      
      const maxDim = Math.max(size.x, size.y, size.z)
      const fov = this.camera.fov * (Math.PI / 180)
      let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2))
      cameraZ *= 1.5 // 增加一些距离
      
      this.camera.position.set(cameraZ, cameraZ, cameraZ)
      this.camera.lookAt(center)
      this.controls.target.copy(center)
      this.controls.update()
    },
    
    onMouseClick(event) {
      const rect = this.renderer.domElement.getBoundingClientRect()
      this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
      this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
      
      this.raycaster.setFromCamera(this.mouse, this.camera)
      
      if (this.model) {
        const intersects = this.raycaster.intersectObject(this.model, true)
        
        if (intersects.length > 0) {
          const clickedObject = intersects[0].object
          
          // 查找包含用户数据的父对象
          let targetObject = clickedObject
          while (targetObject && !targetObject.userData.partName) {
            targetObject = targetObject.parent
          }
          
          if (targetObject && targetObject.userData.partName) {
            this.selectedPart = {
              name: targetObject.userData.partName,
              id: targetObject.userData.originalName
            }
            
            // 高亮选中的部件
            this.highlightPart(targetObject)
            
            console.log('选中部件:', this.selectedPart)
          }
        }
      }
    },
    
    highlightPart(object) {
      // 重置所有部件的高亮
      this.model.traverse((child) => {
        if (child.isMesh && child.material) {
          try {
            // 恢复原始材质属性
            if (child.material.color) {
              child.material.color.setHex(child.userData.originalColor)
            }
            if (child.material.emissive) {
              child.material.emissive.setHex(child.userData.originalEmissive)
            }
            child.material.needsUpdate = true
          } catch (error) {
            console.warn('无法恢复材质属性:', child.name, error)
          }
        }
      })
      
      // 高亮选中的部件
      if (object && object.isMesh && object.material) {
        try {
          // 设置高亮效果
          if (object.material.color) {
            object.material.color.setHex(0xff6b35) // 橙色高亮
          }
          if (object.material.emissive) {
            object.material.emissive.setHex(0x222222) // 轻微发光
          }
          object.material.needsUpdate = true
        } catch (error) {
          console.warn('无法设置高亮效果:', object.name, error)
        }
      }
    },
    
    resetCamera() {
      this.fitCameraToModel()
    },
    
    clearHighlight() {
      // 清除所有高亮效果
      if (this.model) {
        this.model.traverse((child) => {
          if (child.isMesh && child.material) {
            try {
              // 恢复原始材质属性
              if (child.material.color) {
                child.material.color.setHex(child.userData.originalColor)
              }
              if (child.material.emissive) {
                child.material.emissive.setHex(child.userData.originalEmissive)
              }
              child.material.needsUpdate = true
            } catch (error) {
              console.warn('无法恢复材质属性:', child.name, error)
            }
          }
        })
      }
      
      // 清除选中的部件信息
      this.selectedPart = null
    },
    
    toggleWireframe() {
      this.wireframeMode = !this.wireframeMode
      if (this.model) {
        this.model.traverse((child) => {
          if (child.isMesh) {
            child.material.wireframe = this.wireframeMode
          }
        })
      }
    },
    
    toggleAutoRotate() {
      this.autoRotate = !this.autoRotate
      this.controls.autoRotate = this.autoRotate
    },
    
    onWindowResize() {
      const container = this.$refs.threeContainer
      const width = container.clientWidth
      const height = container.clientHeight
      
      this.camera.aspect = width / height
      this.camera.updateProjectionMatrix()
      this.renderer.setSize(width, height)
    },
    
    animate() {
      requestAnimationFrame(this.animate)
      this.controls.update()
      this.renderer.render(this.scene, this.camera)
    },
    
    showErrorMessage(message) {
      // 简单的错误提示
      alert(message)
    }
  }
}
</script>

<style scoped>
.model-3d-test {
  padding: 20px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  margin-bottom: 20px;
  text-align: center;
}

.header h1 {
  color: #333;
  margin-bottom: 10px;
}

.header p {
  color: #666;
  font-size: 14px;
}

.model-container {
  flex: 1;
  display: flex;
  gap: 20px;
  min-height: 0;
}

.three-container {
  flex: 1;
  border: 1px solid #ddd;
  border-radius: 8px;
  background: #f9f9f9;
  position: relative;
}

.info-panel {
  width: 300px;
  padding: 20px;
  background: white;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.info-panel h3 {
  margin-top: 0;
  color: #333;
  border-bottom: 1px solid #eee;
  padding-bottom: 10px;
}

.part-info {
  margin-top: 15px;
}

.part-info p {
  margin: 10px 0;
  color: #555;
}

.no-selection {
  margin-top: 15px;
  color: #999;
  font-style: italic;
}

.controls {
  margin-top: 20px;
  display: flex;
  gap: 10px;
  justify-content: center;
}

.controls button {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.controls button:hover {
  background: #0056b3;
}

.controls button:active {
  background: #004085;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .model-container {
    flex-direction: column;
  }
  
  .info-panel {
    width: 100%;
  }
  
  .three-container {
    height: 400px;
  }
}
</style>
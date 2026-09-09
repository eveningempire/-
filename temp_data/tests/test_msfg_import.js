// 测试多信号流图导入功能
// 这个脚本用于验证JSON文件导入和模块树显示功能

// 模拟导入的JSON数据结构（缺少system_id和parent_id）
const testImportData = {
  "SystemData": [
    {
      "data": {
        "nodes": [
          {
            "id": "test1",
            "type": "test-node",
            "x": 100,
            "y": 100,
            "text": {
              "value": "测试点1"
            },
            "properties": {
              "typeColor": "#eea2a4"
            }
          },
          {
            "id": "fault1",
            "type": "fault-node",
            "x": 300,
            "y": 100,
            "text": {
              "value": "故障1"
            },
            "properties": {
              "typeColor": "#edc3ae"
            }
          }
        ],
        "edges": [
          {
            "id": "edge1",
            "sourceNodeId": "test1",
            "targetNodeId": "fault1",
            "type": "polyline"
          }
        ]
      }
    }
  ]
};

// 模拟_fixImportDataStructure方法
function _fixImportDataStructure(data) {
  // 如果导入的数据缺少system_id和parent_id字段，自动添加
  if (data.SystemData && Array.isArray(data.SystemData)) {
    data.SystemData.forEach((system, index) => {
      // 添加system_id
      if (system.system_id === undefined) {
        system.system_id = index + 1
      }
      // 添加parent_id（第一个系统作为根系统）
      if (system.parent_id === undefined) {
        system.parent_id = index === 0 ? null : 1
      }
      // 添加name字段（如果没有的话）
      if (!system.name) {
        system.name = index === 0 ? "root" : `子系统${system.system_id}`
      }
    })
  }
  return data
}

// 模拟getModuleTree方法
function getModuleTree(gData) {
  // 检查数据是否有效
  if (!gData || !Array.isArray(gData) || gData.length === 0) {
    console.warn('getModuleTree: 无效的gData', gData)
    return []
  }

  // 查找根系统
  let root = gData.find(item => item.parent_id == null)
  if (!root) {
    console.warn('getModuleTree: 找不到根系统，使用第一个系统作为根', gData)
    root = gData[0]
    // 如果第一个系统也没有parent_id，设置为根系统
    if (root.parent_id !== null) {
      root.parent_id = null
    }
  }

  let root_node = {
    label: root.name || 'root',
    id: root.system_id,
    children: []
  }

  function getModuleTreeRecursive(node, gData_) {
    let children = gData_.filter(item => item.parent_id == node.id)
    if (children.length == 0) {
      return null
    }
    children.forEach(item => {
      let child_node = {
        label: item.name || `子系统${item.system_id}`,
        id: item.system_id,
        children: []
      }
      node.children.push(child_node)
      getModuleTreeRecursive(child_node, gData_)
    })
  }

  getModuleTreeRecursive(root_node, gData)
  return [root_node]
}

// 测试修复功能
console.log('=== 测试多信号流图导入功能 ===');

console.log('1. 原始导入数据:');
console.log(JSON.stringify(testImportData, null, 2));

console.log('\n2. 修复后的数据:');
const fixedData = _fixImportDataStructure(testImportData);
console.log(JSON.stringify(fixedData, null, 2));

console.log('\n3. 生成的模块树:');
const moduleTree = getModuleTree(fixedData.SystemData);
console.log(JSON.stringify(moduleTree, null, 2));

console.log('\n4. 验证结果:');
console.log('- 是否包含system_id:', fixedData.SystemData[0].system_id !== undefined);
console.log('- 是否包含parent_id:', fixedData.SystemData[0].parent_id !== undefined);
console.log('- 是否包含name:', fixedData.SystemData[0].name !== undefined);
console.log('- 模块树是否生成:', moduleTree.length > 0);
console.log('- 根节点名称:', moduleTree[0]?.label);

console.log('\n=== 测试完成 ===');

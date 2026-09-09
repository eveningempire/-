# MSFG内存优化解决方案

## 🚨 当前问题
您的JSON文件包含大量节点（约1800+行），导致浏览器处理时出现"out of memory"错误。

## 🔧 立即解决方案

### 方案1：分批导入（推荐）
1. **将大JSON文件分割成较小的部分**
2. **分多次导入，每次导入一部分节点**
3. **逐步构建完整的MSFG**

### 方案2：简化JSON结构
从您的JSON中删除非必要的属性：
```json
// 保留核心属性
{
  "id": "节点ID",
  "type": "test-node" | "fault-node",
  "text": {"value": "节点名称"},
  "x": 坐标X,
  "y": 坐标Y
}

// 删除这些属性（可选）
- properties.collision
- properties.detectable  
- properties.fuzzible
- properties.ui
- properties.typeColor
- anchors (锚点信息)
```

### 方案3：浏览器优化
1. **关闭其他浏览器标签页**
2. **增加浏览器内存限制**：
   ```
   chrome.exe --max_old_space_size=8192
   ```
3. **使用更强大的浏览器**（Chrome/Edge最新版）

## 🎯 核心建议

### JSON结构简化示例：
```json
{
  "SystemData": [{
    "data": {
      "nodes": [
        {
          "id": "test1",
          "type": "test-node", 
          "text": {"value": "温度检测"},
          "x": 100, "y": 100
        },
        {
          "id": "fault1", 
          "type": "fault-node",
          "text": {"value": "过热故障"},
          "x": 300, "y": 100
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
  }]
}
```

## ✅ 已实现的改进

1. **✅ 用户自定义配置名称**
   - 添加 `configName` 参数支持
   - 支持在导入时指定配置名称

2. **✅ 删除配置功能** 
   - DELETE `/api/v1/msfg/msfg-definitions/{id}/`
   - 自动处理激活状态转移
   - 清理相关数据

## 🔄 下一步建议

1. **先尝试简化版JSON**：删除非必要属性
2. **测试导入功能**：确认基本功能正常
3. **如果仍有问题**：考虑分批导入方案
4. **长期优化**：前端虚拟化渲染大量节点

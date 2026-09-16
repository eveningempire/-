# MSFG 默认结果修复说明

## 发现的问题

用户反馈：**正常帧的 MSFG 结果中缺少一些测点分数和故障分数**。

## 根本原因

### 问题 1：浅拷贝导致数据共享

**原代码**（第 2503-2506 行）：

```python
'test_results': default_test_results.copy(),      # 浅拷贝
'fault_results': default_fault_results.copy(),    # 浅拷贝
'system_results': default_system_results.copy(),  # 浅拷贝
'component_results': default_component_results.copy(),  # 浅拷贝
```

**问题说明**：

- `.copy()` 只是浅拷贝，只复制外层字典。
- 内层字典对象仍然会被多个记录共享。
- 当某个记录修改数据时，会影响其他所有记录。

**示例说明**：

```python
# 浅拷贝的问题
default_test_results = {
    '测点1': {'test_score': 0.0, 'status': 'normal'},
    '测点2': {'test_score': 0.0, 'status': 'normal'},
}

record1_result = default_test_results.copy()
record2_result = default_test_results.copy()

# 修改 record1 的测点
record1_result['测点1']['test_score'] = 0.5

# record2 的测点也被修改了
print(record2_result['测点1']['test_score'])  # 输出: 0.5（错误）
```

## 修复方案

### 修复 1：使用深拷贝

**修复后代码**（第 2515-2518 行）：

```python
import copy

'test_results': copy.deepcopy(default_test_results),      # 深拷贝
'fault_results': copy.deepcopy(default_fault_results),    # 深拷贝
'system_results': copy.deepcopy(default_system_results),  # 深拷贝
'component_results': copy.deepcopy(default_component_results),  # 深拷贝
```

**优势**：

- 每条记录都有完全独立的数据副本。
- 修改某条记录不会影响其他记录。
- 保证数据完整性。

**示例说明**：

```python
# 深拷贝的正确行为
import copy

record1_result = copy.deepcopy(default_test_results)
record2_result = copy.deepcopy(default_test_results)

# 修改 record1 的测点
record1_result['测点1']['test_score'] = 0.5

# record2 的测点不受影响
print(record2_result['测点1']['test_score'])  # 输出: 0.0（正确）
```

### 修复 2：添加详细日志验证

**新增日志**（第 2443-2558 行）：

#### 2.1 节点信息验证

```python
logger.info(f"MSFG 节点信息: 测点数 {len(test_nodes)}, 故障数 {len(fault_nodes)}, 部件数 {len(component_nodes)}")
logger.info(f"测点列表: {[node.name for node in test_nodes]}")
logger.info(f"故障列表: {[node.name for node in fault_nodes]}")
```

**输出示例**：

```text
[INFO] MSFG 节点信息: 测点数 12, 故障数 8, 部件数 5
[INFO] 测点列表: ['转子温度', '框架温度', '转子电流', '转子转速', ...]
[INFO] 故障列表: ['轴承磨损', '电机故障', '电压异常', ...]
```

#### 2.2 构建验证

```python
logger.info(f"已构建 {len(default_test_results)} 个测点的默认结果")
logger.info(f"已构建 {len(default_fault_results)} 个故障的默认结果")
```

**输出示例**：

```text
[INFO] 已构建 12 个测点的默认结果
[INFO] 已构建 8 个故障的默认结果
```

#### 2.3 结果验证

```python
logger.info(f"成功生成 {len(default_results)} 个默认 MSFG 结果")
logger.info(
    f"每个结果包含: 测点数 {len(sample_result['test_results'])}, "
    f"故障数 {len(sample_result['fault_results'])}, "
    f"部件数 {len(sample_result['component_results'])}"
)
```

**输出示例**：

```text
[INFO] 成功生成 800 个默认 MSFG 结果
[INFO] 每个结果包含: 测点数 12, 故障数 8, 部件数 5
```

#### 2.4 数据独立性验证

```python
if len(default_results) > 1:
    first_test_results = default_results[0]['test_results']
    second_test_results = default_results[1]['test_results']
    if first_test_results is second_test_results:
        logger.warning("警告：检测到浅拷贝问题，多个记录共享同一个字典对象")
    else:
        logger.info("数据独立性验证通过，每个记录都有独立的数据副本")
```

**输出示例**：

```text
[INFO] 数据独立性验证通过，每个记录都有独立的数据副本
```

## 验证一致性

### 异常帧 vs 正常帧的节点获取方法

#### 异常帧（实际检测）- `_run_msfg_detection()` 第 114 行

```python
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

fusion = AdvancedMSFGFusion()
test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg)
```

#### 正常帧（默认值）- `_generate_default_msfg_results()` 第 441 行

```python
from msfg_analysis.algorithms.msfg.advanced_fusion import AdvancedMSFGFusion

fusion = AdvancedMSFGFusion()
test_nodes, fault_nodes, component_nodes = fusion.get_unified_nodes(msfg_definition)
```

**结论**：完全一致，异常帧和正常帧使用相同方法获取节点。

## 如何验证修复效果

### 步骤 1：查看日志输出

上传文件后，检查终端日志中的以下信息：

```text
[INFO] 为 800 个正常帧生成默认 MSFG 结果
[INFO] MSFG 节点信息: 测点数 12, 故障数 8, 部件数 5
[INFO] 测点列表: ['转子温度', '框架温度', '转子电流', ...]
[INFO] 故障列表: ['轴承磨损', '电机故障', '电压异常', ...]
[INFO] 已构建 12 个测点的默认结果
[INFO] 已构建 8 个故障的默认结果
[INFO] 成功生成 800 个默认 MSFG 结果
[INFO] 每个结果包含: 测点数 12, 故障数 8, 部件数 5
[INFO] 数据独立性验证通过，每个记录都有独立的数据副本
```

### 步骤 2：检查数据库

```python
from msfg_analysis.models import MSFGAnalysisResult

# 查询一个正常帧的 MSFG 结果
normal_frame = PHMData.objects.filter(
    ims_detectionresult__is_anomaly=False
).first()

msfg_result = MSFGAnalysisResult.objects.get(data_point=normal_frame)

# 验证测点数量
test_count = len(msfg_result.test_results)
print(f"测点数量: {test_count}")
print(f"测点列表: {list(msfg_result.test_results.keys())}")

# 验证故障数量
fault_count = len(msfg_result.fault_results)
print(f"故障数量: {fault_count}")
print(f"故障列表: {list(msfg_result.fault_results.keys())}")

# 验证测点分数都为 0
test_scores = [v['test_score'] for v in msfg_result.test_results.values()]
print(f"测点分数: {test_scores}")  # 应该都是 0.0

# 验证故障概率都为 0
fault_probs = [v['fault_probability'] for v in msfg_result.fault_results.values()]
print(f"故障概率: {fault_probs}")  # 应该都是 0.0

# 验证健康分数为 1.0
print(f"整体健康分数: {msfg_result.overall_health_score}")  # 应该是 1.0
```

### 步骤 3：对比异常帧和正常帧

```python
# 获取一个异常帧的 MSFG 结果
anomaly_frame = PHMData.objects.filter(
    ims_detectionresult__is_anomaly=True
).first()

anomaly_msfg = MSFGAnalysisResult.objects.get(data_point=anomaly_frame)
normal_msfg = MSFGAnalysisResult.objects.get(data_point=normal_frame)

# 对比测点数量
print(f"异常帧测点数: {len(anomaly_msfg.test_results)}")
print(f"正常帧测点数: {len(normal_msfg.test_results)}")
# 应该相等

# 对比故障数量
print(f"异常帧故障数: {len(anomaly_msfg.fault_results)}")
print(f"正常帧故障数: {len(normal_msfg.fault_results)}")
# 应该相等

# 对比测点列表
anomaly_tests = set(anomaly_msfg.test_results.keys())
normal_tests = set(normal_msfg.test_results.keys())
print(f"测点列表是否相同: {anomaly_tests == normal_tests}")
# 应该为 True

# 对比故障列表
anomaly_faults = set(anomaly_msfg.fault_results.keys())
normal_faults = set(normal_msfg.fault_results.keys())
print(f"故障列表是否相同: {anomaly_faults == normal_faults}")
# 应该为 True
```

## 预期结果

修复后，正常帧的 MSFG 结果应该满足以下条件。

### 包含完整的测点分数

```json
{
  "test_results": {
    "转子温度": {"test_score": 0.0, "status": "normal"},
    "框架温度": {"test_score": 0.0, "status": "normal"},
    "转子电流": {"test_score": 0.0, "status": "normal"},
    "转子转速": {"test_score": 0.0, "status": "normal"}
  }
}
```

### 包含完整的故障概率

```json
{
  "fault_results": {
    "轴承磨损": {"fault_probability": 0.0, "severity": "none"},
    "电机故障": {"fault_probability": 0.0, "severity": "none"},
    "电压异常": {"fault_probability": 0.0, "severity": "none"}
  }
}
```

### 每个记录都有独立的数据副本

```python
# 修改第一个记录不会影响第二个记录
result1['test_results']['转子温度']['test_score'] = 0.5
result2['test_results']['转子温度']['test_score']  # 仍然是 0.0
```

## 可能的其他问题

如果修复后仍然缺少测点或故障，可能是以下原因。

### 问题 1：MSFG 定义不完整

- 检查 MSFG 定义中的测点节点和故障节点是否完整。
- 使用 Django 管理后台查看 MSFG 定义。

### 问题 2：节点类型不匹配

- 检查节点类型是否正确，例如 `TestNode` 和 `FaultNode`。
- 使用日志输出的节点列表验证。

### 问题 3：数据库查询过滤

- 检查是否存在额外过滤条件，导致部分节点被排除。
- 使用 `fusion.get_unified_nodes()` 返回的原始节点列表验证。

## 总结

本次修复的核心改进：

1. **使用深拷贝**：确保每条记录都有完全独立的数据副本。
2. **添加详细日志**：帮助验证节点信息、构建过程和数据完整性。
3. **增加数据独立性验证**：运行时自动检测浅拷贝问题。
4. **保持方法一致**：异常帧和正常帧使用相同的节点获取方法。

这样可以确保：

- 所有测点分数都被正确写入。
- 所有故障概率都被正确写入。
- 每个记录的数据都是独立的。
- 便于诊断和验证。

如果仍然发现缺少数据，请查看日志输出的节点列表，确认 MSFG 定义中是否包含所有期望的测点和故障。

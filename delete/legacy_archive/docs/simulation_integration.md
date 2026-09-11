# 仿真功能集成说明

## 架构变更

为了简化代码结构并减少不必要的复杂性，我们将 `xiangmu_simulink.py` 中的仿真功能直接集成到了 `app/views/simulation.py` 中。这样做有以下好处：

1. **简化架构**：减少文件数量，让相关功能集中在同一个文件中
2. **减少导入错误**：避免模块导入问题，特别是与MATLAB Engine相关的问题
3. **集中异常处理**：在一个地方处理所有与仿真相关的异常
4. **便于维护**：对仿真逻辑进行修改只需要更新一个文件

## 变更细节

1. 将 `xiangmu_simulink.py` 中的 `run_motor_simulation()` 函数移到了 `simulation.py` 中
2. 增强了错误处理机制，包括MATLAB Engine异常的捕获和报告
3. 增加了对Simulink模型结构的动态探测，使仿真更加健壮
4. 添加了前端加载指示器，提高用户体验

## 如何使用

直接调用 `simulation.py` 中的 `run_simulation()` 路由函数，该函数会处理模型参数设置、仿真执行和结果处理。

示例请求：
```javascript
axios.post('/run-simulation', {
    BLDC_Rs: 0.62,
    BLDC_Ls: 1.12e-4,
    BLDC_p: 8.0,
    // ...其他参数
}, {
    headers: {
        'Content-Type': 'application/json'
    }
});
```

## 模型参数说明

| 参数名 | 描述 | 默认值 | 单位 |
|--------|------|---------|------|
| BLDC_Rs | 电机相电阻 | 0.62 | Ω |
| BLDC_Ls | 电机电感 | 1.12e-4 | H |
| BLDC_p | 电机极对数 | 8 | - |
| BLDC_Kt | 转矩常数 | 0.037 | - |
| Init_command_omega | 初始转速指令 | 6000 | rpm |
| fs | 仿真频率 | 100 | Hz |
| RotorInertia | 转子转动惯量 | 0.23875 | kg·m² |
| mu_EHL_input | 退化系数1(EHL摩擦系数) | 0.04 | - |
| viscosity_input | 退化系数2(黏度) | 45 | - |

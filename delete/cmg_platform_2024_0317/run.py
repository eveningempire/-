# ...existing code...

# 确保这里没有导入xiangmu_simulink
# 如果有类似下面的代码行，将其删除
# from xiangmu_simulink import run_motor_simulation

# ...existing code...

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)  # 关闭调试模式和自动重载
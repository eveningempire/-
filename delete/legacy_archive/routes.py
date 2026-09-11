from flask import Flask, render_template, request, jsonify, send_file
import os
import base64
import matplotlib
matplotlib.use('Agg')  # 避免需要GUI
import matplotlib.pyplot as plt
import io
import pandas as pd
import uuid
from xiangmu_simulink import run_motor_simulation

app = Flask(__name__)

# 存储仿真结果ID映射
sim_results = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/sim-model')
def sim_model():
    return render_template('sim-model.html')

@app.route('/run-simulation', methods=['POST'])
def run_simulation():
    try:
        # 获取前端参数
        params = request.json
        
        # 创建唯一ID用于标识此次仿真
        simulation_id = str(uuid.uuid4())
        
        # 创建保存路径
        save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              'python_matlab', 'simulation_document')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f'sim_result_{simulation_id}.csv')
        
        # 调用仿真函数
        run_motor_simulation(
            model_base_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                       'python_matlab', 'models'),
            sim_time=float(params.get('sim_time', 9.0)),
            cycle=int(params.get('cycle', 2)),
            save_path=save_path,
            operating_condition=int(params.get('operating_condition', 1)),
            BLDC_Rs=float(params.get('BLDC_Rs', 0.62)),
            BLDC_Ls=float(params.get('BLDC_Ls', 112/(10**6))),
            BLDC_p=float(params.get('BLDC_p', 8.0)),
            BLDC_Kt=float(params.get('BLDC_Kt', 0.037)),
            Init_command_omega=float(params.get('Init_command_omega', 6000.0)),
            fs=float(params.get('fs', 10**2)),
            RotorInertia=float(params.get('RotorInertia', 0.23875)),
            mu_EHL_input=float(params.get('mu_EHL_input', 0.04)),
            viscosity_input=float(params.get('viscosity_input', 45))
        )
        
        # 存储结果路径便于后续下载
        sim_results[simulation_id] = save_path
        
        # 生成结果图像
        df = pd.read_csv(save_path)
        plots = generate_plots(df)
        
        return jsonify({
            'message': '仿真完成',
            'simulation_id': simulation_id,
            'plots': plots
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download-data/<simulation_id>')
def download_data(simulation_id):
    if simulation_id in sim_results:
        return send_file(sim_results[simulation_id], as_attachment=True,
                        download_name='simulation_result.csv')
    return "仿真结果不存在", 404

@app.route('/download-simulation-data')
def download_simulation_data():
    """直接下载默认位置的仿真结果"""
    default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              'python_matlab', 'simulation_document', 
                              'sim_result_vector_concat.csv')
    if os.path.exists(default_path):
        return send_file(default_path, as_attachment=True,
                        download_name='simulation_result.csv')
    return "仿真结果不存在", 404

def generate_plots(df):
    """生成各种图像并返回base64编码"""
    plots = {}
    
    # 设置中文字体，如果系统有
    try:
        plt.rcParams['font.sans-serif'] = ['SimHei']  # 用来正常显示中文标签
        plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
    except:
        pass
    
    # 生成电流图
    plt.figure(figsize=(10, 6))
    plt.plot(df['i'])
    plt.title('电流随时间变化')
    plt.xlabel('时间点')
    plt.ylabel('电流 (A)')
    plt.grid(True)
    plots['current'] = fig_to_base64(plt.gcf())
    plt.close()
    
    # 生成电压图
    plt.figure(figsize=(10, 6))
    plt.plot(df['u'])
    plt.title('电压随时间变化')
    plt.xlabel('时间点')
    plt.ylabel('电压 (V)')
    plt.grid(True)
    plots['voltage'] = fig_to_base64(plt.gcf())
    plt.close()
    
    # 生成转速图
    plt.figure(figsize=(10, 6))
    plt.plot(df['w'])
    plt.title('转速随时间变化')
    plt.xlabel('时间点')
    plt.ylabel('转速 (rad/s)')
    plt.grid(True)
    plots['speed'] = fig_to_base64(plt.gcf())
    plt.close()
    
    # 生成摩擦力矩图
    plt.figure(figsize=(10, 6))
    plt.plot(df['FrictionTorque'])
    plt.title('摩擦力矩随时间变化')
    plt.xlabel('时间点')
    plt.ylabel('摩擦力矩 (N·m)')
    plt.grid(True)
    plots['friction'] = fig_to_base64(plt.gcf())
    plt.close()
    
    return plots

def fig_to_base64(fig):
    """将matplotlib图像转换为base64编码"""
    img_buf = io.BytesIO()
    fig.savefig(img_buf, format='png')
    img_buf.seek(0)
    img_base64 = base64.b64encode(img_buf.read()).decode('utf-8')
    return img_base64

if __name__ == '__main__':
    app.run(debug=True)

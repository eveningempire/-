import os
import uuid
import io
import base64
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request, jsonify, send_file
from app import redis_engine

# 创建蓝图
simulation_bp = Blueprint('simulation', __name__)

# 模拟仿真页面
@simulation_bp.route('/simulation', methods=['GET', 'POST'])
def result_display():
    return render_template("simulation.html")

# 仿真模型页面
@simulation_bp.route('/sim-model', methods=['GET', 'POST'])
def sim_model():
    return render_template("sim-model.html")


# 直接在此文件中实现仿真功能
def run_motor_simulation(
    model_base_path,
    sim_time: float = 9.0, #仿真时间
    cycle: int = 2, #仿真轮数
    save_path='',
    operating_condition: int = 1, #工况
    BLDC_Rs = 0.62, #电机项电阻
    BLDC_Ls = 112/(10**6), #电机项电感
    BLDC_p = 8.0, #电机级数
    BLDC_Kt = 0.037, #电机Kt常数
    Init_command_omega = 6000.0, #框架转速
    fs = 10**2, #仿真频率
    RotorInertia = 0.23875, #转子转动惯量
    mu_EHL_input = 0.04, #退化系数1
    viscosity_input = 45 #退化系数2
):
    """运行电机仿真"""
    try:
        import matlab.engine
    except ImportError:
        raise ImportError("MATLAB Engine for Python未安装或无法找到")
    
    print("启动MATLAB引擎...")
    eng = matlab.engine.start_matlab()
    
    # 根据工况选择模型名称
    if operating_condition == 1:
        model_name = "BLDC_w1"
    elif operating_condition == 2:
        model_name = "BLDC_w2"
    else:
        model_name = "BLDC_w1"  # 默认使用矩形工况
    
    # 检查模型文件是否存在
    model_file_path = os.path.join(model_base_path, f"{model_name}.slx")
    if not os.path.exists(model_file_path):
        raise FileNotFoundError(f"找不到模型文件: {model_file_path}")
    
    # 参数初始化 - 按照提供的脚本设置
    print("设置模型参数到MATLAB工作区...")
    try:
        # 基本参数设置 - 按照提供的MATLAB脚本更新
        eng.workspace['fs'] = float(fs)
        eng.workspace['Ts'] = 1.0 / float(fs)
        eng.workspace['Init_command_omega'] = float(Init_command_omega)
        eng.workspace['init_w'] = float(Init_command_omega) * math.pi / 30.0
        eng.workspace['RotorInertia'] = float(RotorInertia)
        eng.workspace['BearingSpan'] = 0.134
        
        # BLDC电机参数 - 按照提供的MATLAB脚本更新
        eng.workspace['BLDC_Rs'] = float(BLDC_Rs)
        eng.workspace['BLDC_Ls'] = float(BLDC_Ls)
        eng.workspace['BLDC_Kt'] = float(BLDC_Kt)
        eng.workspace['BLDC_BackEMF'] = 120.0
        eng.workspace['BLDC_J'] = 7.63e-4 + eng.workspace['RotorInertia']  # 修正为加法而非减法，与MATLAB保持一致
        eng.workspace['BLDC_B'] = 1.0e-6
        eng.workspace['BLDC_p'] = float(BLDC_p)
        eng.workspace['BLDC_Ke'] = float(BLDC_Kt) / (2.0 * float(BLDC_p))
        eng.workspace['POWER_DC'] = 28.0
        
        # 控制器参数计算 - 按照提供的MATLAB脚本更新
        eng.workspace['ACR_wc'] = math.sqrt(1.0/200.0) * float(fs) * 2.0 * math.pi
        eng.workspace['ACR_Pgain'] = 1.0
        eng.workspace['ACR_Igain'] = 1.0
        eng.workspace['ACR_P'] = 2.0 * float(BLDC_Ls) * eng.workspace['ACR_wc'] * eng.workspace['ACR_Pgain']
        eng.workspace['ACR_I'] = 2.0 * float(BLDC_Rs) * eng.workspace['ACR_wc'] * eng.workspace['ACR_Igain']
        eng.workspace['ACR_A'] = 1.0 / eng.workspace['ACR_P']
        eng.workspace['ACR_saturation'] = 500.0
        
        eng.workspace['ASR_Pgain'] = 1.0
        eng.workspace['ASR_Igain'] = 1.0
        eng.workspace['ASR_wc'] = 0.15 * eng.workspace['ACR_wc']
        eng.workspace['ASR_P'] = eng.workspace['BLDC_J'] * eng.workspace['ASR_wc'] / eng.workspace['BLDC_Kt'] * eng.workspace['ASR_Pgain']
        eng.workspace['ASR_I'] = eng.workspace['ASR_P'] * eng.workspace['ASR_wc'] / 5.0 * eng.workspace['ASR_Igain']  # 修正为使用ASR_P而非ACR_P
        eng.workspace['ASR_A'] = 1.0 / eng.workspace['ASR_P']
        eng.workspace['ASR_saturation'] = 5.0
        
        # 设置操作工况
        eng.workspace['operating_condition'] = float(operating_condition)
        
        print("成功设置所有模型参数到MATLAB工作区")
    except Exception as e:
        print(f"设置MATLAB工作区参数时出错: {str(e)}")
        eng.quit()
        raise
    
    # 创建退化参数序列 - 使用线性插值
    mu_EHL = np.linspace(float(mu_EHL_input), float(mu_EHL_input) * 1.5, cycle)
    viscosity = np.linspace(float(viscosity_input), float(viscosity_input) * 1.5, cycle)
    print(f"mu_EHL: {mu_EHL}")
    
    # 初始化拼接容器
    all_i, all_u, all_w, all_FrictionTorque = [], [], [], []
    
    # 多轮仿真
    for i in range(cycle):
        print(f"开始第 {i+1}/{cycle} 轮仿真...")
        
        # 设置当前轮次的参数
        eng.workspace['mu_EHL'] = float(mu_EHL[i])
        eng.workspace['viscosity'] = float(viscosity[i])
        
        # 将这些操作移到循环内部
        eng.cd(model_base_path, nargout=0)
        eng.load_system(model_name, nargout=0)
        eng.set_param(model_name, "StopTime", str(sim_time), nargout=0)
        
        print(f"  当前参数: mu_EHL = {mu_EHL[i]}, viscosity = {viscosity[i]}")
        
        # 开始仿真
        try:
            eng.sim(model_name, nargout=0)
            print(f"  第 {i+1} 轮仿真成功完成")
            
            # 获取仿真结果
            i_raw = np.array(eng.workspace['i']).flatten()
            u_raw = np.array(eng.workspace['u']).flatten()
            w_raw = np.array(eng.workspace['w']).flatten()
            FrictionTorque_raw = np.array(eng.workspace['FrictionTorque']).flatten()
            
            # 拼接结果
            all_i.extend(i_raw)
            all_u.extend(u_raw)
            all_w.extend(w_raw)
            all_FrictionTorque.extend(FrictionTorque_raw)
            
        except Exception as e:
            print(f"  第 {i+1} 轮仿真失败: {str(e)}")
            # 列出当前工作区中的变量，帮助调试
            try:
                workspace_vars = eng.eval("who", nargout=1)
                print("  当前MATLAB工作区变量:")
                for var in workspace_vars:
                    print(f"   - {var}")
            except:
                pass
            eng.quit()
            raise
    
    # 关闭MATLAB引擎
    eng.quit()
    print("MATLAB引擎已关闭")
    
    # 创建DataFrame并保存
    df = pd.DataFrame({
        'i': all_i,
        'u': all_u,
        'w': all_w,
        'FrictionTorque': all_FrictionTorque
    })
    
    # 添加时间列
    df['t'] = np.arange(len(all_i)) / float(fs)
    
    # 保存结果
    if save_path:
        # 确保目录存在
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        print(f"保存结果到: {save_path}")
        df.to_csv(save_path, index=False)
        
        # 同时保存一个固定名称的结果，方便后续分析
        default_save_path = os.path.join(os.path.dirname(save_path), 'sim_result_vector_concat.csv')
        df.to_csv(default_save_path, index=False)
    
    return df

# 运行仿真
@simulation_bp.route('/run-simulation', methods=['POST'])
def run_simulation():
    try:
        # 获取前端参数 - 修复JSON解析问题
        params = request.get_json(silent=True)  # 使用silent=True避免JSON解析错误
        if params is None:
            # 如果JSON解析失败，尝试从表单数据获取
            params = {}
            for key in request.form:
                try:
                    params[key] = float(request.form.get(key))
                except:
                    params[key] = request.form.get(key)
        
        # 创建唯一ID用于标识此次仿真
        simulation_id = str(uuid.uuid4())
        
        # 创建保存路径
        save_dir = os.path.join(os.getcwd(), 'python_matlab', 'simulation_document')
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f'sim_result_{simulation_id}.csv')
        
        # 获取项目根目录
        project_root = os.path.abspath(os.path.join(os.getcwd()))
        
        # 检查模型文件是否存在
        model_base_path = os.path.join(project_root, 'python_matlab', 'models')
        model_file_path = os.path.join(model_base_path, 'BLDC_w1.slx')
        
        if not os.path.exists(model_file_path):
            return jsonify({
                'error': f"找不到Simulink模型文件: {model_file_path}\n" + 
                         f"请确认'python_matlab/models'目录中包含BLDC_w1.slx文件"
            }), 400
            
        print(f"模型文件路径: {model_file_path}")
        
        # 添加调试信息
        print("接收到的参数:")
        for key, value in params.items():
            print(f" - {key}: {value}")
        
        # 调用仿真函数
        df = run_motor_simulation(
            model_base_path=model_base_path,
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
            viscosity_input=float(params.get('viscosity_input', 45)),
            
        )
        
        # 生成结果图像
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
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        plots['current'] = base64.b64encode(img_buf.read()).decode('utf-8')
        plt.close()
        
        # 生成电压图
        plt.figure(figsize=(10, 6))
        plt.plot(df['u'])
        plt.title('电压随时间变化')
        plt.xlabel('时间点')
        plt.ylabel('电压 (V)')
        plt.grid(True)
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        plots['voltage'] = base64.b64encode(img_buf.read()).decode('utf-8')
        plt.close()
        
        # 生成转速图
        plt.figure(figsize=(10, 6))
        plt.plot(df['w'])
        plt.title('转速随时间变化')
        plt.xlabel('时间点')
        plt.ylabel('转速 (rad/s)')
        plt.grid(True)
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        plots['speed'] = base64.b64encode(img_buf.read()).decode('utf-8')
        plt.close()
        
        # 生成摩擦力矩图
        plt.figure(figsize=(10, 6))
        plt.plot(df['FrictionTorque'])
        plt.title('摩擦力矩随时间变化')
        plt.xlabel('时间点')
        plt.ylabel('摩擦力矩 (N·m)')
        plt.grid(True)
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        plots['friction'] = base64.b64encode(img_buf.read()).decode('utf-8')
        plt.close()
        
        # 保存映射，方便后续下载
        redis_engine.hset('cmg', f'sim_result_{simulation_id}', save_path)
        
        return jsonify({
            'message': '仿真完成',
            'simulation_id': simulation_id,
            'plots': plots
        })
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"仿真过程中出现错误: {e}\n{error_detail}")
        
        # 添加更多详细的错误信息返回给前端
        error_message = {
            'error': str(e),
            'details': error_detail,
            'suggestions': [
                '1. 检查MATLAB模型是否正确加载',
                '2. 确认所有必需的参数都已正确设置',
                '3. 可能需要更新Simulink模型以解决维度问题'
            ]
        }
        return jsonify(error_message), 500

# 下载数据
@simulation_bp.route('/download-data/<simulation_id>')
def download_data(simulation_id):
    file_path = redis_engine.hget('cmg', f'sim_result_{simulation_id}')
    if file_path and os.path.exists(file_path):
        return send_file(file_path, as_attachment=True,
                        download_name='simulation_result.csv')
    return "仿真结果不存在", 404

# 下载默认仿真数据
@simulation_bp.route('/download-simulation-data')
def download_simulation_data():
    """直接下载默认位置的仿真结果"""
    default_path = os.path.join(os.getcwd(), 'python_matlab', 'simulation_document', 
                              'sim_result_vector_concat.csv')
    if os.path.exists(default_path):
        return send_file(default_path, as_attachment=True,
                        download_name='simulation_result.csv')
    return "仿真结果不存在", 404

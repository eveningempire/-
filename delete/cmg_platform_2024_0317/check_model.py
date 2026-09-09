"""
检查MATLAB仿真环境和模型文件
"""
import os
import sys
import traceback

def check_matlab_engine():
    print("检查MATLAB Engine...")
    try:
        import matlab.engine
        print("✓ MATLAB Engine已安装")
        
        print("尝试启动MATLAB引擎...")
        eng = matlab.engine.start_matlab()
        print("✓ MATLAB引擎启动成功")
        
        # 检查MATLAB版本
        ver = eng.version()
        print(f"MATLAB版本: {ver}")
        
        # 关闭引擎
        eng.quit()
        return True
    except ImportError:
        print("✗ MATLAB Engine未安装")
        print("请运行以下命令安装MATLAB Engine:")
        print("python matlab_setup.py")
        return False
    except Exception as e:
        print(f"✗ MATLAB引擎启动失败: {str(e)}")
        traceback.print_exc()
        return False

def check_model_files():
    print("\n检查Simulink模型文件...")
    # 获取根目录
    root_dir = os.path.dirname(os.path.abspath(__file__))
    model_dir = os.path.join(root_dir, 'python_matlab', 'models')
    model_file = os.path.join(model_dir, 'BLDC_w1.slx')
    
    # 检查目录是否存在
    if not os.path.exists(model_dir):
        print(f"✗ 模型目录不存在: {model_dir}")
        print(f"  创建目录: {model_dir}")
        try:
            os.makedirs(model_dir)
            print("✓ 模型目录已创建")
        except Exception as e:
            print(f"✗ 创建目录失败: {str(e)}")
        return False
    else:
        print(f"✓ 模型目录存在: {model_dir}")
    
    # 检查模型文件
    if not os.path.exists(model_file):
        print(f"✗ 模型文件不存在: {model_file}")
        print("请将BLDC_w1.slx文件放置在python_matlab/models目录下")
        return False
    else:
        print(f"✓ 模型文件存在: {model_file}")
        
    # 检查目录中的所有文件
    print("\n目录内容:")
    for file in os.listdir(model_dir):
        file_path = os.path.join(model_dir, file)
        size = os.path.getsize(file_path) / 1024  # KB
        print(f"  - {file} ({size:.2f} KB)")
    
    return True

def run_simple_test():
    print("\n尝试进行简单测试...")
    try:
        import matlab.engine
        eng = matlab.engine.start_matlab()
        
        # 获取根目录
        root_dir = os.path.dirname(os.path.abspath(__file__))
        model_dir = os.path.join(root_dir, 'python_matlab', 'models')
        model_file = os.path.join(model_dir, 'BLDC_w1.slx')
        
        # 设置工作目录
        eng.cd(model_dir, nargout=0)
        print(f"设置工作目录: {model_dir}")
        
        # 尝试加载模型
        print("尝试加载模型...")
        try:
            # 先尝试不带后缀
            eng.load_system("BLDC_w1", nargout=0)
            print("✓ 模型加载成功")
        except Exception as e1:
            print(f"无后缀模型名加载失败: {str(e1)}")
            try:
                # 再尝试带后缀
                eng.load_system(model_file, nargout=0)
                print("✓ 使用完整路径加载模型成功")
            except Exception as e2:
                print(f"✗ 无法加载模型: {str(e2)}")
                return False
        
        # 关闭引擎
        eng.quit()
        return True
    
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("MATLAB仿真环境和模型文件检查工具")
    print("=" * 50)
    
    matlab_ok = check_matlab_engine()
    model_ok = check_model_files()
    
    if matlab_ok and model_ok:
        test_ok = run_simple_test()
        if test_ok:
            print("\n✓ 所有检查通过，仿真环境正常")
        else:
            print("\n✗ 简单测试失败，请检查错误信息")
    else:
        print("\n✗ 环境检查失败，请先解决上述问题")
    
    print("\n如果问题仍然存在，请检查:")
    print("1. MATLAB安装路径是否已添加到PATH环境变量")
    print("2. MATLAB版本是否与Python版本兼容")
    print("3. 模型文件是否完整且未损坏")
    print("=" * 50)

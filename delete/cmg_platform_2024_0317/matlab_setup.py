import os
import sys
import subprocess
import platform

def find_matlab():
    """尝试查找MATLAB安装路径"""
    possible_paths = []
    
    # Windows平台
    if platform.system() == 'Windows':
        # 常见的MATLAB安装路径
        program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
        program_files_x86 = os.environ.get('PROGRAMFILES(X86)', 'C:\\Program Files (x86)')
        
        # 查找所有可能的MATLAB版本路径
        for base_path in [program_files, program_files_x86]:
            matlab_base = os.path.join(base_path, 'MATLAB')
            if os.path.exists(matlab_base):
                for item in os.listdir(matlab_base):
                    full_path = os.path.join(matlab_base, item)
                    if os.path.isdir(full_path) and item.startswith('R20'):  # MATLAB版本通常以R20xx开头
                        possible_paths.append(full_path)
    
    # Linux/Mac平台
    else:
        # Unix系统下MATLAB可能的安装位置
        unix_paths = [
            '/usr/local/MATLAB',
            '/opt/MATLAB',
            '/Applications/MATLAB',
            os.path.expanduser('~/MATLAB')
        ]
        
        for base_path in unix_paths:
            if os.path.exists(base_path):
                for item in os.listdir(base_path):
                    full_path = os.path.join(base_path, item)
                    if os.path.isdir(full_path) and item.startswith('R20'):
                        possible_paths.append(full_path)
    
    return possible_paths

def install_matlab_engine(matlab_path=None):
    """安装MATLAB Engine for Python"""
    if not matlab_path:
        paths = find_matlab()
        if not paths:
            print("未找到MATLAB安装路径，请手动指定MATLAB安装目录")
            return False
        
        # 使用找到的第一个MATLAB路径
        matlab_path = paths[0]
        print(f"找到MATLAB安装路径: {matlab_path}")
    
    # 构建engine目录路径
    engine_path = os.path.join(matlab_path, 'extern', 'engines', 'python')
    
    if not os.path.exists(engine_path):
        print(f"在 {matlab_path} 下未找到MATLAB Engine for Python目录")
        return False
    
    print(f"正在从 {engine_path} 安装MATLAB Engine for Python...")
    
    # 在engine目录下执行setup.py安装
    try:
        subprocess.check_call([sys.executable, 'setup.py', 'install'], cwd=engine_path)
        print("MATLAB Engine for Python安装成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装MATLAB Engine for Python时出错: {e}")
        return False

if __name__ == "__main__":
    # 如果命令行提供了MATLAB路径，则使用该路径
    if len(sys.argv) > 1:
        matlab_path = sys.argv[1]
        install_matlab_engine(matlab_path)
    else:
        # 否则尝试自动查找和安装
        install_matlab_engine()

    # 测试导入是否成功
    try:
        print("\n尝试导入matlab.engine...")
        import matlab.engine
        print("导入成功! MATLAB Engine可以正常使用。")
    except ImportError:
        print("\n导入失败。可能需要重启Python环境或检查安装是否成功。")
        print("您可以尝试运行以下命令进行手动安装:")
        print("cd '<MATLAB路径>/extern/engines/python'")
        print("python setup.py install")

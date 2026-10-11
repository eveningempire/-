"""Discover site-local MATLAB installations; never reuse developer paths."""
import importlib
import json
import os
import re
import shutil
from pathlib import Path

from django.conf import settings


def config_path():
    return settings.BASE_DIR / 'config' / 'matlab_runtime.json'


def read_config():
    path = config_path()
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def release_at(root):
    version = Path(root) / 'VersionInfo.xml'
    if version.is_file():
        match = re.search(r'R\d{4}[ab]', version.read_text(encoding='utf-8', errors='replace'))
        if match:
            return match.group()
    match = re.search(r'R\d{4}[ab]', str(root))
    return match.group() if match else None


def installations():
    candidates = []
    configured = os.environ.get('PHM_MATLAB_ROOT') or read_config().get('matlab_root')
    if configured:
        candidates.append(Path(configured))
    command = shutil.which('matlab.exe')
    if command:
        candidates.append(Path(command).parent.parent)
    if os.name == 'nt':
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
                try:
                    with winreg.OpenKey(hive, r'SOFTWARE\MathWorks\MATLAB', 0, winreg.KEY_READ | view) as key:
                        for index in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                with winreg.OpenKey(key, winreg.EnumKey(key, index)) as sub:
                                    candidates.append(Path(winreg.QueryValueEx(sub, 'MATLABROOT')[0]))
                            except OSError:
                                pass
                except OSError:
                    pass
        for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
            if os.environ.get(variable):
                candidates.extend((Path(os.environ[variable]) / 'MATLAB').glob('R*'))
    unique = {}
    for root in candidates:
        if (root / 'bin' / 'matlab.exe').is_file():
            unique[str(root.resolve()).lower()] = {'root': str(root.resolve()), 'release': release_at(root)}
    return list(unique.values())


def engine_status():
    found = installations()
    selected = os.environ.get('PHM_MATLAB_ROOT') or read_config().get('matlab_root')
    problems = []
    engine = None
    actual_root = None
    try:
        engine = importlib.import_module('matlab.engine')
        arch_file = Path(engine.__file__).parent / '_arch.txt'
        if arch_file.is_file():
            lines = [line.strip() for line in arch_file.read_text(encoding='utf-8').splitlines() if line.strip()]
            if len(lines) >= 2:
                actual_root = str(Path(lines[1]).resolve().parent.parent)
    except (ImportError, OSError, RuntimeError) as exc:
        problems.append(f'MATLAB Engine 不可用: {exc}')
    root = selected or actual_root or (found[0]['root'] if len(found) == 1 else None)
    release = release_at(root) if root else None
    if selected and not (Path(selected) / 'bin' / 'matlab.exe').is_file():
        problems.append('指定的 MATLAB 安装目录不存在，请使用当前电脑的路径')
    if selected and actual_root and Path(selected).resolve() != Path(actual_root).resolve():
        problems.append('已安装的 Engine 绑定另一个 MATLAB 目录，请从所选 MATLAB 的 extern/engines/python 安装匹配的 Engine')
    if root is None:
        problems.append('未找到可确定的 MATLAB 安装目录，请手动指定')
    elif release is None:
        problems.append('无法确认 MATLAB 版本，请检查安装目录的 VersionInfo.xml')
    elif release < 'R2023a':
        problems.append(f'当前 MATLAB {release} 不能保证打开 R2023a 模型；需要兼容版本或经验证的模型转换')
    return {'matlab_engine': engine is not None, 'matlab_root': root, 'engine_root': actual_root,
            'matlab_release': release, 'installations': found, 'problems': problems,
            'setup_hint': 'Engine 必须安装在本包创建的 .venv 中，并与所选 MATLAB 和 Python 3.10 匹配。MATLAB 2012 不支持这条 Python Engine 调用路径。',
            'engine_setup_directory': str(Path(root) / 'extern' / 'engines' / 'python') if root else None}


def save_root(root):
    if not isinstance(root, str) or not root.strip():
        raise ValueError('请输入 MATLAB 安装根目录，例如 C:\\Program Files\\MATLAB\\R2023a')
    path = Path(root.strip().strip('"')).resolve()
    if not (path / 'bin' / 'matlab.exe').is_file():
        raise ValueError('该目录没有 bin/matlab.exe，请选择当前电脑的 MATLAB 安装根目录')
    target = config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps({'matlab_root': str(path)}, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)


def start_engine(options):
    status = engine_status()
    if status['problems']:
        raise RuntimeError('; '.join(status['problems']))
    engine = importlib.import_module('matlab.engine').start_matlab(options)
    try:
        actual_root = engine.matlabroot()
        if Path(actual_root).resolve() != Path(status['matlab_root']).resolve():
            raise RuntimeError('Engine 启动了不同目录的 MATLAB，请重新安装匹配的 Engine')
        release = str(engine.version('-release'))
        if release.removeprefix('R') < '2023a':
            raise RuntimeError(f'实际启动版本为 {release}，与 R2023a 模型不兼容')
        if not engine.license('test', 'Simulink'):
            raise RuntimeError('当前 MATLAB 没有可用的 Simulink 许可证')
        return engine
    except Exception:
        engine.quit()
        raise

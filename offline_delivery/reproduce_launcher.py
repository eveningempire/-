from pathlib import Path
import os
import shutil
import subprocess

base = Path('E:/PHM launcher reproduction 20261010')
base.mkdir(exist_ok=True)
source = Path(__file__).resolve().parent / 'phm_platform_offline'
shutil.copy2(source / 'start_phm_platform.bat', base / 'start_phm_platform.bat')
(base / 'frontend/dist').mkdir(parents=True, exist_ok=True)
shutil.copy2(source / 'frontend/dist/index.html', base / 'frontend/dist/index.html')
(base / 'manage.py').write_text('raise SystemExit(1)\n')
# A working real interpreter; the intentional migration failure avoids launching services.
runtime = source / 'runtime/python310'
script = base / '.venv/Scripts'
script.mkdir(parents=True, exist_ok=True)
for name in ['python.exe', 'python310.dll', 'python3.dll', 'vcruntime140.dll', 'vcruntime140_1.dll']:
    shutil.copy2(runtime / name, script / name)
env = os.environ.copy()
env['PYTHONHOME'] = str(runtime)
result = subprocess.run(['C:/Windows/System32/cmd.exe', '/d', '/c',
                         'start_phm_platform.bat'], cwd=base, env=env,
                        input=b'\n\n\n', stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        timeout=60)
print(result.stdout.decode('utf-8', errors='replace'))
print('EXIT', result.returncode)

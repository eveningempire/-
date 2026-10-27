"""Install Engine from this computer's MATLAB source without fetching packages."""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')


def configure():
    from simulation_demo.matlab_runtime import installations, read_config
    configured = os.environ.get('PHM_MATLAB_ROOT') or read_config().get('matlab_root')
    candidates = installations()
    if configured:
        candidates = [item for item in candidates if Path(item['root']).resolve() == Path(configured).resolve()]
    if not candidates:
        print('MATLAB not detected. Offline data generation and analysis remain available.')
        return 0
    if len(candidates) != 1:
        print('Multiple MATLAB installations found. Select one in the fault-injection page first.')
        return 0
    if importlib.util.find_spec('matlab'):
        print('MATLAB Python package already installed. Check Engine status in the platform.')
        return 0
    matlab = Path(candidates[0]['root'])
    source = matlab / 'extern/engines/python'
    setup = source / 'setup.py'
    if not setup.is_file() or not (source / 'dist/matlab').is_dir():
        print(f'{candidates[0]["release"]}: no bundled Engine source suitable for offline installation.')
        return 0
    if '3.10' not in setup.read_text(encoding='utf-8-sig', errors='replace'):
        print(f'{candidates[0]["release"]}: bundled Engine does not declare Python 3.10 support.')
        return 0
    print(f'Configuring MATLAB Engine from {matlab} (offline)...', flush=True)
    env = os.environ.copy()
    env.update(PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1',
               PYTHONNOUSERSITE='1', SETUPTOOLS_USE_DISTUTILS='stdlib')
    (ROOT / 'logs').mkdir(exist_ok=True)
    log = ROOT / 'logs/matlab-engine-setup.log'
    with tempfile.TemporaryDirectory(prefix='engine-', dir=str(ROOT / 'logs')) as directory, log.open('wb') as output:
        try:
            subprocess.run([sys.executable, str(setup), 'build', '--build-base', str(Path(directory)/'build'),
                            'install', '--prefix', sys.prefix, '--install-lib', str(Path(sys.prefix)/'Lib/site-packages'),
                            '--install-scripts', str(Path(directory)/'scripts'), '--no-compile'],
                           cwd=source, env=env, stdout=output, stderr=subprocess.STDOUT,
                           timeout=90, check=True)
            subprocess.run([sys.executable, '-c', 'import matlab.engine; print(matlab.engine.__file__)'],
                           cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT, timeout=30, check=True)
        except (subprocess.SubprocessError, OSError) as exc:
            print(f'Engine configuration did not pass: {exc}. See {log}')
            return 1
    print('MATLAB Engine configured. Restart PHM to refresh its status.')
    return 0


if __name__ == '__main__':
    sys.exit(configure())

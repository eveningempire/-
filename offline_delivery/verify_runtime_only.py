from pathlib import Path
import os
import re
import subprocess
import zipfile

os.environ['PYTHONIOENCODING'] = 'utf-8'
archive = Path('E:/phm_platform_offline_runtime_20261010.zip')
destination = Path('E:/PHM offline QA 20261010')
root = destination / 'phm_platform_offline'
assert not destination.exists(), 'Verification directory already exists'
print('Extracting runtime-only package...', flush=True)
with zipfile.ZipFile(archive) as zipped:
    zipped.extractall(destination)
assert not (root / '.venv').exists()
assert not list(root.rglob('*.md'))
assert not list(root.rglob('*.docx'))
index = (root / 'frontend/dist/index.html').read_text(encoding='utf-8')
for asset in re.findall(r'(?:src|href)="(/static/[^\"]+)"', index):
    assert (root / 'frontend/dist' / asset.removeprefix('/static/')).is_file(), asset
environment = os.environ.copy()
environment['USE_SQLITE'] = 'true'
environment['DJANGO_DEBUG'] = 'True'
environment['PIP_NO_INDEX'] = '1'
environment['PIP_DISABLE_PIP_VERSION_CHECK'] = '1'
with (destination / 'verification.log').open('wb') as log:
    print('Creating a fresh .venv using local wheels...', flush=True)
    subprocess.run(['C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
                    '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                    str(root / 'setup_migration.ps1'), '-SkipFrontend'],
                   cwd=root, env=environment, stdout=log, stderr=subprocess.STDOUT, check=True)
    for arguments in [['-m', 'pip', 'check'], ['manage.py', 'check'],
                      ['manage.py', 'migrate', '--noinput']]:
        subprocess.run([str(root / '.venv/Scripts/python.exe'), *arguments],
                       cwd=root, env=environment, stdout=log,
                       stderr=subprocess.STDOUT, check=True)
print('Fresh offline initialization, dependency check, Django check, migration and assets: OK', flush=True)

"""Build a fresh offline ZIP with a consistent database/media snapshot."""
import hashlib
import json
import sqlite3
import time
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parent / 'phm_platform_offline'
target = Path('E:/phm_platform_offline_complete_verified_20261010.zip')
excluded_dirs = {'.venv', '__pycache__', '.git', 'node_modules', 'docs', '交付文档', 'logs', 'slprj'}
notes = {'HIER14_PYYAML_FIX_README.txt', 'OFFLINE_DELIVERY_STATUS.txt', 'MIGRATION_QUICKSTART.txt',
         '_debug_setup.ps1', '_fn.ps1', 'runtime.json', 'build_offline_bundle.ps1', 'vite.config.js'}
root_files = {'db.sqlite3', 'manage.py', 'create_superuser.py', 'create_superuser.bat',
              'requirements-migration.txt', 'start_phm_platform.bat', 'start_phm_platform.ps1',
              'stop_phm_platform.bat', 'uninstall_phm_platform.bat', 'setup_migration.ps1',
              'verify_phm_runtime.py', 'verify_phm_delivery.py', 'check_phm_status.bat'}


def excluded(relative):
    parts = relative.parts
    if any(part in excluded_dirs or part.startswith('.venv-backup-') for part in parts):
        return True
    if relative.suffix.lower() in {'.md', '.doc', '.docx', '.pdf', '.ppt', '.pptx', '.pyc', '.log', '.bak'}:
        return True
    if relative.name in notes:
        return True
    if len(parts) == 1 and relative.name not in root_files:
        return True
    if parts[0] == 'frontend' and (len(parts) < 2 or parts[1] != 'dist'):
        return True
    if parts[0] in {'delete', 'database-source', 'runtime-installers'}:
        return True
    if parts[0] == 'config' and relative.name == 'matlab_runtime.json':
        return True
    if parts[0] == 'media' and relative.suffix.lower() == '.zip':
        return True
    return False


paths = sorted(path for path in root.rglob('*') if path.is_file() and not excluded(path.relative_to(root)))
with sqlite3.connect(root / 'db.sqlite3') as database:
    datasets = [filename for (filename,) in database.execute('SELECT file FROM datasets_dataset') if filename]
names = {path.relative_to(root).as_posix() for path in paths}
assert all('media/' + filename in names for filename in datasets)
started = time.monotonic()
with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as archive:
    for index, path in enumerate(paths):
        relative = path.relative_to(root).as_posix()
        compression = zipfile.ZIP_STORED if path.suffix.lower() in {'.zip', '.whl', '.png', '.jpg', '.jpeg', '.mp4', '.exe'} else zipfile.ZIP_DEFLATED
        archive.write(path, 'phm_platform_offline/' + relative, compress_type=compression)
        if index % 1000 == 0:
            print(f'Packed {index}/{len(paths)} files ({time.monotonic()-started:.0f}s)', flush=True)
print('Checking ZIP CRC...', flush=True)
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    assert not any('/.venv/' in name or Path(name).suffix.lower() in {'.md', '.docx', '.doc'} for name in archive.namelist())
checksum = hashlib.sha256()
with target.open('rb') as stream:
    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
        checksum.update(block)
report = {'zip': str(target), 'bytes': target.stat().st_size, 'files': len(paths), 'datasets': len(datasets), 'sha256': checksum.hexdigest()}
Path(__file__).with_name('complete_package_manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report), flush=True)

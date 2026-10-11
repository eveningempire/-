"""Update delivery labels without recompressing the unchanged runtime/data."""
from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parent / 'phm_platform_offline'
source = Path('E:/phm_platform_offline_final_20261010.zip')
target = Path('E:/phm_platform_offline_final_20261010_phm.zip')
prefix = 'phm_platform_offline/'
changed = [
    'start_phm_platform.bat', 'stop_phm_platform.bat', 'check_phm_status.bat',
    'README_最终交付说明.md', '项目使用说明.md', 'frontend/vite.config.js',
    'install_hier14_yaml.bat', 'HIER14_PYYAML_FIX_README.txt',
    'OFFLINE_DELIVERY_STATUS.txt', 'setup_migration_runtime_only.ps1',
    'setup_migration_runtime_only.bat',
]
removed = ['start_cmg_platform.bat', 'stop_cmg_platform.bat',
           'check_cmg_status.bat', 'vite.config.js', '_debug_setup.ps1', '_fn.ps1']
shutil.copyfile(source, target)
print('Copied verified archive.', flush=True)
with zipfile.ZipFile(target, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
    excluded = {prefix + name for name in changed + removed}
    archive.filelist[:] = [entry for entry in archive.filelist
                         if entry.filename not in excluded]
    archive.NameToInfo = {entry.filename: entry for entry in archive.filelist}
    for name in changed:
        archive.write(root / name, prefix + name)
with zipfile.ZipFile(target) as archive:
    names = set(archive.namelist())
    assert all(prefix + name in names for name in changed)
    assert all(prefix + name not in names for name in removed)
    for name in changed:
        assert archive.read(prefix + name) == (root / name).read_bytes(), name
    for name in ['runtime/python310/python.exe',
                 'frontend/dist/assets/index-d32ec3a9.js', 'db.sqlite3']:
        assert prefix + name in names
    assert 'start_phm_platform.bat' in archive.read(
        prefix + 'README_最终交付说明.md').decode('utf-8-sig')
print(f'Updated and checked: {target} ({target.stat().st_size} bytes)', flush=True)

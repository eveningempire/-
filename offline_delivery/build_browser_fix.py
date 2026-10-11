from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parent / 'phm_platform_offline'
patch = Path('E:/phm_browser_start_fix_20261010.zip')
full = Path('E:/phm_platform_offline_runtime_20261010_browserfix.zip')
changes = ['start_phm_platform.bat', 'start_phm_platform.ps1']
with zipfile.ZipFile(patch, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
    for name in changes:
        zipped.write(root / name, name)
shutil.copyfile('E:/phm_platform_offline_runtime_20261010_startfix.zip', full)
with zipfile.ZipFile(full, 'a', compression=zipfile.ZIP_DEFLATED) as zipped:
    updated = {'phm_platform_offline/' + name for name in changes}
    zipped.filelist[:] = [item for item in zipped.filelist if item.filename not in updated]
    zipped.NameToInfo = {item.filename: item for item in zipped.filelist}
    for name in changes:
        zipped.write(root / name, 'phm_platform_offline/' + name)
for package, prefix in [(patch, ''), (full, 'phm_platform_offline/')]:
    with zipfile.ZipFile(package) as zipped:
        assert len(zipped.namelist()) == len(set(zipped.namelist()))
        for name in changes:
            assert zipped.read(prefix + name) == (root / name).read_bytes()
        assert zipped.testzip() is None
    print(f'Checked: {package}; {package.stat().st_size} bytes', flush=True)

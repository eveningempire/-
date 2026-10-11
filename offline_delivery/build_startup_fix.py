from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parent / 'phm_platform_offline'
source = Path('E:/phm_platform_offline_runtime_20261010.zip')
full = Path('E:/phm_platform_offline_runtime_20261010_startfix.zip')
patch = Path('E:/phm_offline_start_fix_20261010.zip')
changes = ['start_phm_platform.bat', 'start_phm_platform.ps1',
           'verify_phm_runtime.py', 'setup_migration.ps1']
frontend = Path(__file__).resolve().parent.parent / 'frontend/dist_rebuilt3'
files = [(root / name, name) for name in changes]
files += [(p, 'frontend/dist/' + p.relative_to(frontend).as_posix())
          for p in frontend.rglob('*')
          if p.is_file() and p.suffix.lower() not in {'.md', '.doc', '.docx', '.pdf'}]
with zipfile.ZipFile(patch, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
    for path, name in files:
        archive.write(path, name)
print('Patch created:', patch, patch.stat().st_size, flush=True)
shutil.copyfile(source, full)
with zipfile.ZipFile(full, 'a', compression=zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
    names = {'phm_platform_offline/' + name for _, name in files}
    archive.filelist[:] = [entry for entry in archive.filelist if entry.filename not in names]
    archive.NameToInfo = {entry.filename: entry for entry in archive.filelist}
    for path, name in files:
        archive.write(path, 'phm_platform_offline/' + name)
for package, prefix in [(patch, ''), (full, 'phm_platform_offline/')]:
    with zipfile.ZipFile(package) as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
        for path, name in files:
            assert archive.read(prefix + name) == path.read_bytes(), name
        assert archive.testzip() is None
        if prefix:
            assert not any('/.venv/' in name for name in archive.namelist())
            assert not any(Path(name).suffix.lower() in {'.md', '.doc', '.docx'}
                           for name in archive.namelist())
    print('Verified:', package, package.stat().st_size, flush=True)

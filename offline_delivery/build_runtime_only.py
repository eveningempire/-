"""Copy compressed ZIP payloads while removing virtualenv and delivery manuals."""
import copy
import shutil
import struct
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath

source = Path('E:/phm_platform_offline_final_20261010_phm.zip')
target = Path('E:/phm_platform_offline_runtime_20261010.zip')
removed = Counter()

def normalized_name(info):
    name = info.filename
    # Windows tar wrote legacy GBK filenames without the ZIP UTF-8 flag.
    if not info.flag_bits & 0x800:
        try:
            name = name.encode('cp437').decode('gbk')
        except (UnicodeError, ValueError):
            pass
    return name

def exclusion(name):
    path = PurePosixPath(name)
    parts = path.parts
    if any(p in {'.venv', '__pycache__', '.git'} or
           p.startswith('.venv-backup-') for p in parts):
        return 'environment/cache'
    if path.suffix.lower() in {'.md', '.doc', '.docx', '.pdf', '.ppt', '.pptx'}:
        return 'manuals'
    if len(parts) > 1 and parts[1] in {'docs', '交付文档'}:
        return 'manuals'
    if len(parts) > 1 and parts[1] == 'logs' and not name.endswith('/'):
        return 'old logs'
    if path.name in {'_debug_setup.ps1', '_fn.ps1', 'HIER14_PYYAML_FIX_README.txt',
                     'OFFLINE_DELIVERY_STATUS.txt', 'MIGRATION_QUICKSTART.txt'}:
        return 'notes/debug'
    return None

with zipfile.ZipFile(source) as original, zipfile.ZipFile(target, 'w', allowZip64=True) as output:
    with source.open('rb') as data:
        for item in original.infolist():
            name = normalized_name(item)
            reason = exclusion(name)
            if reason:
                removed[reason] += 1
                continue
            # Locate the compressed payload independently of legacy filename encoding.
            data.seek(item.header_offset)
            header = data.read(30)
            assert header[:4] == b'PK\x03\x04', name
            name_length, extra_length = struct.unpack_from('<HH', header, 26)
            data.seek(name_length + extra_length, 1)
            entry = copy.copy(item)
            entry.filename = name
            entry.orig_filename = name
            entry.flag_bits &= ~(0x8 | 0x800)  # sizes are now known; writer handles UTF-8
            entry.header_offset = output.fp.tell()
            output.fp.write(entry.FileHeader(zip64=entry.file_size > zipfile.ZIP64_LIMIT
                                            or entry.compress_size > zipfile.ZIP64_LIMIT))
            remaining = item.compress_size
            while remaining:
                block = data.read(min(4 * 1024 * 1024, remaining))
                if not block:
                    raise RuntimeError(f'Truncated payload: {name}')
                output.fp.write(block)
                remaining -= len(block)
            output.filelist.append(entry)
            output.NameToInfo[name] = entry
            output.start_dir = output.fp.tell()
            output._didModify = True
with zipfile.ZipFile(target) as archive:
    names = set(archive.namelist())
    assert not any(exclusion(name) for name in names)
    for name in ['start_phm_platform.bat', 'setup_migration.ps1', 'requirements-migration.txt',
                 'runtime/python310/python.exe', 'runtime/python310/Lib/venv/__init__.py',
                 'frontend/dist/index.html', 'db.sqlite3']:
        assert 'phm_platform_offline/' + name in names, name
    print('CRC checking...', flush=True)
    assert archive.testzip() is None
print('Excluded:', dict(removed), flush=True)
print(f'Created: {target}; {target.stat().st_size:,} bytes', flush=True)

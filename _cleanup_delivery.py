from pathlib import Path
import shutil
p = Path('offline_delivery/phm_platform_offline/.venv-backup-20261010-202819')
if p.exists():
    shutil.rmtree(p)
print('cleanup complete')

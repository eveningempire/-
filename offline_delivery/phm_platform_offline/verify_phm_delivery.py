"""Check relocatable data and model assets before accepting a startup."""
import sqlite3
from pathlib import Path

root = Path(__file__).resolve().parent
database = root / 'db.sqlite3'
if not database.is_file():
    raise RuntimeError('Bundled project database is missing')
with sqlite3.connect(database) as connection:
    files = connection.execute('SELECT file FROM datasets_dataset').fetchall()
missing = [filename for (filename,) in files if filename and not (root / 'media' / filename).is_file()]
if missing:
    raise RuntimeError(f'{len(missing)} dataset files missing; first: {missing[0]}')
for relative in ('health-main/backend/algotest/hier14/checkpoints/best_model.pth',
                 'health-main/backend/algotest/hier14/checkpoints/scaler.pkl',
                 'integrations/algorithm_assets/models/life/14/ensemble.pkl',
                 'integrations/simulation_assets/simulate_data_+1.zip',
                 'media/datasets/simulate_data_+1/import_manifest.json'):
    if not (root / relative).is_file():
        raise RuntimeError('Missing algorithm/data asset: ' + relative)
print(f'PHM delivery OK: {len(files)} dataset files and inference assets')

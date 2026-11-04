"""Verify GitHub/offline assets, and report all missing files together."""
import argparse
import hashlib
import json
import os
import sqlite3
import zipfile
from pathlib import Path

from simulation_dataset.assets import simulation_archive


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify(root, assets_only=False):
    errors = []
    manifest = root / 'integrations' / 'delivery_assets.json'
    if manifest.is_file():
        for asset in json.loads(manifest.read_text(encoding='utf-8'))['assets']:
            path = root / asset['path']
            if not path.is_file():
                errors.append('Missing asset: ' + asset['path'])
            elif path.stat().st_size != asset['bytes'] or sha256(path) != asset['sha256']:
                errors.append('Damaged asset (or Git LFS pointer): ' + asset['path'])
    else:
        errors.append('Missing integrations/delivery_assets.json; download the complete main branch.')
    for relative in ('health-main/backend/algotest/hier14/checkpoints/deploy_meta.json',
                     'integrations/algorithm_assets/hier14_repo/src/models/hierarchical_tcn_transformer.py',
                     'health_assessment/p1_v3_strict/candidates.py',
                     'platform_handoff_20260911_v1/health_bundle/model_registry.json',
                     'integrations/matlab/phm_send_telemetry.m'):
        if not (root / relative).is_file():
            errors.append('Missing source/config: ' + relative)
    archive = simulation_archive(root)
    if not archive.is_file() or not zipfile.is_zipfile(archive):
        errors.append('Missing or invalid simulation archive: ' + str(archive))
    if not assets_only:
        database = root / 'db.sqlite3'
        if not database.is_file():
            errors.append('Database missing; run setup_migration.ps1 first.')
        else:
            try:
                with sqlite3.connect(database) as connection:
                    files = connection.execute('SELECT file FROM datasets_dataset').fetchall()
                for (filename,) in files:
                    if filename and not (root / 'media' / filename).is_file():
                        errors.append('Dataset file missing: media/' + filename)
            except sqlite3.Error as exc:
                errors.append('Database not initialized; run manage.py migrate: ' + str(exc))
        if not errors:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')
            import django
            django.setup()
            from fault_diagnosis.service import DiagnosisService
            from platform_health.service import HealthAssessmentService
            for name, service in (('Hier14', DiagnosisService.instance()),
                                  ('Health assessment', HealthAssessmentService.instance())):
                if not service.available:
                    errors.append(name + ' failed to load: ' + str(service.error))
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets-only', action='store_true', help='Check binaries without installing Django or creating a database')
    args = parser.parse_args()
    errors = verify(Path(__file__).resolve().parent, args.assets_only)
    if errors:
        print('PHM delivery verification FAILED:')
        for error in errors:
            print(' - ' + error)
        return 1
    print('PHM delivery OK: verified trained models, Simulink assets and real simulation data')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

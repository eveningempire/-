"""Run real packaged inference on isolated database and media."""
import json
import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
os.environ['USE_SQLITE'] = 'true'
os.environ['DJANGO_SETTINGS_MODULE'] = 'phm_backend.settings'
import django
from django.conf import settings

temporary = tempfile.TemporaryDirectory(prefix='phm-functional-')
database = Path(temporary.name) / 'qa.sqlite3'
with sqlite3.connect(root / 'db.sqlite3') as source, sqlite3.connect(database) as target:
    source.backup(target)
settings.DATABASES['default']['NAME'] = str(database)
django.setup()
import torch
torch.set_num_threads(2)
from django.contrib.auth import get_user_model
from django.test import Client
from datasets.models import Dataset
from simulation_demo.models import FaultWorkflowTask

client = Client()
client.force_login(get_user_model().objects.filter(is_superuser=True).first())
report = {'checks': [], 'failures': []}


def call(label, path, body=None):
    started = time.monotonic()
    try:
        response = client.get(path) if body is None else client.post(path, json.dumps(body), content_type='application/json')
        result = response.json()
        if response.status_code >= 400 or isinstance(result, dict) and (result.get('ok') is False or result.get('status') == 'error'):
            raise RuntimeError(str(result)[:1000])
        json.dumps(result, allow_nan=False)
        if path.endswith('/status/'):
            assert result.get('available', True), str(result)
        if label.startswith('diagnosis') and path.endswith('/predict/'):
            value = result['result']
            assert value.get('window_series'), 'no diagnosis windows'
        if label.startswith('health') and path.endswith('/evaluate/'):
            assert result['result'].get('hi_sequence'), 'no health curve'
        if label.startswith('rul') and path.endswith('/predict/'):
            assert result.get('ensemble_rul'), 'no trained RUL curve'
        entry = {'check': label, 'seconds': round(time.monotonic()-started, 2), 'http': response.status_code}
        report['checks'].append(entry)
        print(json.dumps(entry), flush=True)
        return result
    except Exception as exc:
        report['failures'].append({'check': label, 'error': str(exc)})
        print('FAIL ' + label + ': ' + str(exc), flush=True)


missing = [item.file.name for item in Dataset.objects.all() if item.file and not Path(item.file.path).is_file()]
assert not missing, f'{len(missing)} datasets missing: {missing[:5]}'
print(f'All {Dataset.objects.count()} dataset records have files', flush=True)
report['dataset_count'] = Dataset.objects.count()
manifest = json.loads((Path(settings.MEDIA_ROOT) / 'datasets/simulate_data_+1/import_manifest.json').read_text(encoding='utf-8'))['files']
normal_entry = next(item for item in manifest if item['member'] == 'simulate_data_+1/baseline/fc0.csv')
fault_entry = next(item for item in manifest if item['member'] == 'simulate_data_+1/bengqixi/fc0_t30.csv')
normal, fault = normal_entry['dataset_id'], fault_entry['dataset_id']
for module in ('fault-diagnosis', 'health-assessment', 'rul'):
    call(module+' status', f'/api/v1/{module}/status/')
call('datasets list', '/api/v1/datasets/')
catalog = call('simulation catalog', '/api/v1/simulation-demo/sample/')
assert catalog and catalog['archive']['available']
for algorithm in ('hier14', 'msfg_teams_rt', 'pca_iforest'):
    for name, identifier in [('normal', normal), ('fault', fault)]:
        call(f'diagnosis {algorithm} {name}', '/api/v1/fault-diagnosis/predict/', {'dataset_id': identifier, 'algorithm': algorithm})
for algorithm in ('cdpca_ga', 'ae_gmm'):
    call('health '+algorithm, '/api/v1/health-assessment/evaluate/', {'dataset_id': fault, 'algorithm': algorithm})
system_ids = list(Dataset.objects.filter(system='动力', component='原始状态量').values_list('pk', flat=True)[:2])
assert system_ids, 'No propulsion datasets available for system health'
call('health system', '/api/v1/health-assessment/evaluate/', {'dataset_ids': system_ids, 'algorithm': 'gcn_rbd'})
call('rul trained fault', '/api/v1/rul/predict/', {'dataset_id': fault, 'algorithm': 'health_main_ensemble', 'component_id': '14'})
batch = call('batch trained rul', '/api/v1/rul/predict/', {'dataset_ids': [normal, fault], 'component_id': '14'})
if batch:
    assert batch['success'] == 2, str(batch)[:1000]
batch = call('batch diagnosis', '/api/v1/fault-diagnosis/batch-predict/', {'dataset_ids': [normal, fault], 'algorithm': 'hier14'})
created = call('archive create', '/api/v1/simulation-demo/workflows/', {'mode': 'offline', 'subsystem': '动力', 'fault_mode': '泵气蚀', 'injection_time': 30, 'end_time': 480, 'flight_count': 0})
if created:
    identifier = created['task']['id']
    from simulation_demo.worker import execute_task
    from django.test import override_settings
    with override_settings(MEDIA_ROOT=Path(temporary.name) / 'media'):
        FaultWorkflowTask.objects.filter(pk=identifier).update(status='queued')
        assert execute_task(identifier)
        task = FaultWorkflowTask.objects.get(pk=identifier)
        call('archive detail', f'/api/v1/simulation-demo/workflows/{identifier}/')
        call('diagnosis imported data', '/api/v1/fault-diagnosis/predict/', {'dataset_id': task.dataset_id, 'algorithm': 'hier14'})
        call('rul imported data', '/api/v1/rul/predict/', {'dataset_id': task.dataset_id, 'component_id': '14'})

target = Path(__file__).with_name('complete_delivery_qa.json')
target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print('QA REPORT: ' + str(target), flush=True)
from django.db import connections
connections.close_all()
temporary.cleanup()
sys.exit(bool(report['failures']))

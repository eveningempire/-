"""Exercise shipped trained models with unchanged real simulation samples."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'phm_backend.settings')

import django
django.setup()

import torch
from django.test import Client
from datasets.models import Dataset
from fault_diagnosis.service import DiagnosisService
from platform_health.service import HealthAssessmentService
from rul_service.inputs import prepare
from rul_service.health_main_adapter import predict


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
    torch.set_num_threads(2)
    client = Client()
    for url in ('/', '/api/v1/fault-diagnosis/status/', '/api/v1/health-assessment/status/',
                '/api/v1/rul/status/', '/api/v1/simulation-dataset/catalog/'):
        response = client.get(url)
        assert response.status_code == 200, (url, response.status_code)
        if url != '/':
            body = response.json()
            if 'available' in body:
                assert body['available'], (url, body)
            print(url, json.dumps(body, ensure_ascii=True)[:300])
    raw = Dataset.objects.filter(file='datasets/baseline/fc0.csv').get()
    diagnosis = DiagnosisService.instance().predict(raw.file.path)
    assert diagnosis['n_windows'] > 0 and len(diagnosis['class_probs']) == 14
    print('Hier14 actual inference OK:', diagnosis['n_windows'], 'windows')
    bundle = Path(__file__).resolve().parent / 'platform_handoff_20260911_v1/health_bundle'
    evidence = json.loads((bundle / 'examples/input_smoke.jsonl').read_text(encoding='utf-8').splitlines()[0])
    assessment = HealthAssessmentService.instance().require().process_record(evidence)
    assert 'component_hi' in assessment, assessment
    print('Health assessment actual inference OK:', assessment['component_hi'])
    derived = Dataset.objects.filter(file='datasets/baseline/fc0_P.csv').get()
    asset_dir = Path(__file__).resolve().parent / 'integrations/algorithm_assets/models/life/14'
    prepared = prepare(derived, '14', asset_dir)
    result = predict(derived.file.path, asset_dir, prepared=prepared)
    assert len(result['ensemble_rul']['RF']) > 0
    assert result['rul_value'] >= 0
    print('RUL trained ensemble actual inference OK:', len(result['ensemble_rul']['RF']), 'predictions')
    print('GITHUB_INFERENCE_PASS')


if __name__ == '__main__':
    main()

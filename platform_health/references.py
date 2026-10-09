"""Resolve normal trajectories using registered simulation provenance only."""
import json
from pathlib import Path

from django.conf import settings

from datasets.models import Dataset
from datasets.services import read_rows


def assessment_reference(dataset):
    from simulation_demo.models import FaultWorkflowTask

    manifest = Path(settings.MEDIA_ROOT) / 'datasets/simulate_data_+1/import_manifest.json'
    if manifest.is_file():
        entries = json.loads(manifest.read_text(encoding='utf-8'))['files']
        entry = next((item for item in entries if item.get('dataset_id') == dataset.pk
                      and item.get('file') == dataset.file.name), None)
        if entry:
            filename = Path(entry['member']).name
            flight = filename.split('_t', 1)[0].removesuffix('_P.csv').removesuffix('.csv')
            suffix = '_P.csv' if filename.endswith('_P.csv') else '.csv'
            baseline = next((item for item in entries if item.get('category') == 'baseline'
                             and Path(item['member']).name == flight + suffix), None)
            if baseline:
                normal = Dataset.objects.filter(pk=baseline['dataset_id'], file=baseline['file']).first()
                if normal:
                    return _normal(normal, 'import_manifest_same_flight')

    tasks = FaultWorkflowTask.objects.filter(status='completed', simulation_backend='simulink')
    current = None
    current_export = None
    for task in tasks:
        export = next((item for item in task.simulation_output.get('datasets', [])
                       if item.get('dataset_id') == dataset.pk and item.get('path') == dataset.file.name), None)
        if export:
            current, current_export = task, export
            break
    if current:
        for task in tasks:
            output = task.simulation_output
            params = output.get('parameters', {})
            if (task.flight_count != current.flight_count
                    or params.get('power_fault') != '无故障' or params.get('control_fault') != '无故障'
                    or output.get('model') != current.simulation_output.get('model')
                    or output.get('source') != current.simulation_output.get('source')
                    or output.get('duration') != current.simulation_output.get('duration')):
                continue
            for export in output.get('datasets', []):
                if export.get('component') != current_export.get('component'):
                    continue
                normal = Dataset.objects.filter(pk=export.get('dataset_id'), file=export.get('path')).first()
                if normal:
                    return _normal(normal, 'registered_simulink_same_flight')
    return {'baseline_end': dataset.injection_time if dataset.source == 'simulation' else None}


def _normal(dataset, provenance):
    return {'reference_rows': read_rows(dataset.pk),
            'reference_info': {'dataset_id': dataset.pk, 'dataset_name': dataset.name,
                               'provenance': provenance}}

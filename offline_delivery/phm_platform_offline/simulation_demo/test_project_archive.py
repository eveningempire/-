import csv
import io
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from datasets.models import Dataset
from .models import FaultWorkflowTask
from .project_archive import _selections
from .worker import execute_task


class ProjectArchiveTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.override = override_settings(MEDIA_ROOT=root / 'media')
        self.override.enable()
        self.addCleanup(self.override.disable)
        archive = root / 'samples.zip'
        self.contents = {}
        with zipfile.ZipFile(archive, 'w') as bundle:
            for category, filename in [('baseline', 'fc0'), ('bengqixi', 'fc0_t30')]:
                for suffix, signal in [('', 'S1'), ('_P', 'P1')]:
                    stream = io.StringIO(newline='')
                    writer = csv.writer(stream)
                    writer.writerow(['Time', signal, 'FaultFlag'])
                    writer.writerows([[t, 1 + int(t >= 30), int(category != 'baseline' and t >= 30)] for t in [0, 29, 30, 480]])
                    member = f'simulate_data_+1/{category}/{filename}{suffix}.csv'
                    self.contents[member] = stream.getvalue().encode('utf-8')
                    bundle.writestr(member, self.contents[member])
        self.archive_patch = patch('simulation_dataset.services.ARCHIVE', archive)
        self.archive_patch.start()
        self.addCleanup(self.archive_patch.stop)
        _selections.cache_clear()
        self.client.force_login(get_user_model().objects.create_user(username='archive-admin', is_staff=True))
        self.payload = {'mode': 'offline', 'subsystem': '动力', 'fault_mode': '泵气蚀', 'flight_count': 0, 'injection_time': 30, 'end_time': 480}

    def create(self, **extra):
        return self.client.post('/api/v1/simulation-demo/workflows/', json.dumps({**self.payload, **extra}), content_type='application/json')

    @patch('simulation_demo.views.runtime_status', side_effect=AssertionError('must not check MATLAB'))
    @patch('simulation_demo.worker.subprocess.Popen')
    def test_import_preserves_bytes_pairing_and_runs_without_matlab(self, launch, runtime):
        response = self.create()
        self.assertEqual(response.status_code, 201)
        identifier = response.json()['task']['id']
        generated = self.client.post(f'/api/v1/simulation-demo/workflows/{identifier}/generate/')
        self.assertEqual(generated.status_code, 202)
        self.assertTrue(execute_task(identifier))
        self.assertFalse(execute_task(identifier))
        task = FaultWorkflowTask.objects.get(pk=identifier)
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.simulation_backend, 'project_archive')
        self.assertEqual(Dataset.objects.count(), 2)
        for item in task.simulation_output['datasets']:
            self.assertEqual(Path(Dataset.objects.get(pk=item['dataset_id']).file.path).read_bytes(), self.contents[item['archive_member']])
            self.assertEqual(item['recorded_fault_range'], [30., 480.])
        launch.assert_called_once()

    def test_missing_combination_or_changed_timing_cannot_relabel_data(self):
        for extra in [{'injection_time': 40}, {'end_time': 100}, {'flight_count': 1}, {'flight_count': True}, {'mode': 'realtime', 'simulation_backend': 'project_archive'}]:
            self.assertEqual(self.create(**extra).status_code, 400)
        self.assertEqual(FaultWorkflowTask.objects.count(), 0)

    def test_valid_baseline_has_no_fault_rows(self):
        identifier = self.create(fault_mode='无故障', injection_time=0).json()['task']['id']
        FaultWorkflowTask.objects.filter(pk=identifier).update(status='queued')
        self.assertTrue(execute_task(identifier))
        task = FaultWorkflowTask.objects.get(pk=identifier)
        self.assertTrue(all(item['fault_row_count'] == 0 for item in task.simulation_output['datasets']))

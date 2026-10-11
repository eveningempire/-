import io
import json
import tempfile
import zipfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from datasets.batch_processing import inspect_file
from datasets.models import Dataset
from fault_diagnosis.route_algorithms import _read_numeric, msfg_teams_rt, pca_iforest
from fault_diagnosis.service import DiagnosisService
from phm.fault_replay import _ensure_dataset_events
from phm.models import FaultEvent, TelemetrySample
from platform_health.algorithms import _matrix


def simulation_csv(count=120):
    # Only the truth label changes: an algorithm must not infer a fault from it.
    return 'Time,P1,P2,FaultFlag\n' + ''.join(
        f'{index * .25},1.0,2.0,{int(index >= count // 2)}\n' for index in range(count)
    )


class SimulationColumnTests(SimpleTestCase):
    def test_timestamp_and_truth_label_are_excluded_from_models(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fc0_t15_P.csv'
            path.write_text(simulation_csv(), encoding='utf-8')
            report = inspect_file(path)
            self.assertEqual(report['time_column'], 'Time')
            self.assertEqual(report['fault_flag_column'], 'FaultFlag')
            self.assertEqual(report['numeric_parameter_columns'], ['P1', 'P2'])
            self.assertEqual(report['fault_label_summary']['first_fault_time'], 15.0)
            self.assertEqual(report['fault_label_summary']['counts'], {'0': 60, '1': 60})
            rows, signals = _read_numeric(path)
            self.assertEqual(list(signals), ['P1', 'P2'])
            for algorithm in (msfg_teams_rt, pca_iforest):
                result = algorithm(path)
                self.assertEqual(result['aggregate_pred_name'], '正常')
                self.assertEqual(result['window_series'][-1]['time_end'], 29.75)
                self.assertEqual({item['signal'] for item in result['evidence']}, {'P1', 'P2'})
            service = object.__new__(DiagnosisService)
            service.predictor, service.error = None, 'test unavailable'
            with self.assertRaisesRegex(RuntimeError, 'test unavailable'):
                service.predict(path)
            matrix, keys, times = _matrix(rows)
            self.assertEqual(keys, ['P1', 'P2'])
            self.assertEqual(matrix.shape, (120, 2))
            self.assertEqual(times[-1], 29.75)

    def test_quality_reports_invalid_label_and_backwards_time(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.csv'
            path.write_text('TIME,P1,Fault_Flag\n2,1,0\n1,1,2\n', encoding='utf-8')
            report = inspect_file(path)
        self.assertEqual(report['time_column'], 'TIME')
        self.assertEqual(report['fault_flag_column'], 'Fault_Flag')
        self.assertEqual(report['quality_status'], 'warning')
        self.assertEqual(report['time_summary']['non_increasing_count'], 1)
        self.assertEqual(report['fault_label_summary']['invalid_count'], 1)


class SimulationImportTests(TestCase):
    def test_import_preserves_bytes_metadata_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            archive = Path(folder) / 'source.zip'
            content = simulation_csv()
            with zipfile.ZipFile(archive, 'w') as stream:
                stream.writestr('simulate_data_+1/bengqixi/fc3_t15_P.csv', content)
            report_path = Path(folder) / 'manifest.json'
            for _ in range(2):
                call_command('import_simulation_datasets', archive=archive, report=report_path, stdout=io.StringIO())
            self.assertEqual(Dataset.objects.count(), 1)
            dataset = Dataset.objects.get()
            self.assertEqual(dataset.injection_time, 15)
            self.assertEqual(dataset.launch_number, 3)
            self.assertEqual(dataset.fault_type, '泵气蚀')
            self.assertEqual(Path(dataset.file.path).read_text(encoding='utf-8'), content)
            entry = json.loads(report_path.read_text(encoding='utf-8'))['files'][0]
            self.assertEqual(entry['parameter_columns'], ['P1', 'P2'])
            self.assertEqual(entry['dataset_id'], dataset.pk)
            Path(dataset.file.path).write_text('changed', encoding='utf-8')
            with self.assertRaises(CommandError):
                call_command('import_simulation_datasets', archive=archive, stdout=io.StringIO())
            self.assertEqual(Path(dataset.file.path).read_text(), 'changed')

    def test_file_replay_keeps_truth_boundary_without_copying_samples(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            get_user_model().objects.create_user(username='csv-replay')
            dataset = Dataset.objects.create(name='故障 CSV', fault_type='泵气蚀', injection_time=300)
            dataset.file.save('fault.csv', ContentFile(simulation_csv(2400).encode()))
            self.assertEqual(_ensure_dataset_events(), 1)
            self.assertEqual(_ensure_dataset_events(), 0)
            self.assertEqual(TelemetrySample.objects.count(), 0)
            event = FaultEvent.objects.get()
            detail = self.client.get(f'/api/v1/phm/fault-events/{event.pk}/').json()['curve']
            self.assertEqual(detail['count'], 2400)
            self.assertLess(detail['display_count'], 2400)
            self.assertEqual(detail['parameter_columns'], ['P1', 'P2'])
            self.assertNotIn('FaultFlag', detail['series'])
            self.assertIn({'time': 300.0, 'P1': 1.0, 'P2': 2.0, 'FaultFlag': 1.0}, detail['rows'])
            created = self.client.post(f'/api/v1/phm/fault-events/{event.pk}/replays/', json.dumps({'start': 299.5, 'end': 300.5, 'speed': 2}), content_type='application/json')
            self.assertEqual(created.status_code, 201)
            self.assertEqual(created.json()['curve']['count'], 5)

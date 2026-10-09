import csv
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase, override_settings

from datasets.models import Dataset
from .models import FaultWorkflowTask
from .simulink import _load_core, fault_catalog
from .worker import execute_task


def fake_engine():
    engine = Mock()
    times = [[0.0], [39.0], [40.0], [100.0], [101.0], [480.0]]
    signals = {}
    for name in ['Xe', 'Ve', 'FT', 'Angle'] + [f'S{i}' for i in range(1, 18)] + [f'P{i}' for i in range(1, 18)]:
        width = 3 if name in ('Xe', 'Ve', 'Angle', 'S10') else 1
        signals[name] = {'time': times, 'signals': {'values': [[float(i + column + 1) for column in range(width)] for i in range(len(times))]}}
    engine.getfield.side_effect = lambda result, name: signals[name]
    return engine, signals


class CustomerCoreTests(SimpleTestCase):
    def test_every_customer_fault_uses_exact_block_and_step_mapping(self):
        core = _load_core()
        with tempfile.TemporaryDirectory() as directory:
            for subsystem, faults in fault_catalog().items():
                for fault in faults:
                    with self.subTest(subsystem=subsystem, fault=fault):
                        engine, _ = fake_engine()
                        stages = []
                        scope, derived, _ = core.run_simulation(
                            str(Path(directory) / 'rocket_sim.slx'), str(Path(directory) / 'scope.csv'),
                            power_fault=fault if subsystem == '动力' else '无故障',
                            control_fault=fault if subsystem == '控制' else '无故障',
                            start_time=40, end_time=100, flight_count=3, eng=engine,
                            close_engine=True, on_stage=stages.append,
                        )
                        engine.sim.assert_called_once_with('rocket_sim', nargout=1)
                        engine.set_param.assert_any_call('rocket_sim/Th', 'Value', '1440', nargout=0)
                        engine.set_param.assert_any_call('rocket_sim', 'StopTime', '480', nargout=0)
                        for block in core.FAULT_MAP.values():
                            engine.set_param.assert_any_call(block, 'Value', '1', nargout=0)
                        if fault != '无故障':
                            engine.set_param.assert_any_call(core.FAULT_MAP[fault], 'Value', '0', nargout=0)
                            engine.set_param.assert_any_call(core.STEP1_MAP[fault], 'Time', '40', nargout=0)
                            engine.set_param.assert_any_call(core.STEP2_MAP[fault], 'Time', '100', nargout=0)
                        engine.quit.assert_called_once()
                        self.assertEqual(stages, ['starting_engine', 'configuring', 'solving', 'exporting'])
                        for filename, header in ((scope, core.SCOPE_CSV_HEADER), (derived, core.P_CSV_HEADER)):
                            with open(filename, encoding='utf-8', newline='') as stream:
                                reader = csv.DictReader(stream)
                                self.assertEqual(reader.fieldnames, header)
                                rows = list(reader)
                            self.assertEqual(len(rows), 6)
                            self.assertEqual([int(row['FaultFlag']) for row in rows], [0, 0, 1, 1, 0, 0] if fault != '无故障' else [0]*6)

    def test_reset_failure_aborts_solver_and_closes_engine(self):
        core = _load_core()
        engine, _ = fake_engine()
        engine.set_param.side_effect = RuntimeError('missing block')
        with self.assertRaisesRegex(RuntimeError, 'missing block'):
            core.run_simulation('rocket_sim.slx', 'unused.csv', eng=engine, close_engine=True)
        engine.sim.assert_not_called()
        engine.quit.assert_called_once()

    def test_compatibility_load_setting_is_restored(self):
        core = _load_core()
        engine, _ = fake_engine()
        engine.get_param.return_value = 'on'
        with tempfile.TemporaryDirectory() as directory:
            core.run_simulation('rocket_sim.slx', str(Path(directory)/'scope.csv'), eng=engine,
                                allow_newer_model=True, close_engine=True)
        engine.set_param.assert_any_call(0.0, 'ErrorIfLoadNewModel', 'off', nargout=0)
        engine.set_param.assert_any_call(0.0, 'ErrorIfLoadNewModel', 'on', nargout=0)

    def test_mismatched_signal_grid_is_rejected(self):
        core = _load_core()
        engine, signals = fake_engine()
        signals['P1']['time'] = [[999.0]]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, '时间轴不一致'):
                core.run_simulation('rocket_sim.slx', str(Path(directory)/'scope.csv'), eng=engine, close_engine=True)
            self.assertFalse((Path(directory)/'scope.csv').exists())


class SimulinkWorkflowTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.override = override_settings(MEDIA_ROOT=Path(self.directory.name))
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.admin = get_user_model().objects.create_user(username='sim-admin', is_staff=True)
        self.client.force_login(self.admin)
        self.payload = {'mode': 'realtime', 'subsystem': '动力', 'fault_mode': '泵气蚀',
                        'injection_time': 40, 'end_time': 100, 'flight_count': 0}

    def create_task(self, **extra):
        return self.client.post('/api/v1/simulation-demo/workflows/',
                                data=json.dumps({**self.payload, **extra}), content_type='application/json')

    def test_catalog_includes_13_faults_and_baselines_without_generated_samples(self):
        data = self.client.get('/api/v1/simulation-demo/sample/').json()
        self.assertEqual(sum(len(faults)-1 for faults in data['subsystems'].values()), 13)
        self.assertNotIn('data', data)
        self.assertTrue(data['can_submit'])

    def test_invalid_parameters_create_no_task(self):
        for extra in ({'fault_mode': '泄漏'}, {'subsystem': '电源'}, {'injection_time': -1},
                      {'injection_time': 100}, {'end_time': 481}, {'end_time': float('nan')},
                      {'flight_count': 0.5}, {'flight_count': 21}, {'flight_count': True},
                      {'severity': 0.5}, {'mode': 'bad'}):
            with self.subTest(extra=extra):
                self.assertEqual(self.create_task(**extra).status_code, 400)
        self.assertEqual(FaultWorkflowTask.objects.count(), 0)

    @patch('simulation_demo.views.runtime_status', return_value={'available': False, 'error': 'Engine missing'})
    @patch('simulation_demo.worker.subprocess.Popen')
    def test_missing_runtime_produces_no_fake_dataset(self, launch, runtime):
        task_id = self.create_task().json()['task']['id']
        response = self.client.post(f'/api/v1/simulation-demo/workflows/{task_id}/generate/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['task']['current_stage'], 'runtime_unavailable')
        self.assertEqual(Dataset.objects.count(), 0)
        launch.assert_not_called()

    @patch('simulation_demo.views.runtime_status', return_value={'available': True})
    @patch('simulation_demo.worker.subprocess.Popen')
    def test_launch_is_idempotent_and_rejects_browser_generated_samples(self, launch, runtime):
        task_id = self.create_task().json()['task']['id']
        url = f'/api/v1/simulation-demo/workflows/{task_id}/generate/'
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 202)
        self.assertEqual(self.client.post(url).status_code, 202)
        launch.assert_called_once()
        self.assertIn('run_simulink_task', launch.call_args.args[0])
        self.assertEqual(self.client.post(f'/api/v1/simulation-demo/workflows/{task_id}/samples/').status_code, 409)

    @patch('simulation_demo.views.runtime_status', return_value={'available': True})
    @patch('simulation_demo.worker.subprocess.Popen', side_effect=OSError('launch failed'))
    def test_launch_failure_is_persisted_and_retryable(self, launch, runtime):
        task_id = self.create_task().json()['task']['id']
        response = self.client.post(f'/api/v1/simulation-demo/workflows/{task_id}/generate/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['task']['status'], 'failed')
        self.assertEqual(response.json()['task']['latest_result']['error'], 'launch failed')

    def test_worker_exports_and_registers_both_datasets_once(self):
        task_id = self.create_task(subsystem='控制', fault_mode='陀螺仪卡死', flight_count=3).json()['task']['id']
        FaultWorkflowTask.objects.filter(pk=task_id).update(status='queued')
        core = _load_core()
        engine, _ = fake_engine()
        original = core.run_simulation
        call = Mock(side_effect=lambda *args, **kwargs: original(*args, eng=engine, **kwargs))
        core.run_simulation = call
        with patch('simulation_demo.simulink._load_core', return_value=core):
            self.assertTrue(execute_task(task_id))
            self.assertFalse(execute_task(task_id))
        self.assertEqual(call.call_args.kwargs['control_fault'], '陀螺仪卡死')
        self.assertEqual(call.call_args.kwargs['power_fault'], '无故障')
        self.assertEqual(call.call_args.kwargs['start_time'], 40)
        self.assertEqual(call.call_args.kwargs['end_time'], 100)
        task = FaultWorkflowTask.objects.get(pk=task_id)
        self.assertEqual(task.status, 'completed')
        self.assertEqual(Dataset.objects.count(), 2)
        datasets = task.simulation_output['datasets']
        self.assertEqual([len(item['parameter_columns']) for item in datasets], [29, 17])
        for item in datasets:
            self.assertNotIn('Time', item['parameter_columns'])
            self.assertNotIn('FaultFlag', item['parameter_columns'])
            self.assertEqual(item['row_count'], 6)
            dataset = Dataset.objects.get(pk=item['dataset_id'])
            self.assertIsNone(dataset.degradation)
            self.assertTrue(Path(dataset.file.path).is_file())

    @patch('simulation_demo.worker.run_task', side_effect=RuntimeError('solver failed'))
    def test_solver_failure_is_persisted(self, run_task):
        task_id = self.create_task().json()['task']['id']
        FaultWorkflowTask.objects.filter(pk=task_id).update(status='queued')
        with self.assertRaisesRegex(RuntimeError, 'solver failed'):
            execute_task(task_id)
        task = FaultWorkflowTask.objects.get(pk=task_id)
        self.assertEqual(task.status, 'failed')
        self.assertEqual(task.latest_result['error'], 'solver failed')
        self.assertEqual(Dataset.objects.count(), 0)

    def test_invalid_export_registers_neither_csv(self):
        task_id = self.create_task().json()['task']['id']
        FaultWorkflowTask.objects.filter(pk=task_id).update(status='queued')
        core = _load_core()
        engine, signals = fake_engine()
        signals['P1']['signals']['values'][0][0] = float('nan')
        original = core.run_simulation
        core.run_simulation = lambda *args, **kwargs: original(*args, eng=engine, **kwargs)
        with patch('simulation_demo.simulink._load_core', return_value=core):
            with self.assertRaisesRegex(ValueError, '非有限数值'):
                execute_task(task_id)
        self.assertEqual(Dataset.objects.count(), 0)
        self.assertEqual(FaultWorkflowTask.objects.get(pk=task_id).status, 'failed')

    @patch('simulation_demo.views.runtime_status', return_value={'available': False, 'error': 'Engine missing'})
    def test_diagnosis_injection_endpoint_uses_same_customer_parameters(self, runtime):
        response = self.client.post('/api/v1/fault-diagnosis/simulate-inject/',
                                    data=json.dumps({'fault': {'subsystem': '控制', 'mode': 'TVC偏角不足',
                                                              'start': 12, 'end': 110, 'flight_count': 2}}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 503)
        task = FaultWorkflowTask.objects.get()
        self.assertEqual((task.fault_mode, task.injection_time, task.end_time, task.flight_count),
                         ('TVC偏角不足', 12, 110, 2))
        self.assertEqual(task.simulation_backend, 'simulink')

    def test_read_and_submit_permissions(self):
        self.client.logout()
        self.assertEqual(self.client.get('/api/v1/simulation-demo/sample/').status_code, 401)
        viewer = get_user_model().objects.create_user(username='sim-viewer')
        self.client.force_login(viewer)
        self.assertEqual(self.client.get('/api/v1/simulation-demo/sample/').status_code, 200)
        self.assertEqual(self.create_task().status_code, 403)

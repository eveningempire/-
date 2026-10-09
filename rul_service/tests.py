import json
import tempfile
from pathlib import Path
import joblib
import numpy as np
from django.core.files.base import ContentFile
from django.test import Client, TestCase, override_settings
from datasets.models import Dataset
from phm.models import StructureNode
from simulation_demo.models import FaultWorkflowTask
from .inputs import COMPONENT_FEATURES, prepare


class TrainedRulIntegrationTests(TestCase):
    def test_health_main_ensemble_runs_from_dataset(self):
        rows = ["HI_norm"] + [str(.98 - index * .006) for index in range(100)]
        dataset = Dataset(name="trained-rul-test", source="test")
        dataset.file.save("trained-rul-test.csv", ContentFile(("\n".join(rows) + "\n").encode()), save=True)
        response = Client().post("/api/v1/rul/predict/", data=json.dumps({"dataset_id": dataset.id, "algorithm": "health_main_ensemble", "component_id": "14"}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertFalse(body["development_only"])
        self.assertIn("BiLSTM", body["model_predictions"])
        self.assertIsInstance(body["rul_value"], float)

    def test_batch_predict_keeps_each_dataset_result(self):
        datasets = []
        for offset in (0.0, 0.1):
            rows = ["HI_norm"] + [str(.98 - offset - index * .005) for index in range(60)]
            dataset = Dataset(name=f"batch-{offset}", source="test")
            dataset.file.save(f"batch-{offset}.csv", ContentFile(("\n".join(rows) + "\n").encode()), save=True)
            datasets.append(dataset)
        response = Client().post("/api/v1/rul/predict/", data=json.dumps({"dataset_ids": [item.pk for item in datasets], "algorithm": "health_main_ensemble", "component_id": "14"}), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertEqual(body["success"], 2, body)
        self.assertEqual([item["dataset_id"] for item in body["results"]], [item.pk for item in datasets])
        self.assertEqual([item["result"]["current_hi"] for item in body["results"]], [.685, .585])


class SimulationRulInputTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.directory.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.asset_root = Path(__file__).resolve().parent.parent / 'integrations' / 'algorithm_assets' / 'models' / 'life'

    def dataset(self, name, rows):
        dataset = Dataset(name=name, source='simulation')
        dataset.file.save(name + '.csv', ContentFile(('\n'.join(rows) + '\n').encode()), save=True)
        return dataset

    def derived(self, signal='P1', flag=0):
        return self.dataset('derived', [f'Time,{signal},FaultFlag'] +
                            [f'{index / 2},{0.95 - index * .0005},{flag}' for index in range(129)])

    def register_pair(self, raw, derived):
        FaultWorkflowTask.objects.create(name='pair', mode='offline', subsystem='动力', fault_mode='无故障',
                                         simulation_backend='simulink', status='completed', dataset_id=raw.pk,
                                         simulation_output={'datasets': [
                                             {'dataset_id': raw.pk, 'path': raw.file.name, 'component': '原始状态量'},
                                             {'dataset_id': derived.pk, 'path': derived.file.name, 'component': '派生参数'},
                                         ]})

    def post(self, **payload):
        return Client().post('/api/v1/rul/predict/', data=json.dumps(payload), content_type='application/json')

    def test_derived_csv_runs_full_model_with_real_time_alignment(self):
        dataset = self.derived()
        response = self.post(dataset_id=dataset.pk, algorithm='health_main_ensemble', component_id='1')
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()
        self.assertEqual(result['hi_source']['method'], 'trained_pca')
        self.assertEqual(result['hi_source']['input_signal'], 'P1')
        self.assertEqual(result['hi_times'], list(range(1, 65)))
        self.assertEqual(result['rul_times'], list(range(51, 65)))
        self.assertEqual(len(result['ensemble_rul']['RF']), 14)
        self.assertEqual(result['unit'], 's')
        self.assertTrue(result['development_only'])
        self.assertFalse(result['threshold_used_by_model'])

    def test_training_feature_order_uses_frozen_scaler_and_pca(self):
        dataset = self.derived()
        asset_dir = self.asset_root / '1'
        prepared = prepare(dataset, '1', asset_dir)
        first_window = np.array([.95 - index * .0005 for index in range(4)])
        independent_features = [[first_window.min(), first_window.mean(),
                                 np.sqrt(np.mean(first_window ** 2)), first_window.max()]]
        scaler, pca = joblib.load(asset_dir / 'scaler.pkl'), joblib.load(asset_dir / 'pca.pkl')
        meta = json.loads((asset_dir / 'hi_meta.json').read_text())
        expected = (pca.transform(scaler.transform(independent_features)).ravel()[0] - meta['global_min']) / (
            meta['global_max'] - meta['global_min'] + 1e-8)
        self.assertAlmostEqual(prepared['values'][0], np.clip(expected, 0, 1))
        self.assertEqual(prepared['source']['feature_order'], list(COMPONENT_FEATURES[1]))

    def test_fault_labels_do_not_change_hi_features(self):
        normal = self.derived(flag=0)
        fault = self.derived(flag=1)
        left = prepare(normal, '1', self.asset_root / '1')
        right = prepare(fault, '1', self.asset_root / '1')
        self.assertEqual(left['values'], right['values'])
        self.assertEqual(left['times'], right['times'])

    def test_registered_raw_and_derived_have_identical_hi(self):
        derived = self.derived()
        raw = self.dataset('raw', ['Time,S1,FaultFlag'] + [f'{index / 2},12345,1' for index in range(129)])
        self.register_pair(raw, derived)
        left = prepare(raw, '1', self.asset_root / '1')
        right = prepare(derived, '1', self.asset_root / '1')
        self.assertEqual(left['values'], right['values'])
        self.assertTrue(left['source']['paired_dataset'])
        self.assertEqual(left['source']['source_dataset_id'], derived.pk)

    def test_pair_with_different_time_axis_is_rejected(self):
        derived = self.derived()
        raw = self.dataset('raw', ['Time,S1'] + [f'{index / 2 + .1},1' for index in range(129)])
        self.register_pair(raw, derived)
        response = self.post(dataset_id=raw.pk, algorithm='health_main_ensemble', component_id='1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('时间轴不一致', response.json()['message'])

    def test_paired_source_pbs_must_match_selected_model(self):
        derived = self.derived()
        raw = self.dataset('raw', ['Time,S1'] + [f'{index / 2},1' for index in range(129)])
        self.register_pair(raw, derived)
        expected = StructureNode.objects.create(node_key='rul-pump', pbs_code='rul-pump', name='液氧泵')
        conflicting = StructureNode.objects.create(node_key='rul-rudder', pbs_code='rul-rudder', name='栅格舵')
        derived.structure_node = conflicting
        derived.save(update_fields=['structure_node'])
        for raw_node in (None, expected):
            raw.structure_node = raw_node
            raw.save(update_fields=['structure_node'])
            for algorithm in ('health_main_ensemble', 'hi_linear'):
                with self.subTest(raw_node=raw_node, algorithm=algorithm):
                    response = self.post(dataset_id=raw.pk, algorithm=algorithm, component_id='1')
                    self.assertEqual(response.status_code, 400)
                    self.assertIn('配套派生数据集已关联 PBS 部件', response.json()['message'])
        derived.structure_node = expected
        derived.save(update_fields=['structure_node'])
        response = self.post(dataset_id=raw.pk, algorithm='hi_linear', component_id='1')
        self.assertEqual(response.status_code, 200, response.content)

    def test_unregistered_raw_is_not_guessed_from_name(self):
        self.derived()
        raw = self.dataset('raw', ['Time,S1'] + [f'{index / 2},1' for index in range(129)])
        response = self.post(dataset_id=raw.pk, algorithm='health_main_ensemble', component_id='1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('同次仿真', response.json()['message'])

    def test_short_time_span_fails_even_with_many_rows(self):
        dataset = self.dataset('short', ['Time,P1'] + [f'{index / 100},.9' for index in range(1000)])
        response = self.post(dataset_id=dataset.pk, algorithm='health_main_ensemble', component_id='1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('51 个 HI 窗口', response.json()['message'])

    def test_special_signal_reversal_and_domain_clipping_are_recorded(self):
        dataset = self.derived(signal='P5')
        prepared = prepare(dataset, '5', self.asset_root / '5')
        self.assertTrue(prepared['source']['reversed'])
        self.assertEqual(prepared['source']['feature_order'], ['rms', 'mean', 'max', 'min'])
        extreme = self.dataset('extreme', ['Time,P1'] + [f'{index / 2},1000' for index in range(129)])
        result = prepare(extreme, '1', self.asset_root / '1')
        self.assertEqual(result['source']['clipped_fraction'], 1.0)
        self.assertTrue(all(0 <= value <= 1 for value in result['values']))

    def test_provided_hi_alias_is_kept_and_invalid_hi_is_rejected(self):
        valid = self.dataset('health', ['Time,health'] + [f'{index},.9' for index in range(60)])
        response = self.post(dataset_id=valid.pk, algorithm='health_main_ensemble', component_id='1')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['hi_source']['method'], 'provided_hi')
        invalid = self.dataset('bad-hi', ['HI_norm', '1.1', '.9', '.8'])
        response = self.post(dataset_id=invalid.pk, algorithm='hi_linear', component_id='1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('0 到 1', response.json()['message'])

    def test_linear_trend_uses_seconds_and_batch_preserves_failures(self):
        valid = self.dataset('health', ['Time,HI_norm', '10,.9', '12,.8', '14,.7'])
        response = self.post(dataset_id=valid.pk, algorithm='hi_linear', component_id='1', threshold=.2)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['unit'], 's')
        self.assertAlmostEqual(response.json()['rul_value'], 10.0)
        invalid = self.dataset('bad', ['Time,P2', '1,.9', '2,.8'])
        response = self.post(dataset_ids=[valid.pk, invalid.pk], algorithm='hi_linear', component_id='1')
        self.assertEqual(response.json()['success'], 1)
        self.assertEqual(response.json()['failed'], 1)

    def test_model_selection_must_include_required_parameter(self):
        response = self.post(dataset_id=self.derived().pk, algorithm='health_main_ensemble', component_id='10')
        self.assertEqual(response.status_code, 400)
        self.assertIn('P9', response.json()['message'])

    def test_invalid_thresholds_are_rejected_before_inference(self):
        dataset = self.derived()
        for threshold in (float('nan'), float('inf'), 0, 1):
            with self.subTest(threshold=threshold):
                response = self.post(dataset_id=dataset.pk, algorithm='health_main_ensemble',
                                     component_id='1', threshold=threshold)
                self.assertEqual(response.status_code, 400)
                self.assertIn('有限数值', response.json()['message'])

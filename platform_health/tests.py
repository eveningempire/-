import json
import tempfile
from unittest.mock import patch

import numpy as np
from django.core.files.base import ContentFile
from django.test import Client, SimpleTestCase, TestCase
from sklearn.decomposition import PCA

from datasets.models import Dataset
from .service import HealthAssessmentService
from .algorithms import ae_gmm, cdpca_ga, gcn_rbd


class HealthDirectionTests(SimpleTestCase):
    def trajectories(self, sign=1):
        normal = [{'Time': i, 'pressure': 1 + .01 * np.sin(i),
                   'temperature': .4 + .001 * np.cos(i), 'FaultFlag': 0}
                  for i in range(160)]
        faulty = [dict(row, pressure=row['pressure'] + (sign * .8 if 60 <= i < 110 else 0),
                       FaultFlag=int(60 <= i < 110)) for i, row in enumerate(normal)]
        return normal, faulty

    def test_both_directions_of_deviation_reduce_health_and_recovery_is_allowed(self):
        for method in (cdpca_ga, ae_gmm):
            for sign in (-1, 1):
                with self.subTest(method=method.__name__, sign=sign):
                    normal, faulty = self.trajectories(sign)
                    result = method(faulty, reference_rows=normal)
                    hi = np.array(result['hi_sequence'])
                    self.assertGreater(hi[:50].mean(), .95)
                    self.assertLess(hi[85:105].mean(), .5)
                    self.assertGreater(hi[-15:].mean(), .95)

    def test_pca_sign_does_not_change_health(self):
        normal, faulty = self.trajectories()
        expected = cdpca_ga(faulty, reference_rows=normal)
        transform = PCA.transform

        def reversed_transform(pca, values):
            signs = np.ones(pca.n_components_)
            signs[::2] = -1
            return transform(pca, values) * signs

        with patch.object(PCA, 'transform', reversed_transform):
            actual = cdpca_ga(faulty, reference_rows=normal)
        np.testing.assert_allclose(actual['hi_sequence'], expected['hi_sequence'])

    def test_fault_labels_do_not_change_inference(self):
        normal, faulty = self.trajectories()
        altered = [dict(row, FaultFlag=9-i) for i, row in enumerate(faulty)]
        for method in (cdpca_ga, ae_gmm):
            with self.subTest(method=method.__name__):
                expected = method(faulty, reference_rows=normal)
                actual = method(altered, reference_rows=normal)
                self.assertEqual(expected['hi_sequence'], actual['hi_sequence'])
                self.assertNotIn('FaultFlag', actual['signals'])

    def test_constant_and_short_records_have_finite_healthy_values(self):
        for size in (1, 3, 40):
            for method in (cdpca_ga, ae_gmm):
                with self.subTest(size=size, method=method.__name__):
                    result = method([{'Time': i, 'pressure': 1} for i in range(size)])
                    np.testing.assert_allclose(result['hi_sequence'], np.ones(size), atol=1e-5)
                    json.dumps(result, allow_nan=False)

    def test_prefix_reference_ends_before_known_injection(self):
        rows = [{'Time': i, 'pressure': 1 if i < 5 else 2} for i in range(50)]
        result = cdpca_ga(rows, baseline_end=5)
        self.assertEqual(result['reference']['sample_count'], 5)
        self.assertEqual(result['reference']['time_range'], [0, 4])
        self.assertGreater(result['hi_sequence'][0], .95)
        self.assertLess(result['hi_sequence'][-1], .5)
        with self.assertRaisesMessage(ValueError, '注入前没有参考样本'):
            cdpca_ga(rows, baseline_end=0)

    def test_normal_trajectory_changes_do_not_become_degradation(self):
        normal = [{'Time': i, 'pressure': 1+i*.1} for i in range(100)]
        result = cdpca_ga(normal, reference_rows=normal)
        np.testing.assert_allclose(result['hi_sequence'], np.ones(100))

    def test_system_alignment_direction_recovery_and_endpoints(self):
        components = [
            {'health_index': 1., 'time_sequence': [0, 1, 2, 3, 4], 'hi_sequence': [1, 1, 0, 1, 1]},
            {'health_index': 1., 'time_sequence': [0, 2, 4], 'hi_sequence': [1, 0, 1]},
        ]
        result = gcn_rbd(components, ['pump', 'turbine'])
        self.assertEqual(result['time_sequence'], [0, 1, 2, 3, 4])
        self.assertEqual(result['hi_sequence'][0], 1)
        self.assertEqual(result['hi_sequence'][2], 0)
        self.assertEqual(result['hi_sequence'][-1], 1)
        self.assertEqual(result['component_hi_sequences']['turbine'], [1, .5, 0, .5, 1])
        with self.assertRaisesMessage(ValueError, '没有重叠'):
            gcn_rbd([dict(components[0], time_sequence=[10, 11, 12, 13, 14]), components[1]], ['a', 'b'])

    def test_invalid_time_order_and_reference_columns_are_rejected(self):
        with self.assertRaisesMessage(ValueError, '按时间升序'):
            cdpca_ga([{'Time': 2, 'pressure': 1}, {'Time': 1, 'pressure': 1}])
        with self.assertRaisesMessage(ValueError, '参数列不一致'):
            cdpca_ga([{'Time': 0, 'pressure': 1}], reference_rows=[{'Time': 0, 'temperature': 1}])


class HealthAssessmentIntegrationTests(TestCase):
    def setUp(self):
        HealthAssessmentService._instance = None
        self.client = Client()

    def test_status_reports_loaded_real_bundle(self):
        response = self.client.get("/api/v1/health-assessment/status/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["available"], body.get("error"))
        self.assertEqual(body["input_kind"], "upstream_window_evidence")
        self.assertIn("scikit_learn", body["runtime"])

    def test_registered_model_evaluates_valid_window(self):
        payload = {
            "run_id": 9201,
            "session_id": "django-test",
            "component_id": "oxygen_turbine",
            "window_index": 0,
            "timestamp": 144.9,
            "hi_cd": 0.72,
            "hi_ae": 0.91,
            "anomaly_score": -6.0,
            "reconstruction_error": 0.0004,
            "confidence": 0.97,
        }
        response = self.client.post(
            "/api/v1/health-assessment/evaluate/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()["result"]
        self.assertEqual(result["component_id"], "oxygen_turbine")
        self.assertEqual(result["component_hi_status"], "qualified")
        self.assertIn("trace_hash", result)

    def test_invalid_raw_telemetry_is_rejected_with_schema_error(self):
        response = self.client.post(
            "/api/v1/health-assessment/evaluate/",
            data=json.dumps({"pressure": 1.0}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("E_SCHEMA_MISSING_FIELD", response.json()["error"])

    def test_paper_component_algorithms_return_health_sequences(self):
        rows = [
            {"time": i, "pressure": 1 - i * 0.01, "temperature": 0.4 + i * 0.001,
             "attitude_error": 0.01, "control_error": 0.02}
            for i in range(24)
        ]
        cd = cdpca_ga(rows)
        ae = ae_gmm(rows)
        self.assertEqual(cd["algorithm"], "CDPCA-GA")
        self.assertEqual(ae["algorithm"], "AE-GMM")
        self.assertEqual(len(cd["hi_sequence"]), len(rows))
        self.assertEqual(len(ae["hi_sequence"]), len(rows))
        self.assertTrue(0 <= cd["health_index"] <= 1)
        self.assertTrue(0 <= ae["health_index"] <= 1)

    def test_system_gcn_rbd_fuses_component_health(self):
        result = gcn_rbd(
            [{"health_index": 0.8}, {"health_index": 0.9}],
            ["pump", "turbine"],
        )
        self.assertEqual(result["algorithm"], "GCN + RBD 系统健康评估")
        self.assertAlmostEqual(result["rbd_serial_health_index"], 0.72, places=4)
        self.assertEqual(len(result["hi_sequence"]), 1)
        self.assertTrue(0 <= result["health_index"] <= 1)


class DatasetHealthAssessmentTests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        settings_override = self.settings(MEDIA_ROOT=temporary.name)
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        self.datasets = []
        for system in ('控制', '动力', '重复使用运载器'):
            dataset = Dataset(name=f'{system}-test', system=system)
            content = 'Time,pressure,temperature,FaultFlag\n' + ''.join(
                f'{i},{1-i*.01},{.4+i*.001},{int(i>=12)}\n' for i in range(24))
            dataset.file.save('health-test.csv', ContentFile(content.encode()), save=True)
            self.datasets.append(dataset)

    def post(self, endpoint, payload):
        return self.client.post(f'/api/v1/health-assessment/{endpoint}/',
                                json.dumps(payload), content_type='application/json')

    def test_batch_runs_both_single_methods_independently_and_keeps_failures(self):
        for algorithm in ('cdpca_ga', 'ae_gmm'):
            with self.subTest(algorithm=algorithm), patch('platform_health.algorithms.gcn_rbd') as fusion:
                response = self.post('batch-evaluate', {'algorithm': algorithm,
                    'dataset_ids': [self.datasets[0].pk, 999999, self.datasets[1].pk]})
                self.assertEqual(response.status_code, 200, response.content)
                body = response.json()
                self.assertEqual((body['total'], body['success'], body['failed']), (3, 2, 1))
                self.assertEqual(body['results'][1]['error'], '数据集不存在')
                fusion.assert_not_called()
                for item in (body['results'][0], body['results'][2]):
                    result = item['result']
                    self.assertEqual(result['level'], 'component')
                    self.assertEqual(len(result['hi_sequence']), 24)
                    self.assertEqual(result['signals'], ['pressure', 'temperature'])
                    self.assertTrue(0 <= result['health_index'] <= 1)

    def test_batch_validates_request_and_deduplicates_dataset_ids(self):
        invalid = [[], {}, {'dataset_ids': []}, {'dataset_ids': [True]},
                   {'dataset_ids': ['1']}, {'dataset_ids': [1]*101},
                   {'dataset_ids': [1], 'algorithm': 'gcn_rbd'}]
        for payload in invalid:
            with self.subTest(payload=payload):
                self.assertEqual(self.post('batch-evaluate', payload).status_code, 400)
        self.assertEqual(self.client.get('/api/v1/health-assessment/batch-evaluate/').status_code, 405)
        response = self.post('batch-evaluate', {'dataset_ids': [999999, 999999]})
        self.assertEqual((response.json()['total'], response.json()['failed']), (1, 1))

    def test_system_only_accepts_one_supported_system(self):
        for ids, system in (([self.datasets[2].pk], '重复使用运载器'),
                            ([self.datasets[0].pk, self.datasets[1].pk], '控制'),
                            ([self.datasets[0].pk], '动力')):
            with self.subTest(ids=ids, system=system), patch('platform_health.algorithms.cdpca_ga') as method:
                response = self.post('evaluate', {'algorithm': 'gcn_rbd', 'dataset_ids': ids, 'system': system})
                self.assertEqual(response.status_code, 400)
                method.assert_not_called()
        for dataset in self.datasets[:2]:
            with self.subTest(system=dataset.system):
                response = self.post('evaluate', {'algorithm': 'gcn_rbd', 'dataset_ids': [dataset.pk], 'system': dataset.system})
                self.assertEqual(response.status_code, 200, response.content)
                self.assertEqual(response.json()['result']['level'], 'system')

    def test_single_dataset_still_returns_component_report(self):
        response = self.post('evaluate', {'dataset_id': self.datasets[0].pk, 'algorithm': 'cdpca_ga'})
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['result']['level'], 'component')

    def test_registered_normal_reference_is_shared_by_single_batch_and_system(self):
        from pathlib import Path
        from django.conf import settings

        normal, faulty = HealthDirectionTests().trajectories()
        normal_dataset = self.datasets[1]
        fault_dataset = self.datasets[0]
        fault_dataset.system = normal_dataset.system
        for dataset, rows in ((normal_dataset, normal), (fault_dataset, faulty)):
            content = 'Time,pressure,temperature,FaultFlag\n' + ''.join(
                f"{row['Time']},{row['pressure']},{row['temperature']},{row['FaultFlag']}\n" for row in rows)
            dataset.file.save(f'trajectory-{dataset.pk}.csv', ContentFile(content.encode()), save=True)
        manifest = Path(settings.MEDIA_ROOT) / 'datasets/simulate_data_+1/import_manifest.json'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({'files': [
            {'dataset_id': normal_dataset.pk, 'file': normal_dataset.file.name,
             'member': 'simulate_data_+1/baseline/fc6.csv', 'category': 'baseline'},
            {'dataset_id': fault_dataset.pk, 'file': fault_dataset.file.name,
             'member': 'simulate_data_+1/zhufa/fc6_t60.csv', 'category': 'zhufa'},
        ]}), encoding='utf-8')
        for endpoint, payload in (
            ('evaluate', {'dataset_id': fault_dataset.pk}),
            ('batch-evaluate', {'dataset_ids': [fault_dataset.pk]}),
            ('evaluate', {'dataset_ids': [fault_dataset.pk], 'algorithm': 'gcn_rbd', 'system': '动力'}),
        ):
            response = self.post(endpoint, payload)
            self.assertEqual(response.status_code, 200, response.content)
            result = response.json()['results'][0]['result'] if endpoint == 'batch-evaluate' else response.json()['result']
            component = result['component_results'][0] if result['level'] == 'system' else result
            self.assertEqual(component['reference']['dataset_id'], normal_dataset.pk)
            self.assertEqual(component['reference']['provenance'], 'import_manifest_same_flight')
            self.assertGreater(np.mean(result['hi_sequence'][:50]), .95)
            self.assertLess(np.mean(result['hi_sequence'][85:105]), .5)

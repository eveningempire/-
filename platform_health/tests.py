import json

from django.test import Client, TestCase

from .service import HealthAssessmentService
from .algorithms import ae_gmm, cdpca_ga, gcn_rbd


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
        self.assertEqual(result["algorithm"], "GCN+RBD")
        self.assertAlmostEqual(result["rbd_serial_health_index"], 0.72, places=4)
        self.assertEqual(len(result["hi_sequence"]), 1)
        self.assertTrue(0 <= result["health_index"] <= 1)

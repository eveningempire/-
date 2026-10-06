import json
from django.test import Client, TestCase
from .models import ReleaseAssessment


class ReleaseAssessmentTests(TestCase):
    def test_operator_supplied_weights_are_normalized_and_used(self):
        response = self.client.post(
            "/api/v1/phm/release-assessments/",
            data=json.dumps({
                "subsystem_health": {"动力": .9, "电源": .6, "结构": .8},
                "subsystem_weights": {"动力": 6, "电源": 3, "结构": 1},
                "release_threshold": .5,
            }),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        assessment = response.json()["assessment"]
        self.assertEqual(assessment["subsystem_weights"], {"动力": .6, "电源": .3, "结构": .1})
        self.assertAlmostEqual(assessment["weighted_health_index"], .8)

    def setUp(self): self.client = Client()

    def test_release_when_all_constraints_pass(self):
        response = self.client.post("/api/v1/phm/release-assessments/", data=json.dumps({"vehicle_id": "RLV-01", "subsystem_health": {"动力": .94, "电源": .92, "测控": .91}, "rul_margin": .9, "release_threshold": .85}), content_type="application/json")
        self.assertEqual(response.status_code, 201, response.content); body = response.json()["assessment"]; self.assertEqual(body["decision"], "release"); self.assertGreaterEqual(body["mission_success_probability"], .85); self.assertEqual(body["algorithm_trace"]["vae_gan_status"], "evidence_only_uncalibrated"); self.assertEqual(ReleaseAssessment.objects.count(), 1)

    def test_rf_adapter_restores_training_percentage_scale(self):
        from .trained_release_adapter import predict
        result = predict(.93, .92)
        self.assertEqual(result["rf_input_scale"], "percent_0_100")
        self.assertGreater(result["rf_probability"], .9)

    def test_hold_for_weak_subsystem_and_alarm(self):
        response = self.client.post("/api/v1/phm/release-assessments/", data=json.dumps({"subsystem_health": {"动力": .9, "电源": .55}, "open_critical_alarms": 1}), content_type="application/json")
        self.assertEqual(response.status_code, 201); body = response.json()["assessment"]; self.assertEqual(body["decision"], "hold"); self.assertGreaterEqual(len(body["blockers"]), 2)

    def test_rejects_invalid_health(self):
        response = self.client.post("/api/v1/phm/release-assessments/", data=json.dumps({"subsystem_health": {"动力": 1.2, "电源": .8}}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_model_catalog_exposes_route_models(self):
        ids = {item["id"] for item in self.client.get("/api/v1/phm/model-catalog/").json()["models"]}
        self.assertIn("health-main-rul", ids); self.assertIn("vae-gan-reflight", ids)

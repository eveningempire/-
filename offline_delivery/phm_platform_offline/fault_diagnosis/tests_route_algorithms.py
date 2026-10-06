import json
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from datasets.models import Dataset


class RouteAlgorithmTests(TestCase):
    def setUp(self):
        rows = ["time,pressure,temperature,bus_voltage,battery_capacity,attitude_error,control_error"]
        for index in range(120):
            pressure = 1.0 if index < 70 else 1.0 - (index-69)*.012
            rows.append(f"{index},{pressure},0.4,1.0,1.0,0.0,0.02")
        self.dataset = Dataset(name="route-algorithm-test", source="test")
        self.dataset.file.save("route-algorithm-test.csv", ContentFile(("\n".join(rows)+"\n").encode()), save=True)
        self.client = Client()

    def run_algorithm(self, algorithm):
        return self.client.post("/api/v1/fault-diagnosis/predict/", data=json.dumps({"dataset_id": self.dataset.id, "algorithm": algorithm}), content_type="application/json")

    def test_msfg_teams_rt_reports_pressure_fault_and_matrix(self):
        response = self.run_algorithm("msfg_teams_rt")
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()["result"]
        self.assertEqual(result["algorithm"], "MSFG + TEAMS-RT")
        self.assertEqual(result["pred_name"], "推进剂供给泄漏")
        self.assertEqual(len(result["d_matrix"]["values"]), 6)

    def test_pca_iforest_returns_window_evidence(self):
        response = self.run_algorithm("pca_iforest")
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()["result"]
        self.assertEqual(result["algorithm"], "PCA–iForest")
        self.assertGreater(result["n_windows"], 3)
        self.assertTrue(result["evidence"])

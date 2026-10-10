import json
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from datasets.models import Dataset


def _p_values_csv(p1_tail: float, rows: int = 120):
    header = ["Time"] + [f"P{i}" for i in range(1, 18)] + ["FaultFlag"]
    lines = [",".join(header)]
    for index in range(rows):
        p1 = 1.0 if index < 70 else p1_tail
        vals = [str(index), str(p1)] + ["1.0"] * 16 + ["0"]
        lines.append(",".join(vals))
    return "\n".join(lines) + "\n"


class RouteAlgorithmTests(TestCase):
    def setUp(self):
        rows = ["time,pressure,temperature,bus_voltage,battery_capacity,attitude_error,control_error"]
        for index in range(120):
            pressure = 1.0 if index < 70 else 1.0 - (index-69)*.012
            rows.append(f"{index},{pressure},0.4,1.0,1.0,0.0,0.02")
        self.dataset = Dataset(name="route-algorithm-test", source="test")
        self.dataset.file.save("route-algorithm-test.csv", ContentFile(("\n".join(rows)+"\n").encode()), save=True)
        self.p_dataset = Dataset(name="route-pvalues-test", source="test", component="派生参数")
        self.p_dataset.file.save("route-pvalues-test.csv", ContentFile(_p_values_csv(0.5).encode()), save=True)
        self.client = Client()

    def run_algorithm(self, algorithm, dataset_id=None):
        dataset_id = dataset_id or self.dataset.id
        return self.client.post(
            "/api/v1/fault-diagnosis/predict/",
            data=json.dumps({"dataset_id": dataset_id, "algorithm": algorithm}),
            content_type="application/json",
        )

    def test_msfg_teams_rt_reports_yiyuan_fault_and_matrix(self):
        response = self.run_algorithm("msfg_teams_rt", self.p_dataset.id)
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()["result"]
        self.assertEqual(result["algorithm"], "MSFG + TEAMS-RT 依赖诊断")
        self.assertIn(result["pred_name"], {"泵气蚀", "涡轮转速下降", "喷管堵塞"})
        self.assertEqual(len(result["d_matrix"]["faults"]), 13)

    def test_pca_iforest_returns_window_evidence(self):
        response = self.run_algorithm("pca_iforest")
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()["result"]
        self.assertEqual(result["algorithm"], "PCA–iForest 异常检测")
        self.assertGreater(result["n_windows"], 3)
        self.assertTrue(result["evidence"])

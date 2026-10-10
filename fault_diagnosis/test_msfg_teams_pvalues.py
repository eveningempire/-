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


class MsfgTeamsPvaluesTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dataset = Dataset(name="pvalues-test", source="test", component="派生参数")
        self.dataset.file.save("pvalues-test.csv", ContentFile(_p_values_csv(0.5).encode()), save=True)

    def run_algorithm(self, dataset_id=None):
        dataset_id = dataset_id or self.dataset.id
        return self.client.post(
            "/api/v1/fault-diagnosis/predict/",
            data=json.dumps({"dataset_id": dataset_id, "algorithm": "msfg_teams_rt"}),
            content_type="application/json",
        )

    def test_p1_anomaly_reports_bengqixi(self):
        response = self.run_algorithm()
        self.assertEqual(response.status_code, 200, response.content)
        result = response.json()["result"]
        self.assertEqual(result["algorithm"], "MSFG + TEAMS-RT 依赖诊断")
        self.assertIn(result["pred_name"], {"泵气蚀", "涡轮转速下降", "喷管堵塞"})
        self.assertEqual(len(result["d_matrix"]["faults"]), 13)
        self.assertTrue(any(item["signal"] == "P1" and item["failed"] for item in result["evidence"]))

    def test_resolve_sibling_p_values(self):
        scope = Dataset(name="sim-task", source="simulation", component="原始状态量")
        scope.file.save("scope_data.csv", ContentFile(b"time,FaultFlag\n0,0\n1,0\n"), save=True)
        derived = Dataset(name="sim-task-派生参数", source="simulation", component="派生参数")
        derived.file.save("pvalues.csv", ContentFile(_p_values_csv(0.5).encode()), save=True)
        response = self.run_algorithm(dataset_id=scope.id)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertIn("pvalues", response.json()["result"]["input_csv"].lower())

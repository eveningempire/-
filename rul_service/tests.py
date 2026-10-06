import json
from django.core.files.base import ContentFile
from django.test import Client, TestCase
from datasets.models import Dataset


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

import json

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import Client, TestCase

from datasets.models import Dataset
from .plugin_registry import list_algorithms, validate_parameters


class AlgorithmPluginApiTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user("plugin_admin", password="secret", is_staff=True)
        self.viewer = get_user_model().objects.create_user("plugin_viewer", password="secret")
        self.dataset = Dataset(name="plugin-data", source="test")
        content = "time,pressure\n" + "\n".join(f"{i},1.0" for i in range(12)) + "\n"
        self.dataset.file.save("plugin-data.csv", ContentFile(content.encode()), save=True)

    def test_catalog_detail_and_plugin_execution(self):
        keys = {item["key"] for item in list_algorithms()[0]}
        self.assertIn("example_pressure", keys)
        client = Client()
        client.force_login(self.admin)
        self.assertEqual(client.get("/api/v1/integrations/algorithm-assets/algorithms/").status_code, 200)
        self.assertEqual(client.get("/api/v1/integrations/algorithm-assets/algorithms/example_pressure/").status_code, 200)
        payload = {"dataset_id": self.dataset.pk, "parameters": {"signal": "pressure", "threshold": 0.8}}
        response = client.post("/api/v1/integrations/algorithm-assets/algorithms/example_pressure/run/", json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["result"]["decision"], "normal")
        builtin = client.post("/api/v1/integrations/algorithm-assets/algorithms/msfg_teams_rt/run/", json.dumps({"dataset_id": self.dataset.pk}), content_type="application/json")
        self.assertEqual(builtin.status_code, 200, builtin.content)
        batch = client.post("/api/v1/integrations/algorithm-assets/algorithms/example_pressure/batch-run/", json.dumps({"dataset_ids": [self.dataset.pk, 999999], "parameters": payload["parameters"]}), content_type="application/json")
        self.assertEqual(batch.status_code, 200)
        self.assertEqual((batch.json()["success"], batch.json()["failed"]), (1, 1))

    def test_viewer_cannot_run_and_parameters_are_checked(self):
        client = Client()
        client.force_login(self.viewer)
        response = client.post("/api/v1/integrations/algorithm-assets/algorithms/example_pressure/run/", json.dumps({"dataset_id": self.dataset.pk}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        with self.assertRaisesMessage(ValueError, "类型"):
            validate_parameters({"threshold": {"type": "number"}}, {"threshold": "0.8"})

    def test_catalog_sets_csrf_cookie_for_browser_run(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        catalog = client.get("/api/v1/integrations/algorithm-assets/algorithms/")
        token = catalog.cookies["csrftoken"].value
        payload = {"dataset_id": self.dataset.pk, "parameters": {"signal": "pressure"}}
        response = client.post("/api/v1/integrations/algorithm-assets/algorithms/example_pressure/run/", json.dumps(payload), content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200, response.content)

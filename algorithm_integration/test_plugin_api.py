import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import Client, SimpleTestCase, TestCase

from datasets.models import Dataset
from .plugin_registry import list_algorithms, validate_parameters


class AlgorithmCatalogTests(SimpleTestCase):
    def test_diagnosis_example_is_not_registered(self):
        keys = {item['key'] for item in list_algorithms('diagnosis')[0]}
        self.assertNotIn('example_pressure', keys)
        self.assertTrue({'hier14', 'msfg_teams_rt', 'pca_iforest'}.issubset(keys))


class AlgorithmPluginApiTests(TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        settings_override = self.settings(MEDIA_ROOT=root / 'media')
        settings_override.enable()
        self.addCleanup(settings_override.disable)
        plugin_root = patch('algorithm_integration.plugin_registry.PLUGIN_ROOT', root / 'plugins')
        plugin_root.start()
        self.addCleanup(plugin_root.stop)
        plugin = root / 'plugins' / 'fixture_pressure'
        plugin.mkdir(parents=True)
        manifest = {'key': 'fixture_pressure', 'name': 'Test pressure plugin', 'category': 'diagnosis',
                    'entrypoint': 'algorithm.py:predict', 'min_rows': 8,
                    'parameters': {'signal': {'type': 'string', 'default': 'pressure'},
                                   'threshold': {'type': 'number', 'default': 0.8}}}
        (plugin / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        (plugin / 'algorithm.py').write_text(
            "import csv\n"
            "def predict(csv_path, parameters):\n"
            "    with open(csv_path, encoding='utf-8') as stream:\n"
            "        rows = list(csv.DictReader(stream))\n"
            "    value = float(rows[-1][parameters['signal']])\n"
            "    return {'pred_name': '正常' if value >= parameters['threshold'] else '异常'}\n",
            encoding='utf-8')
        self.admin = get_user_model().objects.create_user("plugin_admin", password="secret", is_staff=True)
        self.viewer = get_user_model().objects.create_user("plugin_viewer", password="secret")
        self.dataset = Dataset(name="plugin-data", source="test")
        content = "time,pressure\n" + "\n".join(f"{i},1.0" for i in range(12)) + "\n"
        self.dataset.file.save("plugin-data.csv", ContentFile(content.encode()), save=True)
        header = ["Time"] + [f"P{i}" for i in range(1, 18)] + ["FaultFlag"]
        p_rows = [",".join(header)]
        for index in range(120):
            p_rows.append(",".join([str(index), "1.0"] + ["1.0"] * 16 + ["0"]))
        self.p_dataset = Dataset(name="plugin-pvalues", source="test", component="派生参数")
        self.p_dataset.file.save("plugin-pvalues.csv", ContentFile(("\n".join(p_rows) + "\n").encode()), save=True)

    def test_catalog_detail_and_plugin_execution(self):
        keys = {item["key"] for item in list_algorithms()[0]}
        self.assertIn("fixture_pressure", keys)
        client = Client()
        client.force_login(self.admin)
        self.assertEqual(client.get("/api/v1/integrations/algorithm-assets/algorithms/").status_code, 200)
        self.assertEqual(client.get("/api/v1/integrations/algorithm-assets/algorithms/fixture_pressure/").status_code, 200)
        payload = {"dataset_id": self.dataset.pk, "parameters": {"signal": "pressure", "threshold": 0.8}}
        response = client.post("/api/v1/integrations/algorithm-assets/algorithms/fixture_pressure/run/", json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()["result"]["decision"], "normal")
        builtin = client.post("/api/v1/integrations/algorithm-assets/algorithms/msfg_teams_rt/run/", json.dumps({"dataset_id": self.p_dataset.pk}), content_type="application/json")
        self.assertEqual(builtin.status_code, 200, builtin.content)
        batch = client.post("/api/v1/integrations/algorithm-assets/algorithms/fixture_pressure/batch-run/", json.dumps({"dataset_ids": [self.dataset.pk, 999999], "parameters": payload["parameters"]}), content_type="application/json")
        self.assertEqual(batch.status_code, 200)
        self.assertEqual((batch.json()["success"], batch.json()["failed"]), (1, 1))

    def test_viewer_cannot_run_and_parameters_are_checked(self):
        client = Client()
        client.force_login(self.viewer)
        response = client.post("/api/v1/integrations/algorithm-assets/algorithms/fixture_pressure/run/", json.dumps({"dataset_id": self.dataset.pk}), content_type="application/json")
        self.assertEqual(response.status_code, 403)
        with self.assertRaisesMessage(ValueError, "类型"):
            validate_parameters({"threshold": {"type": "number"}}, {"threshold": "0.8"})

    def test_catalog_sets_csrf_cookie_for_browser_run(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        catalog = client.get("/api/v1/integrations/algorithm-assets/algorithms/")
        token = catalog.cookies["csrftoken"].value
        payload = {"dataset_id": self.dataset.pk, "parameters": {"signal": "pressure"}}
        response = client.post("/api/v1/integrations/algorithm-assets/algorithms/fixture_pressure/run/", json.dumps(payload), content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200, response.content)

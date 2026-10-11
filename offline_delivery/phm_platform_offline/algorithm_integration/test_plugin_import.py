import io
import json
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase

from datasets.models import Dataset
from . import plugin_registry


def package(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return SimpleUploadedFile("algorithm.zip", buffer.getvalue(), content_type="application/zip")


class PluginImportTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_user("import_admin", is_staff=True)
        self.viewer = get_user_model().objects.create_user("import_viewer")

    def test_admin_import_appears_in_catalog_and_duplicate_is_rejected(self):
        manifest = {"key": "sample_rul", "name": "测试寿命算法", "version": "1.0", "category": "rul", "entrypoint": "algorithm.py:predict", "parameters": {}}
        files = {"sample_rul/manifest.json": json.dumps(manifest), "sample_rul/algorithm.py": "def predict(csv_path, parameters):\n    return {'rul_value': 10, 'unit': 'h'}\n"}
        with tempfile.TemporaryDirectory() as folder, patch.object(plugin_registry, "PLUGIN_ROOT", Path(folder)):
            client = Client()
            client.force_login(self.admin)
            response = client.post("/api/v1/integrations/algorithm-assets/algorithms/import/", {"file": package(files)})
            self.assertEqual(response.status_code, 201, response.content)
            keys = {item["key"] for item in client.get("/api/v1/integrations/algorithm-assets/algorithms/").json()["results"]}
            self.assertIn("sample_rul", keys)
            dataset = Dataset(name="imported-rul-input", source="test")
            dataset.file.save("imported-rul-input.csv", ContentFile(b"hi\n0.9\n"), save=True)
            run = client.post("/api/v1/integrations/algorithm-assets/algorithms/sample_rul/run/", json.dumps({"dataset_id": dataset.pk}), content_type="application/json")
            self.assertEqual(run.status_code, 200, run.content)
            self.assertEqual(run.json()["result"]["rul_value"], 10)
            batch = client.post("/api/v1/integrations/algorithm-assets/algorithms/sample_rul/batch-run/", json.dumps({"dataset_ids": [dataset.pk]}), content_type="application/json")
            self.assertEqual(batch.status_code, 200, batch.content)
            self.assertEqual(batch.json()["results"][0]["dataset_id"], dataset.pk)
            duplicate = client.post("/api/v1/integrations/algorithm-assets/algorithms/import/", {"file": package(files)})
            self.assertEqual(duplicate.status_code, 400)

    def test_bad_package_and_viewer_are_rejected(self):
        files = {"../bad.py": "x = 1", "manifest.json": "{}"}
        with tempfile.TemporaryDirectory() as folder, patch.object(plugin_registry, "PLUGIN_ROOT", Path(folder)):
            client = Client()
            client.force_login(self.viewer)
            self.assertEqual(client.post("/api/v1/integrations/algorithm-assets/algorithms/import/", {"file": package(files)}).status_code, 403)
            client.force_login(self.admin)
            self.assertEqual(client.post("/api/v1/integrations/algorithm-assets/algorithms/import/", {"file": package(files)}).status_code, 400)
            self.assertFalse((Path(folder) / "bad").exists())

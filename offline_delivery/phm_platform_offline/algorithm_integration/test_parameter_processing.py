import json
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from .parameter_processing import validate


class ParameterProcessingTests(SimpleTestCase):
    def test_nested_json_is_normalized(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'parameters.json'
            path.write_text(json.dumps({'model': {'window': '32'}, 'enabled': 'true'}), encoding='utf-8')
            report = validate(path)
        self.assertEqual(report['status'], 'valid')
        self.assertEqual(report['normalized'][0]['model.window'], 32)
        self.assertIs(report['normalized'][0]['enabled'], True)

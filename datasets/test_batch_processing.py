import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from .batch_processing import inspect_file


class BatchProcessingTests(SimpleTestCase):
    def test_csv_quality_report_is_streamed_and_classified(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'propulsion_pressure.csv'
            path.write_text('time,pressure\n0,1.0\n1,0.9\n2,\n', encoding='utf-8')
            report = inspect_file(path)
        self.assertEqual(report['row_count'], 3)
        self.assertEqual(report['numeric_columns'], ['time', 'pressure'])
        self.assertEqual(report['missing_value_count'], 1)
        self.assertEqual(report['inferred_metadata']['system'], '推进系统')
        self.assertEqual(report['quality_status'], 'warning')

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase

from .assets import simulation_archive


class ArchiveSelectionTests(SimpleTestCase):
    def test_sample_archive_is_used_by_a_clean_github_download(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=True):
            root = Path(directory)
            self.assertEqual(simulation_archive(root).name, 'simulation_samples.zip')
            complete = root / 'integrations/simulation_assets/simulate_data_+1.zip'
            complete.parent.mkdir(parents=True)
            complete.touch()
            self.assertEqual(simulation_archive(root), complete)

    def test_explicit_site_archive_is_never_silently_replaced(self):
        with patch.dict(os.environ, {'HEALTH_SIMULATION_ARCHIVE': '/site/missing.zip'}):
            self.assertEqual(simulation_archive(Path('.')), Path('/site/missing.zip'))

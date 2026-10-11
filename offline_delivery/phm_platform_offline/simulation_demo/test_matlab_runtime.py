import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from .matlab_runtime import engine_status, release_at, save_root


class MatlabRuntimeTests(SimpleTestCase):
    def test_release_comes_from_installation_and_not_developer_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'VersionInfo.xml').write_text('<release>R2012b</release>', encoding='utf-8')
            self.assertEqual(release_at(root), 'R2012b')
            with patch('simulation_demo.matlab_runtime.installations', return_value=[{'root': str(root), 'release': 'R2012b'}]), patch('simulation_demo.matlab_runtime.read_config', return_value={}), patch('simulation_demo.matlab_runtime.importlib.import_module', side_effect=ImportError('missing')), patch.dict('os.environ', {'PHM_MATLAB_ROOT': ''}):
                status = engine_status()
                self.assertEqual(status['matlab_release'], 'R2012b')
                self.assertTrue(any('R2023a' in message for message in status['problems']))

    def test_invalid_installation_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesMessage(ValueError, 'bin/matlab.exe'):
                save_root(directory)

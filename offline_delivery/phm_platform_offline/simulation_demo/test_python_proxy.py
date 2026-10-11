import io
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from datasets.models import Dataset
from .models import FaultWorkflowTask
from .python_proxy import run_task


class PythonProxyTests(TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root = Path(self.directory.name)
        self.media_root = root / "media"
        self.override = override_settings(MEDIA_ROOT=self.media_root)
        self.override.enable()
        self.addCleanup(self.override.disable)
        archive = root / "samples.zip"
        scope = pd.DataFrame({"Time": [0, 30, 40, 70, 100, 480], "X": [1, 1, 1, 1, 1, 1],
                              "FT": [10, 10, 10, 10, 10, 10]})
        derived = pd.DataFrame({"Time": scope.Time, "P1": [2, 2, 2, 2, 2, 2]})
        with zipfile.ZipFile(archive, "w") as bundle:
            for name, frame in (("fc0.csv", scope), ("fc0_P.csv", derived)):
                stream = io.StringIO()
                frame.to_csv(stream, index=False)
                bundle.writestr(f"simulate_data_+1/baseline/{name}", stream.getvalue())
        self.archive = patch("simulation_dataset.services.ARCHIVE", archive)
        self.archive.start()
        self.addCleanup(self.archive.stop)

    def test_proxy_generates_two_outputs_without_matlab(self):
        task = FaultWorkflowTask.objects.create(
            name="代理测试", mode="offline", subsystem="动力", fault_mode="泵气蚀",
            injection_time=40, end_time=100, flight_count=0, severity=0.5,
            simulation_backend="python_proxy", status="queued", current_stage="queued")
        self.assertIsNotNone(run_task(task))
        task.refresh_from_db()
        self.assertEqual(task.status, "completed")
        self.assertEqual(task.simulation_output["backend"], "python_proxy")
        self.assertEqual(Dataset.objects.count(), 2)
        output = pd.read_csv(self.media_root / "simulink_runs" / str(task.id) / "scope_data.csv")
        self.assertEqual(output.FaultFlag.tolist(), [0, 0, 1, 1, 1, 0])
        self.assertNotEqual(output.loc[3, "FT"], 10)

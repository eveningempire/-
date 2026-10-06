import io
import tempfile
import zipfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase, override_settings

from .management.commands.import_baseline_datasets import FLIGHTS, ROOT
from .models import Dataset


class BaselineImportTests(TestCase):
    def test_import_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder, override_settings(MEDIA_ROOT=folder):
            archive_path = Path(folder) / "baselines.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                for flight in FLIGHTS:
                    for suffix in ("", "_P"):
                        name = f"fc{flight}{suffix}.csv"
                        rows = "Time,Signal,FaultFlag\n" + "".join(f"{i},1.0,0\n" for i in range(8))
                        archive.writestr(ROOT + name, rows)
            call_command("import_baseline_datasets", archive=archive_path, stdout=io.StringIO())
            self.assertEqual(Dataset.objects.filter(fault_type="正常基线").count(), 14)
            call_command("import_baseline_datasets", archive=archive_path, stdout=io.StringIO())
            self.assertEqual(Dataset.objects.filter(fault_type="正常基线").count(), 14)

"""Import the fault/degradation CSVs from the customer simulation archive.

The archive is kept as the source of truth by ``simulation_dataset``.  This
command publishes the CSV members into the normal Dataset table as well, so
they can be selected by diagnosis, training and fault replay screens.
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datasets.models import Dataset
from datasets.batch_processing import inspect_file
from datasets.management.commands.import_baseline_datasets import _sha256
from simulation_dataset.services import ROOT, NAME_RE, CATEGORY_NAMES


def _inspect(path: Path, category: str) -> dict:
    report = inspect_file(path)
    if not report['time_column'] or not report['fault_flag_column']:
        raise CommandError(f"{path.name}: 缺少时间列或 FaultFlag 列")
    if report['row_count'] < 8 or report['quality_status'] != 'valid':
        raise CommandError(f"{path.name}: 数据为空、缺失、非数值、时间不递增或故障标签无效")
    counts = report['fault_label_summary']['counts']
    if category == 'baseline' and counts.get('1', 0):
        raise CommandError(f"{path.name}: 正常基线包含故障标签")
    if category != 'baseline' and not counts.get('1', 0):
        raise CommandError(f"{path.name}: 故障场景没有 FaultFlag=1 的样本")
    return report


class Command(BaseCommand):
    help = "导入甲方仿真压缩包中的故障/退化 CSV（正常基线已由 import_baseline_datasets 导入）。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--archive",
            type=Path,
            default=settings.BASE_DIR / "integrations" / "simulation_assets" / "simulate_data_+1.zip",
        )
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--include-baseline", action="store_true", help="校验并复用已登记的正常基线")
        parser.add_argument("--report", type=Path, help="保存逐文件校验结果和数据集 ID 的 JSON 报告")

    def handle(self, *args, **options):
        archive_path: Path = options["archive"]
        if not archive_path.is_file():
            raise CommandError(f"找不到仿真压缩包: {archive_path}")

        imported = skipped = 0
        records = []
        media_root = Path(settings.MEDIA_ROOT)
        if options['include_baseline']:
            call_command('import_baseline_datasets', archive=archive_path, dry_run=options['dry_run'], stdout=self.stdout)
        with zipfile.ZipFile(archive_path) as archive:
            members = []
            for info in archive.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".csv"):
                    continue
                parts = info.filename.split("/")
                if len(parts) != 3 or parts[0] != ROOT.rstrip("/"):
                    continue
                category, filename = parts[1], parts[2]
                match = NAME_RE.match(filename)
                if not match or category not in CATEGORY_NAMES or (category == "baseline" and not options["include_baseline"]):
                    continue
                members.append((info, category, filename, match))

            if not members:
                raise CommandError("压缩包中没有可导入的仿真 CSV")

            for info, category, filename, match in members:
                relative = f"datasets/baseline/{filename}" if category == 'baseline' else f"datasets/simulate_data_+1/{category}/{filename}"
                existing = Dataset.objects.filter(file=relative).first()
                if options["dry_run"]:
                    self.stdout.write(f"待导入: {relative}")
                    continue

                target = media_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                partial = target.with_name(target.stem + ".partial.csv")
                try:
                    if existing and not target.is_file():
                        raise CommandError(f"已登记数据集 #{existing.pk} 的文件缺失: {target}")
                    if target.exists():
                        with target.open('rb') as local, archive.open(info) as source:
                            digest = _sha256(local)
                            if digest != _sha256(source):
                                raise CommandError(f"目标文件与源压缩包不一致，停止覆盖: {target}")
                        report = _inspect(target, category)
                    else:
                        with archive.open(info) as source, partial.open("wb") as output:
                            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                                output.write(chunk)
                        report = _inspect(partial, category)
                        with partial.open('rb') as stream:
                            digest = _sha256(stream)
                        partial.replace(target)
                    # Filename tN is the authoritative scenario setting; the
                    # first FaultFlag=1 is retained as a consistency fallback.
                    injection_time = int(match.group("time")) if match.group("time") else report['fault_label_summary']['first_fault_time']
                    label = CATEGORY_NAMES[category]
                    processed = bool(match.group("processed"))
                    if existing:
                        dataset = existing
                        skipped += 1
                    else:
                        with transaction.atomic():
                            dataset = Dataset.objects.create(
                                name=f"{label} {filename}",
                                file=relative,
                                source="simulation",
                                fault_type=label,
                                injection_time=injection_time,
                                launch_number=int(match.group("flight")),
                                system="重复使用运载器",
                                component="派生参数" if processed else "原始状态量",
                            )
                        imported += 1
                    record = {key: report[key] for key in ('row_count', 'columns', 'time_column', 'fault_flag_column', 'parameter_columns', 'time_summary', 'fault_label_summary', 'quality_status')}
                    records.append({**record, 'dataset_id': dataset.pk, 'category': category, 'member': info.filename, 'file': relative, 'sha256': digest, 'injection_time': injection_time})
                    if len(records) % 25 == 0 or len(records) == len(members):
                        self.stdout.write(f"已校验 {len(records)}/{len(members)}: #{dataset.pk} {relative}")
                finally:
                    if partial.exists():
                        partial.unlink()

        if options['report'] and not options['dry_run']:
            report_path = options['report']
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with archive_path.open('rb') as stream:
                archive_digest = _sha256(stream)
            report_path.write_text(json.dumps({'archive': str(archive_path.resolve()), 'archive_sha256': archive_digest, 'files': records}, ensure_ascii=False, indent=2), encoding='utf-8')
            self.stdout.write(f"校验报告: {report_path.resolve()}")
        self.stdout.write(self.style.SUCCESS(f"完成: 新增 {imported} 个，跳过 {skipped} 个"))

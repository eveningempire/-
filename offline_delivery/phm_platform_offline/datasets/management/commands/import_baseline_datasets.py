"""Import the verified normal simulation baseline into the active database."""
from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from datasets.models import Dataset


FLIGHTS = (0, 1, 2, 3, 4, 6, 9)
ROOT = "simulate_data_+1/baseline/"


def _verify_member(archive: zipfile.ZipFile, member: str) -> int:
    """Validate every row before publishing the file as a normal baseline."""
    with archive.open(member) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="utf-8-sig", newline=""))
        if not reader.fieldnames or "FaultFlag" not in reader.fieldnames:
            raise CommandError(f"{member}: 缺少 FaultFlag 列")
        count = 0
        for row in reader:
            count += 1
            if row.get("FaultFlag") not in ("0", "0.0"):
                raise CommandError(f"{member}: 第 {count} 行故障标志非 0")
            if None in row or any(value is None or not value.strip() for value in row.values()):
                raise CommandError(f"{member}: 第 {count} 行有缺失字段")
        if count < 8:
            raise CommandError(f"{member}: 样本不足 8 行")
        return count


def _sha256(stream) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


class Command(BaseCommand):
    help = "将内置正常基线的 7 组原始及派生 CSV 导入当前数据库；重复执行不会重复创建。"

    def add_arguments(self, parser):
        parser.add_argument("--archive", type=Path, default=settings.BASE_DIR / "integrations" / "simulation_assets" / "simulate_data_+1.zip")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        archive_path = options["archive"]
        if not archive_path.is_file():
            raise CommandError(f"找不到正常基线压缩包: {archive_path}")
        media_root = Path(settings.MEDIA_ROOT)
        target_root = media_root / "datasets" / "baseline"
        imported = skipped = 0
        with zipfile.ZipFile(archive_path) as archive:
            for flight in FLIGHTS:
                for processed in (False, True):
                    filename = f"fc{flight}{'_P' if processed else ''}.csv"
                    member = ROOT + filename
                    try:
                        archive.getinfo(member)
                    except KeyError as exc:
                        raise CommandError(f"压缩包缺少 {member}") from exc
                    relative = f"datasets/baseline/{filename}"
                    target = target_root / filename
                    existing = Dataset.objects.filter(file=relative).first()
                    if existing:
                        if not existing.file or not Path(existing.file.path).is_file():
                            raise CommandError(f"数据集 #{existing.pk} 已登记但文件缺失: {relative}")
                        with Path(existing.file.path).open("rb") as local, archive.open(member) as source:
                            if _sha256(local) != _sha256(source):
                                raise CommandError(f"数据集 #{existing.pk} 的文件与基线压缩包不一致: {relative}")
                        skipped += 1
                        self.stdout.write(f"跳过已有 #{existing.pk}: {filename}")
                        continue
                    count = _verify_member(archive, member)
                    if options["dry_run"]:
                        self.stdout.write(f"待导入 {filename}: {count} 行")
                        continue
                    target_root.mkdir(parents=True, exist_ok=True)
                    # Reuse an interrupted copy only when its bytes match the archive.
                    if target.exists():
                        with target.open("rb") as local, archive.open(member) as source:
                            if _sha256(local) != _sha256(source):
                                raise CommandError(f"目标文件与压缩包不同，停止覆盖: {target}")
                    else:
                        partial = target.with_suffix(".csv.partial")
                        try:
                            with archive.open(member) as source, partial.open("wb") as output:
                                for chunk in iter(lambda: source.read(1024 * 1024), b""):
                                    output.write(chunk)
                            partial.replace(target)
                        finally:
                            if partial.exists():
                                partial.unlink()
                    with transaction.atomic():
                        dataset = Dataset.objects.create(
                            name=f"正常基线 fc{flight}{' 派生参数' if processed else ''}",
                            file=relative,
                            source="simulation",
                            fault_type="正常基线",
                            launch_number=flight,
                            system="重复使用运载器",
                            component="派生参数" if processed else "原始状态量",
                        )
                    imported += 1
                    self.stdout.write(f"导入 #{dataset.pk}: {filename}, {count} 行")
        self.stdout.write(self.style.SUCCESS(f"完成: 新增 {imported} 个，跳过 {skipped} 个"))

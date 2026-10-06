"""Install a trusted algorithm package uploaded by a platform administrator."""
from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from . import plugin_registry


MAX_ARCHIVE_BYTES = 200 * 1024 * 1024
MAX_EXPANDED_BYTES = 500 * 1024 * 1024
MAX_MEMBERS = 200
ALLOWED_SUFFIXES = {".json", ".py", ".pt", ".pth", ".pkl", ".joblib", ".npz", ".npy", ".csv", ".txt", ".yaml", ".yml"}


def install(uploaded) -> dict:
    """Validate and install one ZIP containing manifest.json and an adapter.

    Existing keys are never overwritten. ZIP extraction is confined to a
    temporary directory under the plugin root; invalid packages leave no
    discoverable plugin behind.
    """
    if not uploaded.name.lower().endswith(".zip"):
        raise ValueError("请上传 ZIP 算法包")
    if uploaded.size > MAX_ARCHIVE_BYTES:
        raise ValueError("算法包超过 200 MB")
    root = plugin_registry.PLUGIN_ROOT
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise ValueError("插件目录不能是符号链接")
    with tempfile.TemporaryDirectory(prefix="_upload_", dir=root) as temporary:
        workspace = Path(temporary)
        archive_path = workspace / "package.zip"
        with archive_path.open("wb") as output:
            for chunk in uploaded.chunks():
                output.write(chunk)
                if output.tell() > MAX_ARCHIVE_BYTES:
                    raise ValueError("算法包超过 200 MB")
        with zipfile.ZipFile(archive_path) as archive:
            members = [info for info in archive.infolist() if not info.is_dir()]
            if not members or len(members) > MAX_MEMBERS:
                raise ValueError("算法包文件数必须在 1 到 200 之间")
            if sum(info.file_size for info in members) > MAX_EXPANDED_BYTES:
                raise ValueError("解压后算法包超过 500 MB")
            paths = []
            for info in members:
                name = info.filename.replace("\\", "/")
                relative = PurePosixPath(name)
                mode = (info.external_attr >> 16) & 0o170000
                if (not name or name.startswith("/") or ":" in name or
                    any(part in {"", ".", "..", "__pycache__"} for part in relative.parts) or
                    relative.suffix.lower() not in ALLOWED_SUFFIXES or
                    mode not in (0, 0o100000)):
                    raise ValueError(f"算法包包含不允许的路径或文件: {name}")
                paths.append(relative)
            if len(set(paths)) != len(paths):
                raise ValueError("算法包包含重复路径")
            lowered = [str(path).lower() for path in paths]
            if len(set(lowered)) != len(lowered):
                raise ValueError("算法包包含仅大小写不同的重复路径")
            # Accept either a flat ZIP or one wrapper folder named after key.
            manifest_paths = [path for path in paths if path.name == "manifest.json"]
            if len(manifest_paths) != 1 or len(manifest_paths[0].parts) not in (1, 2):
                raise ValueError("算法包必须包含根目录 manifest.json")
            prefix = manifest_paths[0].parts[:-1]
            if any(path.parts[:len(prefix)] != prefix for path in paths):
                raise ValueError("算法包文件必须位于同一算法目录")
            if any(len(path.parts) <= len(prefix) for path in paths):
                raise ValueError("算法包包含空文件路径")
            manifest_data = json.loads(archive.read(str(manifest_paths[0])).decode("utf-8-sig"))
            key = manifest_data.get("key") if isinstance(manifest_data, dict) else None
            if not isinstance(key, str) or not plugin_registry.KEY_RE.fullmatch(key) or key in plugin_registry.BUILTINS:
                raise ValueError("算法 key 无效或与内置算法冲突")
            if prefix and prefix[0] != key:
                raise ValueError("ZIP 顶层目录必须与算法 key 一致")
            destination = root / key
            if destination.exists() or destination.is_symlink():
                raise ValueError(f"算法 {key} 已存在；请使用新的 key 或版本目录")
            staging = workspace / key
            staging.mkdir()
            for info, path in zip(members, paths):
                inside = Path(*path.parts[len(prefix):])
                target = staging / inside
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as source, target.open("wb") as output:
                    copied = 0
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        copied += len(chunk)
                        if copied > info.file_size or copied > MAX_EXPANDED_BYTES:
                            raise ValueError(f"算法包内文件大小异常: {path}")
                        output.write(chunk)
            record = plugin_registry._validate_manifest(staging, manifest_data)
            # Importing an entry module can execute code, so validation here
            # checks structure only. The first test run exercises the adapter.
            staging.rename(destination)
            return plugin_registry.public_record(plugin_registry._validate_manifest(destination, manifest_data))

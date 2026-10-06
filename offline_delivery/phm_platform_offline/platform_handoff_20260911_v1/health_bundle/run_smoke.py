"""Python fallback for SMOKE_TEST.ps1: runs the three bundle smokes."""
import subprocess, sys
cmds = [
    [sys.executable, "-m", "platform_adapter.cli", "--bundle", ".", "--smoke"],
    [sys.executable, "-m", "platform_adapter.cli", "--bundle", ".", "--input", "examples/input_smoke.jsonl"],
    [sys.executable, "-m", "platform_adapter.cli", "--bundle", ".", "--replace-drill"],
]
for cmd in cmds:
    result = subprocess.run(cmd, cwd=__import__('pathlib').Path(__file__).parent)
    if result.returncode != 0:
        sys.exit(result.returncode)
print('BUNDLE_SMOKE_ALL_PASS')

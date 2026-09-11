from __future__ import annotations
import os, subprocess
from pathlib import Path

class MatlabBridge:
    """Execute a configured MATLAB batch script for simulation/injection."""
    def __init__(self):
        self.executable = os.environ.get('MATLAB_EXECUTABLE', 'matlab')
        self.script = os.environ.get('MATLAB_SIM_SCRIPT', '')
    @property
    def configured(self):
        return bool(self.script and Path(self.script).exists())
    def run(self, output_dir, fault=None):
        if not self.configured:
            raise RuntimeError('未配置 MATLAB_SIM_SCRIPT，无法执行 MATLAB 仿真')
        cmd = [self.executable, '-batch', f"run('{self.script}')"]
        env = os.environ.copy(); env['PHM_FAULT_JSON'] = __import__('json').dumps(fault or {}, ensure_ascii=False); env['PHM_OUTPUT_DIR'] = str(output_dir)
        return subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=600, check=True)

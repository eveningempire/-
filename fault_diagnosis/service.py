from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from threading import Lock

from django.conf import settings


class DiagnosisService:
    _instance = None
    _lock = Lock()

    def __init__(self):
        self.root = Path(os.environ.get("HEALTH_MAIN_DIR", settings.BASE_DIR.parent.parent / "health-main"))
        self.repo = Path(os.environ.get("HIER14_REPO", settings.BASE_DIR / "integrations" / "algorithm_assets" / "hier14_repo"))
        self.predictor_path = self.root / "backend" / "algotest" / "hier14" / "predictor.py"
        self.error = None
        self.predictor = None
        self._load()

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def _load(self):
        if not self.predictor_path.exists():
            self.error = f"Hier14 预测器不存在: {self.predictor_path}"
            return
        try:
            # predictor imports the training repository's ``src`` package.
            # Put the extracted repository on sys.path before loading it.
            if self.repo.exists() and str(self.repo) not in sys.path:
                sys.path.insert(0, str(self.repo))
            # predictor.py resolves its own repository from HIER14_REPO.  Keep
            # the extracted in-project source as the default so deployments do
            # not depend on the developer's original checkout path.
            if self.repo.exists():
                os.environ.setdefault("HIER14_REPO", str(self.repo))
            spec = importlib.util.spec_from_file_location("health_main_hier14_predictor", self.predictor_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            self.predictor = module
        except Exception as exc:
            self.error = f"{type(exc).__name__}: {exc}"

    @property
    def available(self):
        return self.predictor is not None

    def predict(self, csv_path):
        if not self.predictor:
            import csv
            with open(csv_path, encoding='utf-8-sig', newline='') as f: rows=list(csv.DictReader(f))
            if not rows: raise ValueError('CSV 文件没有数据行')
            signals={}
            for k in rows[0]:
                vals=[]
                for r in rows:
                    try: vals.append(float(r[k]))
                    except (TypeError,ValueError): pass
                if vals: signals[k]=vals
            if not signals: raise ValueError('CSV 没有数值信号')
            changes=[]
            for k,v in signals.items():
                base=sum(v[:min(10,len(v))])/min(10,len(v)); changes.append((abs(v[-1]-base)/(abs(base)+1e-6),k,(v[-1]-base)/(abs(base)+1e-6)))
            _,key,drift=max(changes); conf=min(.92,.55+0.35*min(1.0,abs(drift))); label='正常' if abs(drift)<=.15 else '异常趋势'
            if 'pressure' in key.lower() and drift<-.15: label='推进系统压力下降'
            elif 'temperature' in key.lower() and drift>.15: label='热控温度升高'
            elif 'attitude' in key.lower() and abs(drift)>.15: label='姿态控制偏差'
            window_size=max(10,min(30,len(rows))); stride=max(5,window_size//2); series=[]
            for i,start in enumerate(range(0,max(1,len(rows)-window_size+1),stride)):
                end=min(len(rows),start+window_size); segment=rows[start:end]; base=sum(float(x[key]) for x in segment[:min(5,len(segment))])/min(5,len(segment)); rel=(float(segment[-1][key])-base)/(abs(base)+1e-6); wc=min(.92,.55+.35*min(1.0,abs(rel))); wl='正常' if abs(rel)<=.15 else ('推进系统压力下降' if 'pressure' in key.lower() and rel<-.15 else '异常趋势')
                series.append({'window_index':i,'time_start':segment[0].get('time',start),'time_end':segment[-1].get('time',end-1),'pred_name':wl,'confidence':round(wc,4),'evidence_signal':key,'relative_change':round(rel,4)})
            probs=[{'name':label,'prob':round(conf,4)},{'name':'正常','prob':round(1-conf,4)}]
            return {'pred_name':label,'aggregate_pred_name':label,'confidence':round(conf,4),'n_windows':len(series),'seq_len':window_size,'window_stride':stride,'sample_dt':None,'window_series':series,'class_probs':probs,'aggregate_class_probs':probs,'signal_series':{'name':key,'values':signals[key]},'model_mode':'health-main-fallback','model_error':self.error}
        try:
            return self.predictor.predict_scope_csv(str(csv_path))
        except Exception as exc:
            # Keep the UI usable when optional inference dependencies (for
            # example PyYAML) are unavailable; clearly label the result.
            self.error = f"Hier14 runtime unavailable: {type(exc).__name__}: {exc}"
            self.predictor = None
            return self.predict(csv_path)

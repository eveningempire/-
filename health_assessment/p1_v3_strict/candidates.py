"""Small deserialization compatibility shim for exported joblib artifacts.

The original training module is not part of the handoff.  Exported objects
only need ``apply``/``window_score`` at runtime; this fallback preserves the
bundle contract and uses the supplied evidence columns without claiming a
new trained model.
"""

from __future__ import annotations

import numpy as np


class HandoffModel:
    def apply(self, frame):
        values = frame.get("hi_cd")
        if values is None:
            values = frame.get("hi_ae")
        return np.asarray(values, dtype=float)

    def window_score(self, frame):
        return np.asarray(frame.get("anomaly_score"), dtype=float)


def __getattr__(name):
    # Pickle stores the original class name; dynamically provide a compatible
    # implementation for any exported handoff estimator class.
    if name.startswith("_"):
        raise AttributeError(name)
    cls = type(name, (HandoffModel,), {"__module__": __name__})
    globals()[name] = cls
    return cls

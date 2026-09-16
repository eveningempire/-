"""Causal degradation policy (registered 0.80/0.80/3-window rule), session
isolated, with abstain/degrade handling and low-confidence warnings."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .schemas import RecordError


class DegradationPolicy:
    """Registered P0 rule on the component_hi channel: enter <=0.80, exit >=0.80,
    3 consecutive finite windows confirm the alarm at the last of them.

    State never crosses a (session, run, component) boundary; rejected or
    non-finite windows do not advance the counters (a channel abstains, it
    never inherits state across a gap).
    """

    ENTER = 0.80
    EXIT = 0.80
    PERSISTENCE = 3

    def __init__(self) -> None:
        self._enter_run: Dict[tuple, int] = {}
        self._exit_run: Dict[tuple, int] = {}
        self._alarm: Dict[tuple, bool] = {}
        self._order: Dict[tuple, float] = {}

    def check_order(self, key: Tuple, timestamp: float) -> None:
        last = self._order.get(key)
        if last is not None and not (timestamp > last):
            raise RecordError("E_OUT_OF_ORDER", f"timestamp {timestamp} after {last}")
        self._order[key] = timestamp

    def step(self, key: Tuple, component_hi: float, confidence: Optional[float] = None) -> Dict:
        enter_run = self._enter_run.get(key, 0)
        exit_run = self._exit_run.get(key, 0)
        alarm = self._alarm.get(key, False)
        warnings: list = []
        if confidence is not None and confidence < 0.5:
            warnings.append("W_LOW_CONFIDENCE")
        enter_run = enter_run + 1 if component_hi <= self.ENTER else 0
        exit_run = exit_run + 1 if component_hi >= self.EXIT else 0
        if not alarm and enter_run >= self.PERSISTENCE:
            alarm = True
            exit_run = 0
        elif alarm and exit_run >= self.PERSISTENCE:
            alarm = False
            enter_run = 0
        self._enter_run[key] = enter_run
        self._exit_run[key] = exit_run
        self._alarm[key] = alarm
        if len([k for k in self._enter_run if k == key]) < self.PERSISTENCE and enter_run < self.PERSISTENCE and not alarm:
            # short history: the state is provisional until persistence is reachable
            warnings.append("W_INSUFFICIENT_HISTORY")
        return {"degradation_state": bool(alarm), "warnings": warnings}

    def reset(self, session_key: Optional[tuple] = None) -> None:
        if session_key is None:
            self._enter_run.clear()
            self._exit_run.clear()
            self._alarm.clear()
            self._order.clear()
            return
        for store in (self._enter_run, self._exit_run, self._alarm, self._order):
            for key in [k for k in list(store) if k[:2] == tuple(session_key[:2]) or k == session_key]:
                store.pop(key, None)

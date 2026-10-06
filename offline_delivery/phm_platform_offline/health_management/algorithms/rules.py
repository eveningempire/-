"""
Stub implementations for rule evaluation.

Rules are defined as JSON objects with parameter thresholds. The structure
should be agreed with the algorithm team. This module interprets a rule
definition of the form:

```
{
    "parameter": "param_name",
    "operator": ">",
    "value": 10.5
}
```

More complex rule types can be added in the future.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple


def evaluate_rule(definition: Dict[str, Any], data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Evaluates a single rule definition against a data record.

    Args:
        definition: A dict describing the rule.
        data: The data record as a dict.

    Returns:
        A tuple ``(is_triggered, details)`` indicating whether the rule
        fired and any additional information.
    """
    param = definition.get("parameter")
    operator = definition.get("operator")
    threshold = definition.get("value")
    value = data.get(param)
    triggered = False
    if value is not None and isinstance(value, (int, float)):
        if operator == ">":
            triggered = value > threshold
        elif operator == ">=":
            triggered = value >= threshold
        elif operator == "<":
            triggered = value < threshold
        elif operator == "<=":
            triggered = value <= threshold
        elif operator == "==":
            triggered = value == threshold
    details = {"parameter": param, "value": value, "threshold": threshold, "operator": operator}
    return triggered, details
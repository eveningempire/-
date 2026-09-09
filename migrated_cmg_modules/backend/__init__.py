"""Flask blueprints for the migrated PHM modules.

This package exposes two blueprints:

* `rule_bp` 鈥?rule editing endpoints and page
* `msfg_bp` 鈥?multi鈥憇ignal flow鈥慻raph endpoints and page

Each blueprint instantiates its own `safeRedis` client and imports
utilities from the original PHM project.  When registering the
blueprints, ensure that the `template_folder` argument points to
`../templates` relative to the package root.

Usage example:

```python
from flask import Flask
from migrated_cmg_modules.backend.rule_module import rule_bp
from migrated_cmg_modules.backend.msfg_module import msfg_bp

app = Flask(__name__, template_folder="migrated_cmg_modules/templates")
app.register_blueprint(rule_bp)
app.register_blueprint(msfg_bp)
```
"""

from .rule_module import rule_bp  # noqa: F401
from .msfg_module import msfg_bp  # noqa: F401

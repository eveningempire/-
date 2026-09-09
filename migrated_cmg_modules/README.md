This directory contains a minimal extract of the PHM health鈥慽nspection platform focusing on two core modules: **rule editing** and **multi鈥憇ignal flow鈥慻raph (MSFG) editing**.  It is intended to be used as the starting point for integrating these features into a new application.  The original project was implemented using Flask on the back鈥慹nd and Vue with Element鈥慤I on the front鈥慹nd.  Only the routes and templates required for the rule鈥慹diting and MSFG components have been brought over鈥攏o attempt has been made to reproduce the full application.

### Structure

```
migrated_cmg_modules/
鈹溾攢鈹€ backend/
鈹偮犅?鈹溾攢鈹€ __init__.py
鈹偮犅?鈹溾攢鈹€ msfg_module.py   鈥?blueprint exposing the MSFG API and page
鈹偮犅?鈹斺攢鈹€ rule_module.py   鈥?blueprint exposing the rule鈥慹diting API and page
鈹溾攢鈹€ templates/
鈹偮犅?鈹溾攢鈹€ msfg-edit.html   鈥?original template for the multi鈥憇ignal flow鈥慻raph editor
鈹偮犅?鈹斺攢鈹€ rule-edit.html   鈥?original template for the rule鈥慹ditor
鈹斺攢鈹€ README.md            鈥?this file
```

### Usage

Each module is implemented as a Flask `Blueprint`.  To use them in your own application:

```python
from flask import Flask
from migrated_cmg_modules.backend.rule_module import rule_bp
from migrated_cmg_modules.backend.msfg_module import msfg_bp

app = Flask(__name__)

# register blueprints under appropriate prefixes
app.register_blueprint(rule_bp)
app.register_blueprint(msfg_bp)

if __name__ == "__main__":
    app.run(debug=True)
```

The templates expect that Vue, axios, Element鈥慤I and LogicFlow are served from `/static/jsscripts/鈥 just as in the original project.  You will need to provide these static assets yourself or update the `<script>` and `<link>` tags in the templates to point at the versions hosted by your own application.  Likewise, both blueprints make use of a Redis instance (via the `safeRedis` wrapper from the original project) to persist their configuration.  The wrapper will attempt to connect to a local Redis server by default.

Because the original project persisted configuration information in both Redis and an underlying database, these modules store and retrieve only from Redis.  If you wish to integrate database persistence, you should adapt the `safeRedis` implementation in `lib/databaseModule/redisProcess.py` from the original project.

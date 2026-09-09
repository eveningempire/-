"""Blueprint providing routes for configuring and editing expert rules.

This module re鈥慽mplements the subset of endpoints from the original
`manage.py` that are involved in rule editing.  It exposes a
blueprint called ``rule_bp`` which can be registered with a Flask
application.  The blueprint relies on the original PHM
infrastructure (notably the ``safeRedis`` wrapper and
``ruleConvertor`` helper) to store configuration in Redis and to
compile rule expressions into an internal representation used by the
detection engine.  Only the rule鈥慹diting API is provided 鈥?any
unrelated functionality has been omitted.

At start鈥憉p the module adds the path to the original PHM source tree
to ``sys.path`` so that imports such as ``lib.algoModule...`` work
correctly.  If you relocate these modules you will need to adjust
``PROJECT_ROOT`` accordingly.
"""

from __future__ import annotations

import json
import os
import sys
from flask import Blueprint, render_template, request, jsonify

# Compute the absolute path to the original project root.  This
# assumes that this file lives in ``migrated_cmg_modules/backend`` and
# that the original project is extracted in ``PHM_Platform/PHM_Platform``
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'PHM_Platform', 'PHM_Platform')
)

# Prepend the project root to sys.path if it is not already there.
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    # Import the safeRedis wrapper and the rule converter from the original
    # project.  If these imports fail you should ensure that
    # PROJECT_ROOT points to the correct location of the original PHM
    # source tree.
    from lib.databaseModule.redisProcess import safeRedis
    from lib.algoModule.detectAlgo.rule.RuleDetector import ruleConvertor
except Exception as exc:
    raise ImportError(
        f"Failed to import required modules from the original PHM project: {exc}.\n"
        f"PROJECT_ROOT is set to {PROJECT_ROOT}.  Adjust this path as necessary."
    )

# Instantiate a Redis wrapper.  By default this connects to
# ``localhost:6379``.  You may override the host/port by passing
# keyword arguments when creating the Blueprint, e.g.::
#
#     rule_bp = create_rule_blueprint(redis_kwargs={"host": "my鈥憆edis", "port": 6380})


def create_rule_blueprint(name: str = 'rule_edit', redis_kwargs: dict | None = None) -> Blueprint:
    """Factory function returning a rule鈥慹diting blueprint.

    Parameters
    ----------
    name:
        Blueprint name.  Defaults to ``'rule_edit'``.
    redis_kwargs:
        Optional dictionary of keyword arguments forwarded to ``safeRedis``.

    Returns
    -------
    flask.Blueprint
        A blueprint exposing the rule鈥慹diting API and view.
    """
    redis_engine = safeRedis(**(redis_kwargs or {}))

    bp = Blueprint(
        name,
        __name__,
        template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates')),
    )

    @bp.route('/rule-edit', methods=['GET', 'POST'])
    def rule_edit_page():
        """Serve the rule editor page.

        Returns the ``rule-edit.html`` template.  The template uses
        Vue.js on the client to call the API endpoints defined below.
        """
        return render_template('rule-edit.html')

    @bp.route('/rule-edit/get-config', methods=['POST'])
    def get_config():
        """Return configuration metadata for the rule editor.

        The front鈥慹nd expects lists of existing fault names, component
        names, measurement point names and the list of rule sources.
        Values are read from Redis.  If no configuration is found
        empty structures are returned.
        """
        obj = request.form.get('obj', 'cmg')
        # Retrieve mapping from fault IDs to their properties
        fault_names_raw = redis_engine.hget(obj, 'fault-name-config')
        fault_names = json.loads(fault_names_raw or '{}')
        # Retrieve parameter names.  On the front鈥慹nd these are shown
        # in the measurement point drop鈥慸own; we map each name to itself.
        pnames_raw = redis_engine.hget(obj, 'pnames')
        pnames = json.loads(pnames_raw or '{}')
        pnames_map = {p: p for p in pnames}
        # Retrieve the list of components.  Again we return a mapping
        # from each component to itself.
        comps_raw = redis_engine.hget(obj, 'components')
        components = json.loads(comps_raw or '{}')
        comps_map = {comp: comp for comp in components}
        return jsonify({
            'faultNames': fault_names,
            'components': comps_map,
            'pnames': pnames_map,
            # These are the available sources for rules.  The
            # front鈥慹nd expects an object mapping values to labels.
            'sources': {
                '涓撳鎰忚': '涓撳鎰忚',
                '鏁版嵁椹卞姩鎸栨帢': '鏁版嵁椹卞姩鎸栨帢',
            },
        })

    @bp.route('/rule-edit/init-all-rule', methods=['GET', 'POST'])
    def init_all_rule():
        """Return the stored rule table.

        Reads the ``rule-edit-config`` key from Redis, expecting it to
        contain a JSON list of rule entries.  If nothing is found an
        empty list is returned.
        """
        obj = request.form.get('obj', 'cmg')
        table_data_raw = redis_engine.hget(obj, 'rule-edit-config')
        table_data = json.loads(table_data_raw or '[]')
        return jsonify(table_data)

    @bp.route('/rule-edit/config-rule', methods=['GET', 'POST'])
    def config_rule():
        """Persist updated rule definitions.

        The front鈥慹nd posts a ``tableData`` form field containing a
        JSON array of rule objects.  After writing this array back
        into Redis under the ``rule-edit-config`` key we convert
        those rules that are marked online into an internal
        representation understood by the detector and store the
        resulting data under the ``rule-config`` key.
        """
        obj = request.form.get('obj', 'cmg')
        table_data_str = request.form.get('tableData', '')
        if not table_data_str:
            return jsonify({'error': 'tableData is required'}), 400
        try:
            table_data = json.loads(table_data_str)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON in tableData'}), 400
        # Retrieve measurement point names.  The rule converter uses
        # this mapping to resolve which component a parameter belongs
        # to.
        pnames_raw = redis_engine.hget(obj, 'pnames') or '{}'
        pnames = json.loads(pnames_raw)
        # Convert rules into the detector format.  The converter
        # returns a JSON string of internal structures plus the
        # original table; we only persist the first element here.
        online_rules_json, _ = ruleConvertor(pnames)._config_rule(table_data)
        # Persist the user鈥慺acing rule definitions and the compiled
        # rules separately.  Clients should call ``init-all-rule`` to
        # retrieve the original definitions.
        redis_engine.hset(obj, 'rule-edit-config', table_data_str)
        redis_engine.hset(obj, 'rule-config', online_rules_json)
        return jsonify(None)

    return bp


# Provide a default blueprint instance so that the importing code can
# simply do ``from migrated_cmg_modules.backend.rule_module import rule_bp``.
rule_bp = create_rule_blueprint()


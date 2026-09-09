"""Blueprint providing routes for the multi鈥憇ignal flow鈥慻raph editor.

This module extracts the MSFG鈥憆elated functionality from the original
PHM platform and exposes it as a standalone Flask blueprint.  The
editor itself is implemented on the front鈥慹nd in Vue and LogicFlow
and is served from the ``msfg-edit.html`` template contained in
``templates/``.  The back鈥慹nd stores configuration data in Redis via
the ``safeRedis`` wrapper and exposes a handful of APIs for
initialising and persisting the graph as well as running analysis
against measurement data.

To integrate this blueprint into your own application simply
register it with your Flask app as shown in the package README.  If
you wish to customise the Redis connection, use the factory
function ``create_msfg_blueprint`` instead of importing the global
``msfg_bp``.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Dict, List, Any

from flask import Blueprint, render_template, request, jsonify

# Compute the absolute path to the original PHM project and add it
# to sys.path so that imports work.  See ``rule_module.py`` for more
# details.
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', 'PHM_Platform', 'PHM_Platform')
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from lib.databaseModule.redisProcess import safeRedis
    from lib.flaskModule.msfgModule import utils as msfg_util
    from lib.flaskModule.msfgModule.msfgApp import msfg_route_app
except Exception as exc:
    raise ImportError(
        f"Failed to import required modules from the original PHM project: {exc}.\n"
        f"PROJECT_ROOT is set to {PROJECT_ROOT}.  Adjust this path if necessary."
    )


def create_msfg_blueprint(name: str = 'msfg_edit', redis_kwargs: dict | None = None) -> Blueprint:
    """Factory function returning a blueprint for MSFG editing.

    Parameters
    ----------
    name:
        Name of the blueprint.  Defaults to ``'msfg_edit'``.
    redis_kwargs:
        Optional dictionary of keyword arguments forwarded to ``safeRedis``.

    Returns
    -------
    flask.Blueprint
        A blueprint exposing the MSFG API and page.
    """
    redis_engine = safeRedis(**(redis_kwargs or {}))

    bp = Blueprint(
        name,
        __name__,
        template_folder=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates')),
    )

    # -------------------------------------------------------------------
    # Page route
    # -------------------------------------------------------------------
    @bp.route('/multi-info-edit', methods=['GET', 'POST'])
    def msfg_edit_page() -> Any:
        """Render the MSFG editor page."""
        return render_template('msfg-edit.html')

    # -------------------------------------------------------------------
    # Graph initialisation
    # -------------------------------------------------------------------
    @bp.route('/multi-info-edit/init-graph/', methods=['GET', 'POST'])
    def msfg_init_graph() -> Any:
        """Return the stored MSFG structure.

        The graph is stored in Redis under the key ``msfg-raw-config``.
        If nothing is found an empty list is returned.  The front鈥慹nd
        expects a JSON serialisable structure.
        """
        obj = request.form.get('obj', 'cmg')
        raw = redis_engine.hget(obj, 'msfg-raw-config')
        res = json.loads(raw or '[]')
        return jsonify(res)

    # -------------------------------------------------------------------
    # Graph persistence
    # -------------------------------------------------------------------
    @bp.route('/multi-info-edit/config-graph/', methods=['GET', 'POST'])
    def msfg_config_graph() -> Any:
        """Persist the MSFG structure and derive detection configuration.

        The client posts a ``graphData`` form field containing a
        JSON鈥慹ncoded MSFG.  This function stores the raw graph in
        Redis, computes the corresponding detection matrices using
        utilities from the original project and stores derived
        information (fault names, measurement point names, component
        names) under separate keys.  See ``manage.py`` in the
        original project for additional context.
        """
        obj = request.form.get('obj', 'cmg')
        graph_data = request.form.get('graphData')
        if not graph_data:
            return jsonify({'error': 'graphData is required'}), 400
        try:
            struct_raw = json.loads(graph_data)
        except json.JSONDecodeError:
            return jsonify({'error': 'Invalid JSON in graphData'}), 400
        # Persist the raw graph.  ``safeRedis`` automatically derives
        # and stores the processed ``msfg-config`` when writing
        # ``msfg-raw-config`` 鈥?see ``safeRedis.hset`` in the original
        # project.
        redis_engine.hset(obj, 'msfg-raw-config', graph_data)
        # Unpack the structure for analysis.  The raw graph may be
        # wrapped in an object with a ``SystemData`` field; unwrap it
        # if necessary.
        struct = struct_raw
        if isinstance(struct_raw, dict) and 'SystemData' in struct_raw:
            struct = struct_raw['SystemData']
        # Flatten the graph and compute the detection matrix.  ``to_D_mat``
        # returns several values including test/fault names and a
        # fault configuration mapping; see utils.py for details.
        try:
            nodes, edges, system = msfg_util.flatten_graph(struct)
            D_mat, test_name, fault_name, conn_ids, test_loc, fault_loc, sysmap, collision_node, fault_config = (
                msfg_util.to_D_mat(nodes, edges, system, eps=1e-15, raise_collision=False)
            )
        except Exception as e:
            # If the graph is invalid, report the error to the client.
            return jsonify({'error': f'Failed to process graph: {e}'}), 500
        # Store measurement point names and component names for use in
        # rule editing.  ``test_name`` is a list of measurement point
        # identifiers while the helper below extracts component names
        # from the raw structure.
        pnames = test_name
        components = _extract_component_names(struct)
        redis_engine.hset(obj, 'pnames', json.dumps(pnames))
        redis_engine.hset(obj, 'components', json.dumps(components))
        # Store fault names along with an empty component field.  The
        # front鈥慹nd expects a mapping from fault identifiers to
        # configuration dictionaries.  We extend the dictionaries with
        # a ``component`` property here to match the original
        # behaviour.
        fault_info = {
            infon: {**info, 'component': info.get('component', '')}
            for infon, info in fault_config.items()
        }
        redis_engine.hset(obj, 'fault-name-config', json.dumps(fault_info))
        return jsonify(None)

    # -------------------------------------------------------------------
    # Extract component names
    # -------------------------------------------------------------------
    def _extract_component_names(data: Any) -> List[str]:
        """Return a list of subsystem names from a nested MSFG.

        The MSFG structure contains subsystem dictionaries with a
        ``name`` field at the top level of ``SystemData``.  This helper
        walks the list and collects the names.  If the structure is
        nested differently or missing names, the returned list may be
        empty.
        """
        if isinstance(data, dict) and 'SystemData' in data:
            data = data['SystemData']
        result: List[str] = []
        if isinstance(data, list):
            for itm in data:
                if isinstance(itm, dict) and 'name' in itm:
                    result.append(itm['name'])
        return result

    # -------------------------------------------------------------------
    # Delegate additional MSFG API endpoints to the original app
    # -------------------------------------------------------------------
    # The original PHM platform defined several more endpoints related to
    # uploading FMECA/Visio files, optimising and checking graphs and
    # running analyses.  Rather than re鈥慽mplement these here we reuse
    # the functions from ``msfgApp`` and register them against this
    # blueprint.  Each function uses ``request`` and ``redis_engine``
    # above implicitly via closure or import.
    msfg_route_app(bp)

    return bp


# Provide a default blueprint instance.  This allows importing code to
# do ``from migrated_cmg_modules.backend.msfg_module import msfg_bp``.
msfg_bp = create_msfg_blueprint()


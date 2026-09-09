import logging
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

def _get_node_name(node: Dict[str, Any]) -> str:
    """Extracts a node's name from various possible keys."""
    props = node.get('properties') or {}
    name = (
        props.get('tableName') or
        (node.get('text') or {}).get('value') or
        node.get('name') or
        str(node.get('id', ''))
    )
    return str(name).strip() if name else ''

def extract_mappings_from_graph(parsed_graph: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """
    Extracts direct and indirect mappings from a parsed graph structure.

    Args:
        parsed_graph: The dictionary output from normalize_and_parse_graph.

    Returns:
        A dictionary containing lists of different mapping types.
    """
    nodes = parsed_graph.get('nodes', [])
    edges = parsed_graph.get('edges', [])
    
    if not nodes or not edges:
        return {
            "test_to_fault": [],
            "fault_to_component": [],
            "test_to_component": [],
        }

    # Create fast lookups
    node_map = {str(n.get('id')): n for n in nodes}
    adj = defaultdict(list)
    for edge in edges:
        source_id = str(edge.get('sourceNodeId'))
        target_id = str(edge.get('targetNodeId'))
        if source_id in node_map and target_id in node_map:
            adj[source_id].append(target_id)

    # --- 1. Extract Direct Mappings ---
    direct_test_fault = []
    direct_fault_component = []
    direct_test_component = []

    for edge in edges:
        source_id = str(edge.get('sourceNodeId'))
        target_id = str(edge.get('targetNodeId'))

        if source_id in node_map and target_id in node_map:
            source_node = node_map[source_id]
            target_node = node_map[target_id]
            
            source_cat = source_node.get('category')
            target_cat = target_node.get('category')
            
            source_name = _get_node_name(source_node)
            target_name = _get_node_name(target_node)

            if source_cat == 'Test' and target_cat == 'Fault':
                direct_test_fault.append({
                    "test_point_name": source_name,
                    "fault_name": target_name,
                    "type": "direct"
                })
            elif source_cat == 'Fault' and target_cat == 'Component':
                direct_fault_component.append({
                    "fault_name": source_name,
                    "component_name": target_name,
                    "type": "direct"
                })
            elif source_cat == 'Test' and target_cat == 'Component':
                 direct_test_component.append({
                    "test_point_name": source_name,
                    "component_name": target_name,
                    "type": "direct"
                })

    # --- 2. Extract Indirect Mappings (Test -> Component) via Faults ---
    # Build a fault-to-components map for quick lookup
    fault_to_components = defaultdict(list)
    for mapping in direct_fault_component:
        fault_to_components[mapping["fault_name"]].append(mapping["component_name"])

    indirect_test_component = []
    # Find Test -> Fault -> Component paths
    for tf_map in direct_test_fault:
        test_name = tf_map["test_point_name"]
        fault_name = tf_map["fault_name"]
        if fault_name in fault_to_components:
            for component_name in fault_to_components[fault_name]:
                indirect_test_component.append({
                    "test_point_name": test_name,
                    "component_name": component_name,
                    "type": "indirect",
                    "via": fault_name
                })
                
    # --- 3. Consolidate and Deduplicate Mappings ---
    def deduplicate(mappings: List[Dict]) -> List[Dict]:
        seen = set()
        result = []
        if not mappings:
            return result
        
        key_fields = tuple(mappings[0].keys())
        # Adjust key fields for different mapping types to ensure proper uniqueness
        if "test_point_name" in key_fields and "fault_name" in key_fields:
            unique_keys = ("test_point_name", "fault_name")
        elif "fault_name" in key_fields and "component_name" in key_fields:
            unique_keys = ("fault_name", "component_name")
        elif "test_point_name" in key_fields and "component_name" in key_fields:
            unique_keys = ("test_point_name", "component_name")
        else:
            unique_keys = key_fields
            
        for m in mappings:
            # Create a unique key based on the mapping's core values
            key = tuple(m.get(k) for k in unique_keys)
            if key not in seen:
                seen.add(key)
                result.append(m)
        return result

    # Combine direct and indirect, then deduplicate
    all_test_component = direct_test_component + indirect_test_component
    
    return {
        "test_to_fault": deduplicate(direct_test_fault),
        "fault_to_component": deduplicate(direct_fault_component),
        "test_to_component": deduplicate(all_test_component),
    }

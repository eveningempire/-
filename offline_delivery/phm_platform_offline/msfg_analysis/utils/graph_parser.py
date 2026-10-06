from typing import Dict, List, Any
import logging
import copy

logger = logging.getLogger(__name__)

def _get_node_category(node: Dict[str, Any]) -> str:
    """
    Robustly determines the category of a node.
    
    It first checks for a 'category' key. If not found, it falls back to
    interpreting the 'type' key for backward compatibility.
    
    Args:
        node: The node dictionary from the graph data.
        
    Returns:
        The determined category name (e.g., 'Test', 'Fault', 'Component', 'AND').
    """
    # 1. Prioritize the explicit 'category' attribute
    category = node.get('category')
    if category and isinstance(category, str) and category.strip():
        return category.strip()

    # 2. Fallback to the 'type' attribute for backward compatibility
    node_type = node.get('type')
    if isinstance(node_type, str):
        ntype_lower = node_type.lower()
        if 'test' in ntype_lower:
            return 'Test'
        if 'fault' in ntype_lower:
            return 'Fault'
        if 'and' in ntype_lower:
            return 'AND'
        # 'subsystem-node', 'component-node' etc. are all components
        if 'system' in ntype_lower or 'component' in ntype_lower:
            return 'Component'

    # 3. Default to 'Component' if no specific category can be determined
    return 'Component'

def normalize_and_parse_graph(graph_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes the graph data by ensuring every node has a 'category' attribute,
    and then parses it to extract categorized node lists and names.
    
    Args:
        graph_data: The raw graph data dictionary, potentially in various formats.
        
    Returns:
        A dictionary containing the normalized graph and parsed data:
        {
            'normalized_graph': The graph data with 'category' in every node,
            'nodes': List of all nodes,
            'edges': List of all edges,
            'test_nodes': List of test node objects,
            'fault_nodes': List of fault node objects,
            'component_nodes': List of component node objects,
            'and_nodes': List of AND node objects,
            'test_names': List of unique test names,
            'fault_names': List of unique fault names,
            'component_names': List of unique component names
        }
    """
    if not isinstance(graph_data, dict):
        logger.warning("Input graph_data is not a dictionary. Returning empty structure.")
        return {}

    # Deep copy to avoid modifying the original object
    normalized_graph = copy.deepcopy(graph_data)
    
    # Handle both direct {nodes, edges} and nested {SystemData: [...]} structures
    system_data_list = normalized_graph.get('SystemData')
    all_nodes = []
    all_edges = []

    if isinstance(system_data_list, list):
        for system in system_data_list:
            if isinstance(system, dict) and isinstance(system.get('data'), dict):
                nodes = system.get('data', {}).get('nodes', [])
                edges = system.get('data', {}).get('edges', [])
                if isinstance(nodes, list):
                    all_nodes.extend(nodes)
                if isinstance(edges, list):
                    all_edges.extend(edges)
    else:
        nodes = normalized_graph.get('nodes', [])
        edges = normalized_graph.get('edges', [])
        if isinstance(nodes, list):
            all_nodes = nodes
        if isinstance(edges, list):
            all_edges = edges

    # --- Normalization and Parsing ---
    test_nodes, fault_nodes, component_nodes, and_nodes = [], [], [], []
    
    for node in all_nodes:
        if not isinstance(node, dict):
            continue
            
        category = _get_node_category(node)
        node['category'] = category  # Ensure the category is explicitly set

        if category == 'Test':
            test_nodes.append(node)
        elif category == 'Fault':
            fault_nodes.append(node)
        elif category == 'AND':
            and_nodes.append(node)
        else: # 'Component' and any other defaults
            component_nodes.append(node)
            
    def get_node_name(n: Dict[str, Any]) -> str:
        """Extracts a node's name from various possible keys."""
        props = n.get('properties') or {}
        name = (
            props.get('tableName') or
            (n.get('text') or {}).get('value') or
            n.get('name') or
            str(n.get('id', ''))
        )
        return str(name).strip() if name else ''

    # --- Extract unique names ---
    seen_test_names, test_names = set(), []
    for n in test_nodes:
        name = get_node_name(n)
        if name and name not in seen_test_names:
            seen_test_names.add(name)
            test_names.append(name)

    seen_fault_names, fault_names = set(), []
    for n in fault_nodes:
        name = get_node_name(n)
        if name and name not in seen_fault_names:
            seen_fault_names.add(name)
            fault_names.append(name)

    seen_comp_names, component_names = set(), []
    for n in component_nodes:
        name = get_node_name(n)
        # Exclude root or generic system names from component list
        if name and name.lower() not in ['root', 'system', '']:
            if name not in seen_comp_names:
                seen_comp_names.add(name)
                component_names.append(name)

    return {
        'normalized_graph': normalized_graph,
        'nodes': all_nodes,
        'edges': all_edges,
        'test_nodes': test_nodes,
        'fault_nodes': fault_nodes,
        'component_nodes': component_nodes,
        'and_nodes': and_nodes,
        'test_names': test_names,
        'fault_names': fault_names,
        'component_names': component_names,
    }

from .ir_builder import IRBuilder
from .cfg_builder import CFGBuilder
from .analyzer import CFGAnalyzer
# visualizer optional (not for API)
# from .visualizer import CFGVisualizer
from .flowchart import FlowchartGenerator

def get_node_description(node):
    """Generate human-readable description for a node"""
    node_type = node.get("type", "unknown")
    
    if node_type == "start":
        return "START"
    elif node_type == "end":
        return "END"
    elif node_type == "process":
        return node.get("code", "process")
    elif node_type == "output":
        return node.get("code", "output")
    elif node_type == "decision":
        return f"if {node.get('condition', '...')}"
    elif node_type == "loop":
        return f"while {node.get('condition', '...')}"
    elif node_type == "for":
        var = node.get("var", "i")
        start = node.get("start", "0")
        end = node.get("end", "n")
        return f"for {var} from {start} to {end}"
    elif node_type == "else":
        return "else"
    elif node_type == "end_if":
        return "end_if"
    elif node_type == "loop_end":
        return "loop_end"
    else:
        return node_type

def convert_ir_readable(ir):
    """Convert IR to readable format with node descriptions"""
    # Create a mapping of node ID to node object
    node_map = {node["id"]: node for node in ir["nodes"]}
    
    readable_ir = {
        "nodes": ir["nodes"],
        "edges": []
    }
    
    for edge in ir["edges"]:
        source_id = edge["from"]
        target_id = edge["to"]
        
        source_node = node_map.get(source_id, {"type": "unknown"})
        target_node = node_map.get(target_id, {"type": "unknown"})
        
        source_desc = get_node_description(source_node)
        target_desc = get_node_description(target_node)
        
        readable_edge = {
            "from": {
                "id": source_id,
                "label": source_desc
            },
            "to": {
                "id": target_id,
                "label": target_desc
            }
        }
        
        # Include label if it exists
        if "label" in edge:
            readable_edge["label"] = edge["label"]
        
        readable_ir["edges"].append(readable_edge)
    
    return readable_ir

def convert_analysis_readable(ir, dead_code, cycles, branch_errors):
    """Convert analysis results to readable format with node descriptions"""
    # Create a mapping of node ID to node object
    node_map = {node["id"]: node for node in ir["nodes"]}
    
    # Convert dead code
    readable_dead_code = [
        {
            "id": node_id,
            "label": get_node_description(node_map.get(node_id, {"type": "unknown"}))
        }
        for node_id in dead_code
    ]
    
    # Convert cycles
    readable_cycles = []
    for i, cycle in enumerate(cycles):
        cycle_path = []
        for node_id in cycle:
            node = node_map.get(node_id, {"type": "unknown"})
            cycle_path.append({
                "id": node_id,
                "label": get_node_description(node)
            })
        
        readable_cycles.append({
            "cycle_number": i + 1,
            "path": cycle_path
        })
    
    # Convert branch errors
    readable_branch_errors = []
    for error in branch_errors:
        # Parse error message and replace node IDs with descriptions
        readable_error = error
        for node_id, node in node_map.items():
            node_desc = get_node_description(node)
            readable_error = readable_error.replace(f"Node {node_id}", f"Node {node_id} ({node_desc})")
        readable_branch_errors.append(readable_error)
    
    return {
        "dead_code": readable_dead_code,
        "cycles": readable_cycles,
        "branch_errors": readable_branch_errors
    }

def convert_cfg_edges_readable(G, ir):
    """Convert CFG edges to readable format with node descriptions"""
    # Create a mapping of node ID to node object
    node_map = {node["id"]: node for node in ir["nodes"]}
    
    readable_edges = []
    for source, target, data in G.edges(data=True):
        source_node = node_map.get(source, {"type": "unknown"})
        target_node = node_map.get(target, {"type": "unknown"})
        
        source_desc = get_node_description(source_node)
        target_desc = get_node_description(target_node)
        
        readable_edges.append({
            "from": {
                "id": source,
                "label": source_desc
            },
            "to": {
                "id": target,
                "label": target_desc
            },
            "label": data.get("label", "")
        })
    
    return readable_edges

def run_pipeline(tokens):

    if not tokens:
        return {
            "ir": {},
            "cfg_edges": [],
            "dead_code": [],
            "cycles": [],
            "branch_errors": [],
            "flowchart": ""
        }

    ir_builder = IRBuilder()
    ir = ir_builder.build(tokens)

    cfg_builder = CFGBuilder()
    G = cfg_builder.build(ir)

    analyzer = CFGAnalyzer(G)

    # Get raw analysis results
    dead_code = analyzer.reachability()
    cycles = analyzer.detect_cycles()
    branch_errors = analyzer.validate_branches()

    # 🔥 SAFE FLOWCHART
    flowchart_path = ""
    try:
        flowchart = FlowchartGenerator()
        flowchart_path = flowchart.generate(ir)
    except Exception as e:
        print("Flowchart failed:", e)

    # Convert analysis to readable format
    readable_analysis = convert_analysis_readable(ir, dead_code, cycles, branch_errors)

    return {
        "ir": convert_ir_readable(ir),
        "cfg_edges": convert_cfg_edges_readable(G, ir),
        "dead_code": readable_analysis["dead_code"],
        "cycles": readable_analysis["cycles"],
        "branch_errors": readable_analysis["branch_errors"],
        "flowchart": flowchart_path
    }
from .ir_builder import IRBuilder
from .cfg_builder import CFGBuilder
from .analyzer import CFGAnalyzer
# visualizer optional (not for API)
# from .visualizer import CFGVisualizer
from .flowchart import FlowchartGenerator

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

    # 🔥 SAFE FLOWCHART
    flowchart_path = ""
    try:
        flowchart = FlowchartGenerator()
        flowchart_path = flowchart.generate(ir)
    except Exception as e:
        print("Flowchart failed:", e)

    return {
        "ir": ir,
        "cfg_edges": list(G.edges(data=True)),
        "dead_code": analyzer.reachability(),
        "cycles": analyzer.detect_cycles(),
        "branch_errors": analyzer.validate_branches(),
        "flowchart": flowchart_path
    }
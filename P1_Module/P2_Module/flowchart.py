from graphviz import Digraph
import os

class FlowchartGenerator:

    def generate(self, ir):
        try:
            dot = Digraph(format='png')

            # Nodes
            for node in ir["nodes"]:
                node_id = str(node["id"])

                if node["type"] == "start":
                    dot.node(node_id, "Start", shape="oval")
                elif node["type"] == "end":
                    dot.node(node_id, "End", shape="oval")
                elif node["type"] == "decision":
                    dot.node(node_id, node.get("condition", ""), shape="diamond")
                else:
                    dot.node(node_id, node.get("code", ""), shape="box")

            # Edges
            for edge in ir["edges"]:
                label = edge.get("label", "")
                dot.edge(str(edge["from"]), str(edge["to"]), label=label)

            # Ensure static folder exists
            os.makedirs("static", exist_ok=True)

            # Save file
            filepath = "static/flowchart"
            dot.render(filepath, format='png', cleanup=True)

            return "/static/flowchart.png"

        except Exception as e:
            print("🔥 Flowchart Error:", e)
            return ""
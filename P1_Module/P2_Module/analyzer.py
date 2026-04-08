import networkx as nx

class CFGAnalyzer:

    def __init__(self, G):
        self.G = G

    def reachability(self):
        start = [n for n, d in self.G.nodes(data=True) if d["type"] == "start"][0]
        reachable = nx.descendants(self.G, start) | {start}
        return list(set(self.G.nodes()) - reachable)

    def detect_cycles(self):
        return list(nx.simple_cycles(self.G))

    def validate_branches(self):
        errors = []

        for node, data in self.G.nodes(data=True):
            if data["type"] == "decision":
                out_edges = list(self.G.out_edges(node, data=True))

                labels = [e[2].get("label") for e in out_edges]

                if "true" not in labels or "false" not in labels:
                    errors.append(f"Node {node} missing true/false branch")

        return errors
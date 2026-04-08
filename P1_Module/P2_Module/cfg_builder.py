import networkx as nx

class CFGBuilder:

    def build(self, ir):
        G = nx.DiGraph()

        for node in ir["nodes"]:
            G.add_node(node["id"], **node)

        for edge in ir["edges"]:
            label = edge.get("label", "")
            G.add_edge(edge["from"], edge["to"], label=label)

        return G
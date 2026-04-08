import matplotlib.pyplot as plt
import networkx as nx

class CFGVisualizer:

    def draw(self, G):
        pos = nx.spring_layout(G)

        labels = {}
        for n, d in G.nodes(data=True):
            if d["type"] == "decision":
                labels[n] = d["condition"]
            elif "code" in d:
                labels[n] = d["code"]
            else:
                labels[n] = d["type"]

        edge_labels = nx.get_edge_attributes(G, 'label')

        nx.draw(G, pos, with_labels=True, labels=labels, node_size=2000)
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)

        plt.title("Control Flow Graph")
        plt.show()
import matplotlib.pyplot as plt
import networkx as nx


class GraphTool:

    def create_graph(self, dependencies):
        graph = nx.DiGraph()
        for file_name, imports in dependencies.items():
            graph.add_node(file_name)

            for import_detail in imports:

                module = import_detail["module"]
                graph.add_edge(file_name, module)

        return graph

    def plot_graph(self, graph):

        # Larger canvas for larger projects
        fig = plt.figure(figsize=(24, 18))

        # Increase distance between nodes
        pos = nx.spring_layout(graph, k=5, iterations=300, seed=42)

        nx.draw_networkx_nodes(graph, pos, node_size=6000)

        nx.draw_networkx_edges(graph, pos, arrows=True, arrowsize=25, width=2, alpha=0.7, connectionstyle="arc3,rad=0.05")

        nx.draw_networkx_labels(graph, pos, font_size=13, font_weight="bold")

        plt.axis("off")
        plt.tight_layout()

        return fig
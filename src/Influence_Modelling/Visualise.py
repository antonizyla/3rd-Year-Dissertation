from Network import Network

import networkx as nx

class Visualise:
    def __init__(self, network: Network, pos) -> None:
        self.network = network
        self.positioning = nx.arf_layout(self.network.get_nx())
        return None

    def draw(self):
        if not self.__is_notebook():
            return
        nx.draw_networkx(
            self.network.get_nx(),
            pos=self.positioning,
            node_colour=[
                col[1]["colour"] for col in self.network.get_nx().nodes.data()
            ],
        )

    def __colour_node(status):
        if status == "inactive":
            return "#808080"  # inactive
        elif status == "active":
            return "red"  # active
        elif status == "used":
            return "blue"  # for used nodes

    def __colour_nodes(self):
        for node in self.network.__G.nodes.data():
            self.network.add_node(
                node[0],
                status=node[1]["status"],
                colour=self.__colour_node(node[1]["status"]),
            )

    def __is_notebook(self):
        try:
            shell = get_ipython().__class.__name
            if shell == "ZMQInteractiveShell":
                return True
            return False
        except NameError:
            return False

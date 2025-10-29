import math
import random

import networkx as nx
from networkx.algorithms.graphical import is_graphical
from networkx.utils.random_sequence import powerlaw_sequence

from Influence_Modelling import Heuristics, helper


class Network:
    """
    Network Class: Create, Update, Load, Save networks into a database.
    Run simulations on networks using ICC, DCC and LTM models and utilise
    various heuristics to choose seed nodes
    """

    def get_nx(self):
        return self.__G

    def __init__(self, project: str, name: str, verbose: bool = False) -> None:
        """
        Initialise a new empty Graph.
        :param str project: Name of Project - links to sqlite file
        :param str name: Name of Network
        """
        self.__G: nx.DiGraph = nx.empty_graph()
        self.__H = self.__G
        self.__name: str = name
        self.__v = verbose
        self.__limit: int = 10**5  # limit on the number of iterations reached

    def set_nx(self, G: nx.DiGraph):
        self.__G = G
        self.__H = self.__G.copy()

    def run_ICC(
        self, seed_nodes, p: float = 0.1, iteration_limit=None
    ) -> tuple[int, nx.DiGraph]:
        """
        Run a simulation of the independant cascade model on the network.
        :param float p: Probability of a node turning a neighbouring node
        :param list seed_nodes: The set of nodes which start the spread in
        the network
        :return: A tuple in the form `(i, G)`, where `i` is the number of
        iterations before the network could no longer change in influence
        and `G` is the final graph after `i` iterations
        """

        self.__H: nx.DiGraph = self.__G.copy()

        if seed_nodes is None or seed_nodes == []:
            print(
                f"""[Independant Cascade Model]  on network: {self.__name}. 
                No seed nodes provided. Using Random Nodes"""
            )
            seed_nodes = Heuristics.random_h(self.get_nx())

        # set all nodes to be inactive
        for v in self.__H.nodes.data():
            self.__H.add_node(v[0], status="inactive")
        # set our seed nodes to be active
        for s in seed_nodes:
            self.__H.add_node(s, status="active")

        if iteration_limit is not None:
            self.__limit = iteration_limit
        i: int = 0
        while not self.__all_nodes_complete() and i < self.__limit:
            for node in self.__active_nodes():
                self.__H.add_node(node, status="used")
                for adj in self.__H.adj[node]:
                    if helper.turn(p) and self.__H.nodes[adj]["status"] == "inactive":
                        self.__H.add_node(adj, status="active")
            i += 1
        return (i, self.__H)

    def __all_nodes_complete(self) -> bool:
        for n in self.__H.nodes.data():
            if n[1]["status"] == "active":
                return False
        return True

    def run_DCC(
        self, seed_nodes, p: float = 0.1, dec_func=lambda x: x * 0.7
    ) -> tuple[int, nx.DiGraph]:
        """
        Run a simulation of the decreasing cascade model on the network.
        :param float p: Probability of a node turning a neighbouring node
        :param list seed_nodes: The set of nodes which start the spread in
        the network
        :param lambda dec_func: A single variable lambda function which
        denotes how the likelyhood of a node being influenced changes every
        time it is attempted.
        :return: A tuple in the form `(i, G)`, where `i` is the number of
        iterations before the network could no longer change in influence
        and `G` is the final graph after `i` iterations
        """
        self.__H = self.__G

        if seed_nodes is None or seed_nodes == []:
            print(
                f"""[Decreasing Cascade Model] on network: {self.__name}. 
                No seed nodes provided. Using Random Nodes"""
            )
            seed_nodes = Heuristics.random_h(self.get_nx())

        # all nodes inactive and get a starting probability
        for node in self.__H.nodes.data():
            self.__H.add_node(node[0], status="inactive", prob=p)
        # seed nodes become active
        for seed in seed_nodes:
            self.__H.add_node(seed, status="active")
        # same as ICC
        i = 0
        while not self.__all_nodes_complete() and i < self.__limit:
            for node in self.__active_nodes():
                self.__H.add_node(node, status="used")
                for adj in self.__H.adj[node]:
                    if self.__H.nodes[adj]["status"] == "inactive":
                        probability: float = self.__H.nodes[adj]["prob"]
                        if helper.turn(probability):
                            self.__H.add_node(adj, status="active")
                        else:
                            self.__H.add_node(adj, prob=dec_func(probability))
            i += 1
        return (i, self.__H)

    def run_LTM(
        self, seed_nodes, thres_funct=lambda G, node: random.random()
    ) -> tuple[int, nx.DiGraph]:
        """
        Run a simulation of the linear threshold model on the network.
        :param list seed_nodes: The set of nodes which start in the
        `active` state
        :param lambda thres_funct: A lambda function which gives the
        threshold for a given node, taking in the graph and the specific node
        :return: A tuple in the form `(i, G)`, where `i` is the number of
        iterations before the network could no longer change in influence
        and `G` is the final graph after `i` iterations
        """
        self.__H = self.__G
        number_infected_0 = 0
        number_infected_1 = 0
        if seed_nodes is None or seed_nodes == []:
            print(
                f"""[Linear Threshold Model] on network: 
                {self.__name}. No seed nodes provided. Using 
                Degree Heuristic"""
            )
            seed_nodes = Heuristics.random_h(self.get_nx())

        for node in self.__H.nodes.data():
            self.__H.add_node(
                node[0], status="inactive", prob=thres_funct(self.__H, node)
            )
        for seed in seed_nodes:
            self.__H.add_node(seed, status="active")
            number_infected_0 += 1

        i = 0
        while not self.__all_nodes_complete() and i < 100:
            number_infected_1 = number_infected_0
            i += 1
            for node, data in self.__H.nodes.data():
                if data["status"] == "inactive":
                    # check neighbours for percentage > threshold
                    active_neighbours = 0
                    total_neighbours = 0
                    for adj in self.__H.adj[node]:
                        if self.__H.nodes[adj]["status"] == "active":
                            active_neighbours += 1
                        total_neighbours += 1
                    if (
                        total_neighbours > 0
                        and (active_neighbours / total_neighbours)
                        > self.__H.nodes[node]["prob"]
                    ):
                        self.__H.add_node(node, status="active")
                        number_infected_1 += 1
            if number_infected_1 - number_infected_0 == 0:
                break
            else:
                number_infected_0 = number_infected_1
        return (i, self.__H)

    def __active_nodes(self) -> list:
        active = []
        for n in self.__H.nodes.data():
            if n[1]["status"] == "active":
                active.append(n[0])
        return active

    def eppstein_generator(self, n: int):
        """
        Generate a random graph based on the Eppstein power law generation algorithm.
        :param n int: number of nodes to generate.
        """
        # https://stackoverflow.com/a/68247654
        sequence = []
        while True:
            sequence = sorted(
                [int(round(d)) for d in powerlaw_sequence(n)], reverse=True
            )
            if is_graphical(sequence):
                break
        G = nx.random_degree_sequence_graph(sequence)
        # with this the graph is undirected so add a reverse of each edge
        H: nx.DiGraph = nx.empty_graph(0)
        for u, v in G.edges():
            H.add_edge(u, v)
            H.add_edge(v, u)
        self.__G = H
        self.__H = H

    def kleinbergs_generator(self, n: int):
        """
        Generate a random graph based on the Kleinberg generation algorithm.
        :param n int: number of nodes to generate.
        """
        n = math.floor(n**0.5)
        # based on a square lattice of root n on each side gives n total nodes
        self.__G = nx.navigable_small_world_graph(n)
        self.__H = self.__G

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

    def get_name(self):
        return self.__name

    def __init__(self, name: str, verbose: bool = False) -> None:
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

    def run_ICC_find_min_nodes(
        self, heuristic, target_propogation, quick=False, p=0.1, iteration_limit=None
    ):
        return self.__run_find_min_nodes(
            self.run_ICC, heuristic, target_propogation, quick, p, iteration_limit
        )

    def run_DCC_find_min_nodes(
        self, heuristic, target_propogation, quick=False, p=0.1, iteration_limit=None
    ):
        return self.__run_find_min_nodes(
            self.run_DCC, heuristic, target_propogation, quick, p, iteration_limit
        )

    def run_LTM_find_min_nodes(
        self, heuristic, target_propogation, quick=False, p=0.1, iteration_limit=None
    ):
        return self.__run_find_min_nodes(
            self.run_LTM, heuristic, target_propogation, quick, p, iteration_limit
        )

    def __run_find_min_nodes(
        self,
        model,
        heuristic,
        target_propogation,
        quick=False,
        p=0.1,
        iteration_limit=None,
    ):
        assert type(model).__name__ == "method"
        assert type(heuristic).__name__ == "function"
        assert type(target_propogation) is float or target_propogation == 1
        assert target_propogation >= 0 and target_propogation <= 1
        assert p >= 0 and p <= 1 and type(p) is float
        assert iteration_limit is None or (
            type(iteration_limit) is int and iteration_limit >= 0
        )
        assert type(quick) is bool

        # follow an exponential increase in the number of seed nodes to overshoot target
        # from n_overshoot and n_undershoot perform binary search to find closest right of n
        # n_over = 2*n_under, maximum of n_over is |V| so will binary perform log(V) trials,
        # and on average log(V) to get the detailed point.

        # produce a list [1, 2, 4, 16, ..., |V|]
        seed_numbers = [
            int(math.pow(2, x))
            for x in range(math.floor(math.log(len(self.__G.nodes()))))
        ] + [len(self.__G.nodes())]

        under_index, over_index = 0, 0
        for i, seed_num in enumerate(seed_numbers):
            iters, final = model(heuristic(self.__G, seed_num), p, iteration_limit)
            coverage = len(
                [
                    data
                    for _, data in final.nodes().data()
                    if data["status"] != "inactive"
                ]
            ) / len(list(final.nodes()))
            if coverage >= target_propogation:
                over_index = i
                break

        # in the case the that 1 seed is enough
        if over_index == under_index:
            return seed_numbers[over_index]

        # when want a quick definite bound
        if quick:
            return seed_numbers[over_index]

        inbetween = [
            i for i in range(seed_numbers[under_index], seed_numbers[over_index] + 1, 1)
        ]
        left, right = 0, len(inbetween)
        while left <= right:
            mid = math.floor((left + right) / 2)
            iters, final = self.run_ICC(
                heuristic(self.__G, inbetween[mid]), p, iteration_limit
            )
            coverage = len(
                [
                    data
                    for _, data in final.nodes().data()
                    if data["status"] != "inactive"
                ]
            ) / len(list(final.nodes()))
            if coverage >= target_propogation:
                right = mid - 1
            else:
                left = mid + 1
        return inbetween[right]

    def run_ICC_find_min_nodes(
        self, heuristic, target_propogation, quick=False, p=0.1, iteration_limit=None
    ):
        """
        Find the minimum number of nodes to achieve target_propogation spread using ICC

        :param heuristic: Function used to select seed nodes
        :param target_propogation: Value in range [0, 1] to aim for as overall infection target
        :param quick: Whether to perform BFS between the coarse grained search steps
        :param p: Propogation probability in ICC model.
        :param iteration_limit: Limit to number of iterations of cascade.
        """
        assert type(heuristic).__name__ == "function"
        assert type(target_propogation) is float or target_propogation == 1
        assert target_propogation >= 0 and target_propogation <= 1
        assert p >= 0 and p <= 1 and type(p) is float
        assert iteration_limit is None or (
            type(iteration_limit) is int and iteration_limit >= 0
        )
        assert type(quick) is bool

        # follow an exponential increase in the number of seed nodes to overshoot target
        # from n_overshoot and n_undershoot perform binary search to find closest right of n
        # n_over = 2*n_under, maximum of n_over is |V| so will binary perform log(V) trials,
        # and on average log(V) to get the detailed point.

        # produce a list [1, 2, 4, 16, ..., |V|]
        seed_numbers = [
            int(math.pow(2, x))
            for x in range(math.floor(math.log(len(self.__G.nodes()))))
        ] + [len(self.__G.nodes())]

        under_index, over_index = 0, 0
        for i, seed_num in enumerate(seed_numbers):
            iters, final = self.run_ICC(
                heuristic(self.__G, seed_num), p, iteration_limit
            )
            coverage = len(
                [
                    data
                    for _, data in final.nodes().data()
                    if data["status"] != "inactive"
                ]
            ) / len(list(final.nodes()))
            if coverage >= target_propogation:
                over_index = i
                break

        # in the case the that 1 seed is enough
        if over_index == under_index:
            return seed_numbers[over_index]

        # when want a quick definite bound
        if quick:
            return seed_numbers[over_index]

        inbetween = [
            i for i in range(seed_numbers[under_index], seed_numbers[over_index] + 1, 1)
        ]
        left, right = 0, len(inbetween)
        while left <= right:
            mid = math.floor((left + right) / 2)
            iters, final = self.run_ICC(
                heuristic(self.__G, inbetween[mid]), p, iteration_limit
            )
            coverage = len(
                [
                    data
                    for _, data in final.nodes().data()
                    if data["status"] != "inactive"
                ]
            ) / len(list(final.nodes()))
            if coverage >= target_propogation:
                right = mid - 1
            else:
                left = mid + 1
        return inbetween[right]

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

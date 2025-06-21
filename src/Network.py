import ast
import random
import sqlite3
import uuid

import networkx as nx

from Db import initialise_database
from helper import turn


class Network:
    """
    Network Class: Create, Update, Load, Save networks into a database.
    Run simulations on networks using ICC, DCC and LTM models and utilise
    various heuristics to choose seed nodes
    """

    def __init__(self, project: str, name: str) -> None:
        """
        Initialise a new empty Graph.
        :param str project: Name of Project - links to sqlite file
        :param str name: Name of Network
        """
        self.__network_id: str = str(uuid.uuid4())
        self.__G: nx.DiGraph = nx.empty_graph()
        self.__name: str = name
        self.__limit: int = 10**5  # limit on the number of iterations reached
        con: sqlite3.Connection | None = initialise_database(project)
        if con is not None:
            self.__con: sqlite3.Connection = con

    def save_db(self, verbose=False) -> str:
        """
        Save the network into database. Database file specified when network
        was instanciated.
        :param bool verbose: Default to `False`, adds logging of database
        actions if `True`
        :return str network_id: `str` The unique identifier of the network
        in the database as a string
        """
        edge_list: list[str] = [line for line in nx.generate_edgelist(self.__G)]
        query = """
            insert into networks (id, name, network) values (?, ?, ?);
        """  # id, name, blob
        try:
            cur: sqlite3.Cursor = self.__con.cursor()
            cur.execute(query, (self.__network_id, self.__name, str(edge_list)))
            self.__con.commit()
        except Exception as e:
            print(f"[Network] Error Saving to Database: {e}")
            return ""
        return self.__network_id

    def load_from_db(self, name: str, verbose=False) -> bool:
        """
        Load the a given network from the database by it's name.
        :param str name: Name of network to retrieve
        :param bool verbose: Default to `False`, adds logging of
        database actions if `True`
        :return bool status: `True` if succeeded, `False` if not
        """
        cur: sqlite3.Cursor = self.__con.cursor()
        res: sqlite3.Cursor = cur.execute(
            "select * from networks where name = ?", (name,)
        )
        temp_record = res.fetchone()
        self.__network_id = temp_record[0]
        self.__name = name
        try:
            edges_list: list[str] = ast.literal_eval(temp_record[2])
            edges = []
            for edge in edges_list:
                sp: list[str] = edge.split()
                edges.append((sp[0], sp[1], ast.literal_eval(sp[2])))
            self.__G.add_edges_from(edges)
            if verbose:
                print(
                    f"""[Network Verbose] Loaded {len(self.__G.edges)} 
                    edges into graph"""
                )
        except Exception as e:
            print(f"[Network] Error Occured in Reading file: {e}")
            return False
        return True

    def run_ICC(self, seed_nodes, p: float = 0.5) -> tuple[int, nx.DiGraph]:
        """
        Run a simulation of the independant cascade model on the network.
        :param float p: Probability of a node turning a neighbouring node
        :param list seed_nodes: The set of nodes which start the spread in
        the network
        :return: A tuple in the form `(i, G)`, where `i` is the number of
        iterations before the network could no longer change in influence
        and `G` is the final graph after `i` iterations
        """

        self.H: nx.DiGraph = self.__G

        if seed_nodes is None or seed_nodes == []:
            print(
                f"""[Independant Cascade Model]  on network: {self.__name}. 
                No seed nodes provided. Using Degree Heuristic"""
            )
            seed_nodes = self.deg_h()

        # set all nodes to be inactive
        for v in self.H.nodes.data():
            self.__G.add_node(v[0], status="inactive")
        # set our seed nodes to be active
        for s in seed_nodes:
            self.H.add_node(s[0], status="active")

        i: int = 0
        while not self.__all_nodes_complete() and i < self.__limit:
            for node in self.__active_nodes():
                self.H.add_node(node, status="used")
                for adj in self.H.adj[node]:
                    if turn(p) and self.H.nodes[adj]["status"] == "inactive":
                        self.H.add_node(adj, status="active")
            i += 1
        return (i, self.H)

    def __all_nodes_complete(self) -> bool:
        for n in self.H.nodes.data():
            if n[1]["status"] == "active":
                return False
        return True

    def run_DCC(
        self, seed_nodes, p: float = 0.5, dec_func=lambda x: x * 0.7
    ) -> tuple[int, nx.DiGraph]:
        """
        Run a simulation of the decreasing cascade model on the network.
        :param float p: Probability of a node turning a neighbouring node
        :param list seed_nodes: The set of nodes which start the spread in
        the network
        :param lambda dec_func: A single variable lambda function which
        denotes how the likelyhood of a node being influence changes every
        time it is attempted.
        :return: A tuple in the form `(i, G)`, where `i` is the number of
        iterations before the network could no longer change in influence
        and `G` is the final graph after `i` iterations
        """
        self.H = self.__G

        if seed_nodes is None or seed_nodes == []:
            print(
                f"""[Decreasing Cascade Model] on network: {self.__name}. 
                No seed nodes provided. Using Degree Heuristic"""
            )
            seed_nodes = self.deg_h()

        # all nodes inactive and get a starting probability
        for node in self.H.nodes.data():
            self.H.add_node(node[0], status="inactive", prob=p)
        # seed nodes become active
        for seed in seed_nodes:
            self.H.add_node(seed, status="active")
        # same as ICC
        i = 0
        while not self.__all_nodes_complete() and i < self.__limit:
            for node in self.__active_nodes():
                self.H.add_node(node, status="used")
                for adj in self.H.adj[node]:
                    if self.H.nodes[adj]["status"] == "inactive":
                        probability: float = self.H.nodes[adj]["prob"]
                        if turn(probability):
                            self.H.add_node(adj, status="active")
                        else:
                            self.H.add_node(adj, prob=dec_func(probability))
            i += 1
        return (i, self.H)

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
        self.H = self.__G

        if seed_nodes is None or seed_nodes == []:
            print(
                f"""[Linear Threshold Model] on network: 
                {self.__name}. No seed nodes provided. Using 
                Degree Heuristic"""
            )
            seed_nodes = self.deg_h()

        for node in self.H.nodes.data():
            self.H.add_node(node[0], status="inactive", prob=thres_funct(self.H, node))
        for seed in seed_nodes:
            self.H.add_node(seed, status="active")

        i = 0
        while not self.__all_nodes_complete() and i < self.__limit:
            i += 1
            for node in self.H.nodes.data():
                if node["status"] == "inactive":
                    # check neighbours for percentage > threshold
                    active_neighbours = 0
                    for adj in self.H.adj[node]:
                        if self.H.nodes[adj]["status"] == "active":
                            active_neighbours += 1
                    if (active_neighbours / len(self.H.adj[node])) > self.H.nodes[node][
                        "prob"
                    ]:
                        self.H.add_node(node, status="active")
        return (i, self.H)

    def __active_nodes(self) -> list:
        active = []
        for n in self.H.nodes.data():
            if n[1]["status"] == "active":
                active.append(n[0])
        return active

    def deg_h(self, n: int = 2) -> list:
        """
        Finds the `n` highest degree nodes in the network.

        :param int n: Number of vertices to return
        :return: List of size n of vertices
        """
        nodes = []
        for node in self.__G.nodes():
            nodes.append((self.__G.degree(node), node))  # type: ignore
        nodes.sort(reverse=True)
        return [x[1] for x in nodes[:n]]

    def deg_discount_h(self, n: int = 2) -> list:
        """
        Find n vertices in the graph that satisfy the degree discount heuristic

        Takes the highest degree vertex v from the network, removes it from
        the network (thereby lowering the degree of adj(v)) and continues doing
        this until n vertices are found.

        :param int n: Number of vertices to return
        :return: list of size n of vertices

        """
        if n >= len(self.__G.nodes()):
            return [node for node in self.__G.nodes()]
        H: nx.DiGraph = self.__G
        vertices = []
        while n != 0:
            degrees = H.degree()  # type: ignore
            maximal_deg = max([v for (u, v) in degrees])
            vertex = [u for (u, v) in degrees if v == maximal_deg][0]
            vertices.append(vertex)
            H.remove_node(vertex)
            n -= 1
        return vertices

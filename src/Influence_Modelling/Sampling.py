import random
from random import shuffle
from typing import Any, Set

import networkx as nx


def bfs_sample(G: nx.DiGraph, S, n: int):
    """
    From the set of seed nodes add nodes using bfs until qutoa is reached.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    # early termination when no sample required
    if G.number_of_nodes() <= n:
        return G

    H: nx.DiGraph = nx.empty_graph(0)
    working_set = set()
    while H.number_of_nodes() < n:
        for node in S:
            working_set.add(node)
            for adjacent in G.adj[node]:
                working_set.add(adjacent)
        H.add_nodes_from(working_set)
        S = working_set
    return G.remove_nodes_from([node for node in G.nodes() if node not in H.nodes()])


def snowball_sample(G: nx.DiGraph, S, n: int):
    """
    Following from BFS until quota is reached, if adding another bfs layer
    would put over the quota then a random selection would be added instead.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    # early termination when no sample required
    if G.number_of_nodes() <= n:
        return G

    H: nx.DiGraph = nx.empty_graph(0)
    H.add_nodes_from(S)
    layer: Set[Any] = set()
    while H.number_of_nodes() < n:
        for node in S:
            for adjacent in G.adj[node]:
                layer.add(adjacent)
        if len(layer) > (n - H.number_of_nodes()):
            H.add_nodes_from(random_sample([x for x in layer], n - H.number_of_nodes()))
            return H
        H.add_nodes_from(layer)
        S: Set[Any] = layer
        layer = set()
    return G.remove_nodes_from([node for node in G.nodes() if node not in H.nodes()])


def random_walk_sample(G: nx.DiGraph, S, n: int):
    """
    Nodes are chosen following a random traversal, every node has an equal
    chance of being chosen at each step.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    subgraph_nodes: set[Any] = set()
    for seed in S:
        subgraph_nodes.add(seed)
    layer: set[Any] = subgraph_nodes
    while True:
        layer_walked_one: set[Any] = set()
        for v in layer:
            if len(subgraph_nodes) >= n:
                return G.remove_nodes_from(
                    [node for node in G.nodes() if node not in subgraph_nodes]
                )
            # choose a neighbour of v to go to as the next step of walk
            adj = G.adj[v]
            next = random.choice(adj)
            layer_walked_one.add(next)
        subgraph_nodes.add(layer)
        layer = layer_walked_one


def mhrw_sample(G: nx.DiGraph, S, n: int):
    """
    Metropolis-Hastings Random Walk. A random walk sample with a bias
    towards high degree locations aiming to preserve them inside the sample.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    subgraph_nodes: set[Any] = set()
    for seed in S:
        subgraph_nodes.add(seed)
    explored = subgraph_nodes
    from_explored = set()
    while len(subgraph_nodes) < n:
        for e in explored:
            # choose random neighbour of e based on probability from degrees
            neighbours = G.adj[e]
            samples = []
            for n in neighbours:
                for _ in G.degree(n):  # type: ignore
                    samples.append(n)
            selection = random_sample(samples, 1)[
                0
            ]  # our chose next step based on degree of neighbours
            from_explored.add(selection)
        subgraph_nodes.add(explored)
        explored = from_explored
        from_explored = set()
    return G.remove_nodes_from(
        [node for node in G.nodes() if node not in subgraph_nodes]
    )


def mhda_sample(G: nx.DiGraph, S, n: int):
    """
    Metropolis-Hastings Random Walk With Delayed Acceptance. An extension
    of MHRW with a modification to transition functions to reduce revisiting of
    the same locations.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    subgraph_nodes: set[Any] = set()
    for seed in S:
        subgraph_nodes.add(seed)
    explored = subgraph_nodes
    from_explored = set()
    while len(subgraph_nodes) < n:
        for e in explored:
            # choose random neighbour of e based on probability from degrees
            neighbours = G.adj[e]
            samples = []
            for n in neighbours:
                if n in from_explored or n in explored or n in subgraph_nodes:
                    samples.append(n)
                else:
                    for _ in G.degree(n):  # type: ignore
                        samples.append(n)
            selection = random_sample(samples, 1)[
                0
            ]  # our chose next step based on degree of neighbours
            from_explored.add(selection)
        subgraph_nodes.add(explored)
        explored = from_explored
        from_explored = set()
    return G.remove_nodes_from(
        [node for node in G.nodes() if node not in subgraph_nodes]
    )


def ablatross_sample(G: nx.DiGraph):
    """
    Albatross Sampling. A random walk with an chance to randomly jump to a
    disjoint location within the graph and gain greater coverage of disjoint
    connected components.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    pass


def random_sample(collection: list[Any], n) -> list[Any]:
    if n >= collection:
        return collection
    s: set[Any] = {}  # type: ignore
    while len(s) < n:
        shuffle(collection)
        s.add(collection.pop(0))
    return [x for x in s]

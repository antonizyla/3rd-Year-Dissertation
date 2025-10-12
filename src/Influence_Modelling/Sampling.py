import math
import random
from typing import Any, List, Set

import networkx as nx


def bfs_sample(G: nx.DiGraph, S: List[Any], n: int) -> nx.DiGraph:
    """
    Generate a sample from the set of seed nodes add nodes using bfs until the quota is reached.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    # early termination when no sample required
    if G.number_of_nodes() <= n:
        return G
    if len(S) == 0:  # cannot perform bfs from no start
        return nx.empty_graph()

    H: nx.DiGraph = nx.empty_graph(0)
    working_set = set()
    while H.number_of_nodes() < n:
        for node in S:
            working_set.add(node)
            for adjacent in G.adj[node]:
                working_set.add(adjacent)
        H.add_nodes_from(working_set)
        S = list(working_set)
    return G.subgraph(H.nodes()).copy()


def snowball_sample(G: nx.DiGraph, S: List[Any], n: int) -> nx.DiGraph:
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
            H.add_nodes_from(random.sample(list(layer), n - H.number_of_nodes()))
            break
        H.add_nodes_from(layer)
        S = list(layer)
        layer = set()
    return G.subgraph(H.nodes()).copy()


def random_walk_sample(G: nx.DiGraph, S: List[Any], n: int) -> nx.DiGraph:
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


def mhrw_sample(G: nx.DiGraph, n: int) -> nx.DiGraph:
    """
    Metropolis-Hastings Random Walk. A random walk sample with a bias
    towards high degree locations aiming to preserve them inside the sample.

    :param nx.Digraph G: The graph to be sampled
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    if n >= len(list(G.nodes())):
        return G

    xt = random_element([v for v in G.nodes()])  # generate x_0 in effect
    subgraph_nodes = set()

    while len(subgraph_nodes) < n:
        p = random.random()

        # this turns it into O(n^2) at minimum
        j = random_element([n for n in G.adj[xt] if n not in subgraph_nodes])

        if j is None:
            j = random_element([v for v in G.nodes() if v not in subgraph_nodes])

        if p <= min(1, G.degree(xt) / G.degree(j)):
            xt = j
            subgraph_nodes.add(j)

    return G.subgraph([n for n in subgraph_nodes])


def mhda_sample(G: nx.DiGraph, n: int) -> nx.DiGraph:
    """
    Metropolis-Hastings Random Walk With Delayed Acceptance. An extension
    of MHRW with a modification to transition functions to reduce revisiting of
    the same locations.

    :param nx.Digraph G: The graph to be sampled
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    yt = None
    xt = random_element([v for v in G.nodes()])
    subgraph_nodes = set()
    while len(subgraph_nodes) < n:
        p = random.random()
        i = random_element([n for n in G.adj[xt] if n not in subgraph_nodes])
        if i is None:
            i = random_element([n for n in G.nodes() if n not in subgraph_nodes])
        if p <= min(1, G.degree(xt) / G.degree(i)):
            if yt == i and G.degree(xt) > 1:
                k = random_element([n for n in G.adj[xt] if n is not i])
                q = random.random()
                if q <= min(
                    1,
                    min(1, (G.degree(xt) / G.degree(k)) ** 2)
                    * max(1, (G.degree(i) / G.degree(xt)) ** 2),
                ):
                    yt = xt
                    xt = k
                else:
                    yt = xt
                    xt = i
            else:
                yt = xt
                xt = i
        subgraph_nodes.add(xt)
    return G.subgraph([n for n in subgraph_nodes])


def albatross_sample(G: nx.DiGraph, S: List[Any], n: int) -> nx.DiGraph:
    """
    Albatross Sampling. A random walk with an chance to randomly jump to a
    disjoint location within the graph and gain greater coverage of disjoint
    connected components.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    sample = Set()
    p = 0.02
    sample.add(random_sample(G.nodes(), 1)[0])
    last_added = [v for v in sample][0]
    while len(sample) < n:
        if random.random() < p:
            # choose a random non connected vertex
            available = [v for v in G.nodes() if v not in [u for u in sample]]
            selected = random.shuffle(available).pop(0)
            sample.add(selected)
            last_added = selected
        else:
            # choose edge linked to last_added
            u = last_added
            v = random_sample(G.adj[u], 1).pop(0)
            if random.random() < G.in_degree(u) / G.in_degree(v):
                last_added = v
                sample.add(v)
            else:
                sample.add(u)
    return sample


def albatross_transition_probability(G: nx.DiGraph, u, v) -> float:
    """
    Function for computing the probability of a jump beetween two
    nodes inside of the albatross sampling algorithmn. (I did
    not read the full algorithm and thought this was part of it
    rather than the analysis)

    :param nx.DiGraph G: Graph we reason about.
    :param u: start node.
    :param v: destination node.
    :return: Probability of going to that node.
    """
    p_jump = 0.02  # as given in albatross paper page 5 section 4.1
    m = len([v for v in G.nodes()])  # number of nodes in graph
    # the two are neighbours
    if v in [x for x in G.adj[u]]:
        return (
            min((1 - p_jump) / G.in_degree(u), (1 - p_jump) / G.in_degree(v))
            + p_jump / m
        )
    # the two are the same
    if v is u:
        pairs = [(a, b) for a in G.nodes() for b in G.nodes() if a is not b]
        return (
            1
            - p_jump
            - [
                min((1 - p_jump) / G.in_degree(w), (1 - p_jump) / G.in_degree(u))
                for (w, u) in pairs
            ]
            + p_jump / m
        )
    # the two are disjoint
    return p_jump / m


def random_sample(collection: list[Any], n: int) -> list[Any]:
    if n >= len(collection):
        return collection
    s: set[Any] = set()
    while len(s) < n:
        random.shuffle(collection)
        s.add(collection.pop(0))
    return [x for x in s]


def random_element(xs: list[Any]) -> Any:
    length = len(xs)
    if length <= 0:
        return None
    return xs[math.floor(random.random() * length)]

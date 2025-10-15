import math
import random
from typing import Any, List

import networkx as nx


def bfs_sample(G: nx.DiGraph, n: int) -> nx.DiGraph:
    """
    Generate a sample from the set of seed nodes add nodes using bfs until the quota is
    reached.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    # early termination when no sample required
    if G.number_of_nodes() <= n:
        return G
    subgraph_nodes = set()
    current_layer = [random_element([v for v in G.nodes()])]
    while len(subgraph_nodes) < n:
        for v in current_layer:
            subgraph_nodes.add(v)

        # find the neighbourhood of current layer that's no included already
        neighbours = []
        for c in current_layer:
            for v in G.adj[c]:
                neighbours.append(v)
        current_layer = [v for v in neighbours if v not in subgraph_nodes]
    return G.subgraph([u for u in subgraph_nodes])


def snowball_sample(G: nx.DiGraph, n: int) -> nx.DiGraph:
    """
    Following from BFS until quota is reached, if adding another bfs layer
    would put over the quota then a random selection would be added instead.

    :param nx.Digraph G: The graph to be sampled
    :param S: List of nodes which are our seed nodes
    :param int n: Number of nodes to be selected in our sample.
    :return: Subgraph of G following the algorithm
    """
    if G.number_of_nodes() <= n:
        return G
    subgraph_nodes = set()
    current_layer = [random_element([v for v in G.nodes()])]
    while len(subgraph_nodes) < n:
        for v in current_layer:
            subgraph_nodes.add(v)
            if len(subgraph_nodes) == n:
                return G.subgraph([u for u in subgraph_nodes])

        # find the neighbourhood of current layer that's no included already
        neighbours = []
        for c in current_layer:
            for v in G.adj[c]:
                neighbours.append(v)
        current_layer = [v for v in neighbours if v not in subgraph_nodes]
    return G.subgraph([u for u in subgraph_nodes])


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
    sample = set()
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

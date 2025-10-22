import networkx as nx

from Influence_Modelling import Sampling


def random_h(G, n: int = 2) -> list:
    """
    Find n random nodes in the network.
    """
    return Sampling.random_sample([v for v in G.nodes()], n)


def deg_h(G, n: int = 2) -> list:
    """
    Finds the `n` highest degree nodes in the network.

    :param int n: Number of vertices to return
    :return: List of size n of vertices
    """
    nodes = []
    for node in G.nodes():
        nodes.append((G.degree(node), node))  # type: ignore
    nodes.sort(reverse=True)
    return [x[1] for x in nodes[:n]]


def deg_discount_h(G, n: int = 2) -> list:
    """
    Find n vertices in the graph that satisfy the degree discount heuristic

    Takes the highest degree vertex v from the network, removes it from
    the network (thereby lowering the degree of adj(v)) and continues doing
    this until n vertices are found.

    :param int n: Number of vertices to return
    :return: list of size n of vertices

    """
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    H: nx.DiGraph = G
    vertices = []
    while n != 0:
        degrees = H.degree()
        maximal_deg = max([v for (u, v) in degrees])
        vertex = [u for (u, v) in degrees if v == maximal_deg][0]
        vertices.append(vertex)
        H.remove_node(vertex)
        n -= 1
    return vertices

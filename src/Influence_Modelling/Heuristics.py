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
    H: nx.DiGraph = G.copy()
    vertices = []
    while len(vertices) < n:
        degrees = H.degree()
        maximal_deg = max([degree for (_, degree) in H.degree()])
        vertex = [vertex for (vertex, degree) in degrees if degree == maximal_deg][0]
        vertices.append(vertex)
        H.remove_node(vertex)
    return vertices


def __neighbour_deg(G, node):
    neighbour_degrees = [G.degree(n) for n in G.adj[node]]
    if neighbour_degrees == []:
        return 0
    return sum(neighbour_degrees) / len(neighbour_degrees)


def mean_neighbour_deg_h(G, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    nodes = []
    for node in G.nodes():
        nodes.append((__neighbour_deg(G, node), node))  # type: ignore
    nodes.sort(reverse=True)
    return [x[1] for x in nodes[:n]]


def local_clustering_coefficient_h(G, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.clustering(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def betweenness_centrality_h(G, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.betweenness_centrality(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def average_shortest_path_length_h(G, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.average_shortest_path_length(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def eigenvector_centrality_h(G, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.eigenvector_centrality(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]

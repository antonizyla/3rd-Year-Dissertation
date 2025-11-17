import networkx as nx

from Influence_Modelling import Network, Sampling


def random_h(G: nx.DiGraph, n: int = 2) -> list:
    """
    Find n random nodes in the network.
    """
    return Sampling.random_sample([v for v in G.nodes()], n)


def deg_h(G: nx.DiGraph, n: int = 2) -> list:
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


def deg_discount_h(G: nx.DiGraph, n: int = 2) -> list:
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


def mean_neighbour_deg_h(G: nx.DiGraph, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    nodes = []
    for node in G.nodes():
        nodes.append((__neighbour_deg(G, node), node))  # type: ignore
    nodes.sort(reverse=True)
    return [x[1] for x in nodes[:n]]


def local_clustering_coefficient_h(G: nx.DiGraph, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.clustering(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def betweenness_centrality_h(G: nx.DiGraph, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.betweenness_centrality(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def average_shortest_path_length_h(G: nx.DiGraph, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.average_shortest_path_length(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def eigenvector_centrality_h(G: nx.DiGraph, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.eigenvector_centrality(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def katz_centrality_h(G: nx.DiGraph, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]
    coefficients = nx.katz_centrality_numpy(G)
    node_coefficients = [(coefficients[node], node) for node in G.nodes()]
    node_coefficients.sort(reverse=True)
    return [x[1] for x in node_coefficients[:n]]


def greedy_h(G: nx.DiGraph, n: int = 2) -> list:
    if n >= len(G.nodes()):
        return [node for node in G.nodes()]

    net = Network.Network("", "")
    net.set_nx(G)

    seeds = [node for node in G.nodes()]
    for i in range(len(seeds)):
        _, final = net.run_ICC([seeds[i], 0.1, 10000])
        seeds[i] = (
            len(
                [
                    data
                    for _, data in final.nodes().data()
                    if data["status"] != "inactive"
                ]
            )
            / len(list(final.nodes())),
            seeds[i],
        )

    seeds.sort(reverse=True)
    return [seed for (_, seed) in seeds[0:n]]


def celf_h(G: nx.DiGraph, n: int = 2) -> list:
    marginal_gain = []
    nodes = [v for v in G.nodes()]
    net = Network.Network("", "")
    net.set_nx(G)
    for node in nodes:
        iterations, final = net.run_ICC([node], 0.1, 100)
        marginal_gain.append(
            (
                len(
                    [
                        x
                        for (x, data) in final.nodes().data()
                        if data["status"] == "used"
                    ]
                ),
                node,
            )
        )

    marginal_gain.sort(reverse=False)
    Q = marginal_gain
    seeds = [Q[0]]
    spread = seeds[0][0]
    Q.pop(0)  # remove the first item as it's in the list

    for _ in range(n - 1):
        check = False
        while not check:
            current = Q[0][1]
            i, f = net.run_ICC(seeds + [current], 0.1, 100)
            f_spread = len(
                [x for (x, data) in f.nodes().data() if data["status"] == "used"]
            )
            Q[0] = (f_spread - spread, Q[0][1])
            Q.sort(reverse=True)
            check: bool = Q[0][1] == current

        spread += Q[0][0]
        seeds.append(Q[0])
        Q = Q[1:]

    return [seed for (_, seed) in seeds]

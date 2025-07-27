import networkx as nx


def s_1_number_nodes(G: nx.DiGraph):
    return len(list(G.nodes()))


def s_2_number_edges(G: nx.DiGraph):
    return len(list(G.edges()))


def s_3_mean_degree(G: nx.DiGraph):
    degrees = [G.degree(v) for v in [u for u in G.nodes()]]
    return sum(degrees) / len(degrees)


def s_4_clustering_coefficient(G: nx.DiGraph):
    return nx.average_clustering(G)


def s_5_diameter(G: nx.DiGraph):
    return nx.diameter(G)


def s_6_centralization(G: nx.DiGraph):
    return max_degree(G) / s_2_number_edges(G) - density(G)


def density(G):
    return s_3_mean_degree(G) / (s_1_number_nodes(G) - 1)


def max_degree(G):
    return max([G.degree(v) for v in G.nodes()])

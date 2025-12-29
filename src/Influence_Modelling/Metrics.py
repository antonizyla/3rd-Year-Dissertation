import networkx as nx
import pandas as pd

from Influence_Modelling import Network


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


def generate_tabular_row(G: Network.Network | nx.DiGraph) -> pd.DataFrame:
    g = G.get_nx() if isinstance(G, Network.Network) else G
    result = [
        [
            s_1_number_nodes(g),
            s_2_number_edges(g),
            s_3_mean_degree(g),
            s_4_clustering_coefficient(g),
            s_5_diameter(g),
            s_6_centralization(g),
        ]
    ]
    columns: list[str] = [
        "Nodes",
        "Edges",
        "Mean Degree",
        "Clustering Coef.",
        "Diameter",
        "Centralization",
    ]
    if isinstance(G, Network.Network):
        result[0] = [G.get_name(), *result[0]]
        columns = ["Name", *columns]
    return pd.DataFrame(result, columns=columns)

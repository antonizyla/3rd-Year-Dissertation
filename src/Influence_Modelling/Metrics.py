import networkx as nx
import numpy as np
import pandas as pd

from Influence_Modelling import Network


def s_1_number_nodes(G: nx.DiGraph):
    """
    Docstring for s_1_number_nodes

    :param G: Description
    :type G: nx.DiGraph
    """
    return len(list(G.nodes()))


def s_2_number_edges(G: nx.DiGraph):
    """
    Docstring for s_2_number_edges

    :param G: Description
    :type G: nx.DiGraph
    """
    return len(list(G.edges()))


def s_3_mean_degree(G: nx.DiGraph):
    """
    Docstring for s_3_mean_degree

    :param G: Description
    :type G: nx.DiGraph
    """
    degrees = [G.degree(v) for v in [u for u in G.nodes()]]
    if len(degrees) == 0:
        return np.nan
    return sum(degrees) / len(degrees)


def s_4_clustering_coefficient(G: nx.DiGraph):
    """
    Docstring for s_4_clustering_coefficient

    :param G: Description
    :type G: nx.DiGraph
    """
    return nx.average_clustering(G)


def s_5_diameter(G: nx.DiGraph):
    """
    Docstring for s_5_diameter

    :param G: Description
    :type G: nx.DiGraph
    """

    max_dist = 0
    for source in G.nodes:
        lengths = nx.single_source_shortest_path_length(G, source)
        if lengths:
            max_dist = max(max_dist, max(lengths.values()))
    return max_dist


def s_6_centralization(G: nx.DiGraph):
    """
    Docstring for s_6_centralization

    :param G: Description
    :type G: nx.DiGraph
    """
    num_edges = s_2_number_edges(G)
    dens = density(G)
    if np.isnan(num_edges) or np.isnan(dens):
        print("S_6 Centralization Calc: Division by 0 -> Returning NaN")
        return np.nan
    return max_degree(G) / num_edges - density(G)


def density(G):
    """
    Docstring for density

    :param G: Description
    """
    nodes = s_1_number_nodes(G)
    if nodes == 1:
        print("Density Calc: Division by 0 -> Returning NaN")
        return np.nan
    return s_3_mean_degree(G) / (s_1_number_nodes(G) - 1)


def max_degree(G):
    """
    Docstring for max_degree

    :param G: Description
    """
    degs = [G.degree(v) for v in G.nodes()]
    if len(degs) == 0:
        print("Max Degree Calculation: Empty Array -> Returning 0")
        return 0
    return max(degs)


def generate_tabular_row(G: Network.Network | nx.DiGraph) -> pd.DataFrame:
    """
    For a given network generate a 1 row pandas dataframe with it's key features.

    :param G: Description
    :type G: Network.Network | nx.DiGraph
    :return: Description
    :rtype: DataFrame
    """
    assert G is not None

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


def combine_rows(rows: list[pd.DataFrame]):
    """
    Turn multiple samples data about a network into a single row.

    :param rows: Description
    :type rows: list[pd.DataFrame]
    """
    assert len(rows) >= 1

import networkx as nx

from Influence_Modelling.Sampling import bfs_sample


def test_bfs_no_seeds():
    sample = bfs_sample(nx.petersen_graph(), [], 2)
    assert sample.nodes() == nx.empty_graph().nodes()


def test_bfs_too_many_seeds():
    sample = bfs_sample(nx.empty_graph(), [1], 2)
    assert sample.nodes() == nx.empty_graph().nodes()


def test_bfs_close_seeds():
    G: nx.DiGraph = nx.empty_graph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (2, 1), (1, 3), (3, 1)])

    sample = bfs_sample(G, [1], 3)
    assert sample.nodes() == G.nodes()


def test_bfs_disjoint_components():
    G: nx.DiGraph = nx.empty_graph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (2, 1), (1, 3), (3, 1)])
    G.add_nodes_from([11, 12, 13])
    G.add_edges_from([(11, 12), (12, 11), (11, 13), (13, 11)])

    sample = bfs_sample(G, [1, 11], 6)
    assert sample.nodes() == G.nodes()


def test_bfs_unreacheable():
    G: nx.DiGraph = nx.empty_graph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (3, 1)])

    sample: nx.DiGraph = bfs_sample(G, [1], 2)
    sample.nodes()
    assert False


def test_bfs_layer_sizing():
    G: nx.DiGraph = nx.empty_graph()
    G.add_nodes_from([1, 2, 3, 4, 5])
    G.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 5)])

    sample = bfs_sample(G, [1], 4)
    assert len(sample) == 5

import networkx as nx

from Influence_Modelling.Sampling import snowball_sample


def test_snowball_no_seeds():
    sample = snowball_sample(nx.petersen_graph(), [], 2)
    assert sample.nodes() == nx.empty_graph().nodes()


def test_snowball_too_many_seeds():
    sample = snowball_sample(nx.empty_graph(), [1], 2)
    assert sample.nodes() == nx.empty_graph().nodes()


def test_snowball_close_seeds():
    G: nx.DiGraph = nx.empty_graph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (2, 1), (1, 3), (3, 1)])

    sample = snowball_sample(G, [1], 3)
    assert sample.nodes() == G.nodes()


def test_snowball_unreachable():
    G: nx.DiGraph = nx.empty_graph()
    G.add_nodes_from([1, 2, 3])
    G.add_edges_from([(1, 2), (3, 1)])

    sample: nx.DiGraph = snowball_sample(G, [1], 2)
    sample.nodes()
    assert False

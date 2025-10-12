from multiprocessing import Process, Manager
import networkx as nx
import pandas as pd
from Influence_Modelling import NetworkMetrics, Sampling, XsvNetwork

def single_run(G: nx.DiGraph, sampling_method, results, nodes: int = 1000):
    sample: nx.DiGraph = nx.empty_graph()
    if sampling_method is None:
        sample = G
    else:
        sample = sampling_method(G, nodes)
    results.append(
        pd.DataFrame(
            data={
                "nodes": [NetworkMetrics.s_1_number_nodes(sample)],
                "edges": [NetworkMetrics.s_2_number_edges(sample)],
                "mean_degree": [NetworkMetrics.s_3_mean_degree(sample)],
                "cc": [NetworkMetrics.s_4_clustering_coefficient(sample)],
                "centralization": [NetworkMetrics.s_6_centralization(sample)],
                # "diameter": NetworkMetrics.s_5_diameter(sample),
            }
        )
    )


def repeats(G, label, method, trials, nodes, results):
    with Manager() as manager:
        r = manager.list()

        processes = [
            Process(target=single_run, args=(G, method, r, nodes))
            for _ in range(trials)
        ]
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        df = pd.concat(r)
        df.columns = ["nodes", "edges", "mean_degree", "cc", "centralization"]
        results.append(
            pd.DataFrame(
                data={
                    "method": [label],
                    "nodes": [df["nodes"].to_numpy().mean()],
                    "nodes_std": [df["nodes"].to_numpy().std()],
                    "edges": [df["edges"].to_numpy().mean()],
                    "edges_std": [df["edges"].to_numpy().std()],
                    "mean_degree": [df["mean_degree"].to_numpy().mean()],
                    "mean_degree_std": [df["mean_degree"].to_numpy().std()],
                    "cc": [df["cc"].to_numpy().mean()],
                    "cc_std": [df["cc"].to_numpy().std()],
                    "centralization": [df["centralization"].to_numpy().mean()],
                    "centralization_std": [df["centralization"].to_numpy().std()],
                    # "diameter": [df["diameter"].to_numpy().std],
                    # "diameter_std": [df["diameter"].to_numpy().std],
                }
            )
        )

if __name__ == "__main__":
    enron_data = XsvNetwork.XsvNetwork("", "", "enron")
    enron_network = enron_data.get_nx()
    trials = 15
    nodes = 1000


    methods = [
        ("None", None),
        # ("BFS", Sampling.bfs_sample),
        # ("SNS", Sampling.snowball_sample),
        # ("RW", Sampling.random_walk_sample),
        ("MHRW", Sampling.mhrw_sample),
        ("MHDA", Sampling.mhda_sample),
        # ("Albatross", Sampling.albatross_sample),
    ]

    with Manager() as m:
        results = m.list()

        for label, method in methods:
            repeats(enron_network, label, method, trials, nodes, results)
        print(pd.concat(results))

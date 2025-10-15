from multiprocessing import Process, Manager
import time
import networkx as nx
import gc
import resource
import pandas as pd
from Influence_Modelling import NetworkMetrics, Sampling, XsvNetwork


def single_run(G: nx.DiGraph, sampling_method, results, nodes: int = 1000):
    gc.disable()
    memory_start: resource.struct_rusage = resource.getrusage(resource.RUSAGE_SELF)
    start_time = time.time_ns()
    sample: nx.DiGraph = nx.empty_graph()
    if sampling_method is None:
        sample = G
    else:
        sample = sampling_method(G, nodes)
    result = pd.DataFrame(
            data={
                "nodes": [NetworkMetrics.s_1_number_nodes(sample)],
                "edges": [NetworkMetrics.s_2_number_edges(sample)],
                "mean_degree": [NetworkMetrics.s_3_mean_degree(sample)],
                "cc": [NetworkMetrics.s_4_clustering_coefficient(sample)],
                "centralization": [NetworkMetrics.s_6_centralization(sample)],
                # "diameter": NetworkMetrics.s_5_diameter(sample),
            }
        )
    memory_end: resource.struct_rusage = resource.getrusage(resource.RUSAGE_SELF)
    gc.enable()
    end_time = time.time_ns()
    result['time_taken'] = end_time - start_time
    result['maximum_memory'] = memory_end.ru_maxrss - memory_start.ru_maxrss
    results.append(result)


def repeats(G, label, method, trials, nodes, results):
    with Manager() as manager:
        r = manager.list()
        if method is None:
            trials = 1
        processes = [
            Process(target=single_run, args=(G, method, r, nodes))
            for _ in range(trials)
        ]
        for p in processes:
            p.start()
        for p in processes:
            p.join()

        print("Completed " + label + "for ")

        df = pd.concat(r)
        df.columns = ["nodes", "edges", "mean_degree", "cc", "centralization", "time_taken", "maximum_memory"]
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
                    "time_taken_ns": [df['time_taken'].to_numpy().mean()],
                    "time_taken_std_ns": [df['time_taken'].to_numpy().std()],
                    "maximum_memory_kb": [df['maximum_memory'].to_numpy().mean()],
                    "maximum_memory_std_kb": [df['maximum_memory'].to_numpy().std()]
                }
            )
        )


if __name__ == "__main__":
    enron_data = XsvNetwork.XsvNetwork("", "", "enron")
    enron_network = enron_data.get_nx()
    twitter_data = XsvNetwork.XsvNetwork("", "", "twitter")
    twitter_network = twitter_data.get_nx()
    p2p_data = XsvNetwork.XsvNetwork("", "", "p2p")
    p2p_network = p2p_data.get_nx()

    trials = 5
    nodes = 100

    methods = [
        ("None", None),
        ("BFS", Sampling.bfs_sample),
        ("SNS", Sampling.snowball_sample),
        # ("RW", Sampling.random_walk_sample),
        ("MHRW", Sampling.mhrw_sample),
        ("MHDA", Sampling.mhda_sample),
        # ("Albatross", Sampling.albatross_sample),
    ]

    with Manager() as m:
        enron_results = m.list()
        #twitter_results = m.list()
        p2p_results = m.list()

        # for label, method in methods:
        #    repeats(enron_network, label, method, trials, nodes, enron_results)
        #    repeats(twitter_network, label, method, trials, nodes, twitter_results)
        #    repeats(p2p_network, label, method, trials, nodes, p2p_results)

        enron_processes = [
            Process(
                target=repeats,
                args=(enron_network, label, method, trials, nodes, enron_results),
            )
            for label, method in methods
        ]
        #twitter_processes = [
        #    Process(
        #        target=repeats,
        #        args=(twitter_network, label, method, trials, nodes, twitter_results),
        #    )
        #    for label, method in methods
        #]
        p2p_processes = [
            Process(
                target=repeats,
                args=(p2p_network, label, method, trials, nodes, p2p_results),
            )
            for label, method in methods
        ]
        all_procs = enron_processes + p2p_processes 

        for p in all_procs:
            p.start()
        for p in all_procs:
            p.join()

        print("Enron Dataset")
        print(pd.concat(enron_results))
        #print("Twitter Dataset")
        #print(pd.concat(twitter_results))
        print("P2P Dataset")
        print(pd.concat(p2p_results))

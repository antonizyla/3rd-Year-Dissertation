import gc
import math
import multiprocessing
import random
import resource
import time
from multiprocessing import Pool

import networkx as nx
import pandas as pd

from Influence_Modelling import NetworkMetrics, Sampling, XsvNetwork


def concatenate_individual_runs(rows: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(
        data={
            "dataset": [rows["dataset"].to_string().split(" ")[-1]],
            "method": [rows["method"].to_string().split(" ")[-1]],
            "nodes": [rows["nodes"].to_numpy().mean()],
            "nodes_std": [rows["nodes"].to_numpy().std()],
            "edges": [rows["edges"].to_numpy().mean()],
            "edges_std": [rows["edges"].to_numpy().std()],
            "mean_degree": [rows["mean_degree"].to_numpy().mean()],
            "mean_degree_std": [rows["mean_degree"].to_numpy().std()],
            "cc": [rows["cc"].to_numpy().mean()],
            "cc_std": [rows["cc"].to_numpy().std()],
            "centralization": [rows["centralization"].to_numpy().mean()],
            "centralization_std": [rows["centralization"].to_numpy().std()],
            # "diameter": [df["diameter"].to_numpy().std],
            # "diameter_std": [df["diameter"].to_numpy().std],
            "time_taken_ns": [rows["time_taken"].to_numpy().mean()],
            "time_taken_std_ns": [rows["time_taken"].to_numpy().std()],
            "maximum_memory_kb": [rows["maximum_memory"].to_numpy().mean()],
            "maximum_memory_std_kb": [rows["maximum_memory"].to_numpy().std()],
        }
    )
    print(f"Concatenating {df['dataset']}: {df['method']}")
    return df 


def single_row(
    dataset_name, dataset_network, method_name, method_function, nodes
) -> pd.DataFrame:
    gc.disable()
    memory_start: resource.struct_rusage = resource.getrusage(resource.RUSAGE_SELF)
    start_time = time.time_ns()
    sample: nx.DiGraph = nx.empty_graph()
    if method_function is None:
        sample = dataset_network
    else:
        sample = method_function(dataset_network, nodes)
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
    result["time_taken"] = end_time - start_time
    result["maximum_memory"] = memory_end.ru_maxrss - memory_start.ru_maxrss
    result["dataset"] = dataset_name
    result["method"] = method_name
    print(f"Completed a trial of {dataset_name}: {method_name}")
    return result


if __name__ == "__main__":
    pd.options.display.max_columns = None
    pd.options.display.max_rows = None
    pd.options.display.expand_frame_repr = False

    # Set all parameters here
    trials: int = 2
    nodes: int = 100
    threads: int = 40

    output_file_path: str = f"sampling_results{math.floor(random.random() * 1000)}.txt"

    enron_data = XsvNetwork.XsvNetwork("", "", "enron")
    twitter_data = XsvNetwork.XsvNetwork("", "", "twitter")
    p2p_data = XsvNetwork.XsvNetwork("", "", "p2p")
    datasets = [
        ("Enron", enron_data.get_nx()),
        #("Twitter", twitter_data.get_nx()),
        # ("P2P", p2p_data.get_nx()),
    ]

    methods = [
        ("None", None),
        ("BFS", Sampling.bfs_sample),
        # ("SNS", Sampling.snowball_sample),
        # ("RW", Sampling.random_walk_sample),
        ("MHRW", Sampling.mhrw_sample),
        ("MHDA", Sampling.mhda_sample),
        # ("Albatross", Sampling.albatross_sample),
    ]

    runs = []
    p = Pool(threads)

    for dataset_name, dataset_network in datasets:
        for method_name, method_function in methods:
            for _ in range(trials):
                runs.append(
                    (dataset_name, dataset_network, method_name, method_function, nodes)
                )

    rows = []
    all_rows = p.starmap(single_row, runs)

    # take mean and std dev of each combo of dataset and sample method
    df = pd.concat(all_rows)
    compressed = pd.DataFrame()
    concatenated = pd.DataFrame()
    for method_name, _ in methods:
        for dataset_name, _ in datasets:
            concatenated = pd.concat(
                [
                    concatenate_individual_runs(
                        df[
                            (df["method"] == method_name)
                            & 
                            (df["dataset"] == dataset_name)
                        ]
                    ),
                    concatenated,
                ]
            )

    # create a list of dataframes that are for each dataset
    tables = []
    for dataset_name, _ in datasets:
        tables.append(concatenated[concatenated["dataset"] == dataset_name])

    print(len(tables))
    for table in tables:
        print(table)

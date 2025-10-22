import argparse
import gc
import os
import pickle
import resource
import time
from multiprocessing import Pool

import networkx as nx
import pandas as pd
import logging

from Influence_Modelling import NetworkMetrics, Sampling, XsvNetwork

output_folder_path: str = ""
logger = logging.getLogger(__name__)
logging.basicConfig(filename="example.log", encoding="utf-8", level=logging.DEBUG)


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
    filepath = f"{output_folder_path}/Concatenated-{df['dataset'].to_string().split(' ')[0]}-{df['method'].to_string().split(' ')[0]}-{df['nodes'].to_string().split(' ')[0]}.pickle"
    with open(filepath, "wb") as handle:
        pickle.dump(df, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(
            f"Completed Concatenation of {df['dataset'].to_string().split(' ')[0]} using {df['method'].to_string().split(' ')[0]} and saved to `{filepath}`"
        )
    return df


def single_row(
    dataset_name: str,
    dataset_network: nx.DiGraph,
    method_name: str,
    method_function,
    nodes: int,
    trial: int,
) -> pd.DataFrame:
    memory_start: resource.struct_rusage = resource.getrusage(resource.RUSAGE_SELF)
    start_time: int = time.time_ns()
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
    end_time: int = time.time_ns()
    result["time_taken"] = end_time - start_time
    result["maximum_memory"] = memory_end.ru_maxrss - memory_start.ru_maxrss
    result["dataset"] = dataset_name
    result["method"] = method_name
    filepath: str = (
        f"{output_folder_path}/{dataset_name}-{method_name}-{nodes}-{trial}.pickle"
    )
    with open(filepath, "wb") as handle:
        pickle.dump(result, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(
            f"""Completed a trial of {dataset_name}: {method_name} and saved to file at `{filepath}`"""
        )
    return result


if __name__ == "__main__":
    pd.options.display.max_columns = None
    pd.options.display.max_rows = None
    pd.options.display.expand_frame_repr = False

    parser = argparse.ArgumentParser("python sampling.py")
    parser.add_argument(
        "--output_location",
        "-o",
        "-o",
        help="Folder to output all intermediate data. Default will be to create a folder called log.",
        type=str,
        default="log",
    )
    parser.add_argument(
        "--processes",
        "-p",
        help="Number of processes to use. Should be set to double the number of physical cpu cores.",
        type=int,
        default=16,
    )
    parser.add_argument(
        "--nodes",
        "-n",
        help="The number of nodes to sample from each dataset, a good starting point is 1000.",
        type=int,
        default=1000,
    )
    parser.add_argument(
        "--trials",
        "-t",
        help="The number of times to repeat each sample and average the results from, a good starting point is 15.",
        type=int,
        default=15,
    )
    args = parser.parse_args()

    # create the intermediate output folder
    output_folder_path = args.output_location
    if not os.path.exists(args.output_location):
        os.makedirs(args.output_location)
    threads = args.processes
    trials = args.trials
    nodes = args.nodes
    logfile = f"{output_folder_path}/log.txt"
    logging.basicConfig(filename=logfile, encoding="utf-8", level=logging.DEBUG)

    enron_data = XsvNetwork.XsvNetwork("", "", "enron")
    twitter_data = XsvNetwork.XsvNetwork("", "", "twitter")
    p2p_data = XsvNetwork.XsvNetwork("", "", "p2p")

    # THIS IS BIT TO EDIT
    #########################################################################
    datasets = [
        ("Enron", enron_data.get_nx()),
        # ("Twitter", twitter_data.get_nx()),
        # ("P2P", p2p_data.get_nx()),
    ]
    methods = [
        ("None", None),
        # ("BFS", Sampling.bfs_sample),
        # ("SNS", Sampling.snowball_sample),
        # ("RW", Sampling.random_walk_sample),
        # ("MHRW", Sampling.mhrw_sample),
        ("MHDA", Sampling.mhda_sample),
        # ("Albatross", Sampling.albatross_sample),
    ]
    ##########################################################################

    runs = []
    p = Pool(threads)

    for dataset_name, dataset_network in datasets:
        for method_name, method_function in methods:
            if method_function is None:
                runs.append(
                    (
                        dataset_name,
                        dataset_network,
                        method_name,
                        method_function,
                        nodes,
                        0,
                    )
                )
            else:
                for trial in range(trials):
                    runs.append(
                        (
                            dataset_name,
                            dataset_network,
                            method_name,
                            method_function,
                            nodes,
                            trial,
                        )
                    )

    rows = []
    all_rows = p.starmap(single_row, runs)

    # take mean and std dev of each combo of dataset and sample method
    df = pd.concat(all_rows)
    concatenated = pd.DataFrame()
    for method_name, _ in methods:
        for dataset_name, _ in datasets:
            concatenated = pd.concat(
                [
                    concatenate_individual_runs(
                        df[
                            (df["method"] == method_name)
                            & (df["dataset"] == dataset_name)
                        ]
                    ),
                    concatenated,
                ]
            )

    # create a list of dataframes that are for each dataset
    tables = []
    for dataset_name, _ in datasets:
        tables.append(concatenated[concatenated["dataset"] == dataset_name])
        filepath = (
            f"{output_folder_path}/Compiled-{dataset_name}-{nodes}n-{trials}t.pickle"
        )
        with open(filepath, "wb") as handle:
            pickle.dump(tables[-1], handle, protocol=pickle.HIGHEST_PROTOCOL)
            logger.debug(
                f"Saved Compiled Table for {dataset_name} to file `{filepath}`"
            )

    for table in tables:
        print(table)

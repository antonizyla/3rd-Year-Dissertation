import argparse
import os
import pickle
import time
from multiprocessing import Pool

import networkx as nx
import pandas as pd

from Influence_Modelling import Heuristics, Network, Sampling, XsvNetwork

output_folder_path = ""


def single_run_ltm(
    dataset_name: str,
    network: nx.DiGraph,
    heuristic_name: str,
    heuristic_method,
    seed_size: int,
    maximum_iterations: int,
    trial: int,
    sampling_function,
    sample_size: int,
):
    start_time = time.time_ns()

    if sampling_function is not None and sample_size is not None:
        network = sampling_function(network, sample_size)

    seeds = heuristic_method(network, seed_size)
    start_coverage = seed_size / len(list(network.nodes()))
    N = Network.Network("", "", False)
    N.set_nx(network)
    iterations, final = N.run_LTM(seeds)
    end_coverage = len(
        [data for _, data in final.nodes().data() if data["status"] != "inactive"]
    ) / len(list(final.nodes()))
    end_time = time.time_ns()
    result = pd.DataFrame(
        data=[
            [
                dataset_name,
                heuristic_name,
                seed_size,
                start_coverage,
                end_coverage,
                iterations,
                end_time - start_time,
                len(
                    [
                        node
                        for (node, data) in final.nodes().data()
                        if data["status"] == "active"
                    ]
                ),
                len(
                    [
                        node
                        for (node, data) in final.nodes().data()
                        if data["status"] == "inactive"
                    ]
                ),
                len(
                    [
                        node
                        for (node, data) in final.nodes().data()
                        if data["status"] == "active"
                    ]
                ),
            ]
        ],
        columns=[
            "dataset",
            "heuristic",
            "n",
            "start_coverage",
            "end_coverage",
            "iterations",
            "time_taken_ns",
            "active_nodes",
            "inactive_nodes",
            "used_nodes",
        ],
    )
    filepath: str = (
        f"{output_folder_path}/LTM-{heuristic_name}-{seed_size}-{trial}.pickle"
    )
    with open(filepath, "wb") as handle:
        pickle.dump(result, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(
            f"""Completed a trial of {heuristic_name} and saved to file at `{filepath}`"""
        )
    return result


def concatenate_individual_runs(rows: pd.DataFrame) -> pd.DataFrame:
    # columns=["heuristic", "n", "start_coverage", "end_coverage", "iterations"],
    df = pd.DataFrame.from_dict(
        data={
            "dataset": [rows["dataset"].to_string().split(" ")[-1]],
            "heuristic": [rows["heuristic"].to_string().split(" ")[-1]],
            "n": [rows["n"].to_string().split(" ")[-1]],
            "start_coverage": [rows["start_coverage"].to_numpy().mean()],
            "start_coverage_std": [rows["start_coverage"].to_numpy().std()],
            "end_coverage": [rows["end_coverage"].to_numpy().mean()],
            "end_coverage_std": [rows["end_coverage"].to_numpy().std()],
            "iterations": [rows["iterations"].to_numpy().mean()],
            "iterations_std": [rows["iterations"].to_numpy().std()],
            "time_taken_ns": [rows["time_taken_ns"].to_numpy().mean()],
            "time_taken_std_ns": [rows["time_taken_ns"].to_numpy().std()],
            "number_rows": [len(rows)],
            "infected_nodes": [rows["used_nodes"].mean()],
            "infected_nodes_std": [rows["used_nodes"].std()],
        }
    )
    heuristic_name = df["heuristic"][0]
    seed_size = df["n"][0]
    filepath: str = (
        f"{output_folder_path}/Concatenated-LTM-{heuristic_name}-{seed_size}.pickle"
    )
    with open(filepath, "wb") as handle:
        pickle.dump(df, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(
            f"Completed Concatenation of {heuristic_name} with {seed_size} seeds and saved to `{filepath}`"
        )
    return df


if __name__ == "__main__":
    pd.options.display.max_columns = None
    pd.options.display.max_rows = None
    pd.options.display.expand_frame_repr = False

    parser = argparse.ArgumentParser("python linear_threshold.py")
    parser.add_argument(
        "--output_location",
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
        "--trials",
        "-t",
        help="The number of times to repeat each sample and average the results from, a good starting point is 30.",
        type=int,
        default=30,
    )
    args = parser.parse_args()

    # create the intermediate output folder
    output_folder_path = args.output_location
    if not os.path.exists(args.output_location):
        os.makedirs(args.output_location)
    threads = args.processes
    trials = args.trials
    logfile = f"{output_folder_path}/log.txt"

    enron_data = XsvNetwork.XsvNetwork("", "", "enron")

    # THIS IS THE BIT TO EDIT
    ################################################################################
    datasets = [
        # (Label, Networkx Datastructure, Sampling Method, number of nodes to sample)
        ("Enron-MHDA-4096", enron_data.get_nx(), Sampling.mhda_sample, 4096),
        ("Enron-MHDA-1024", enron_data.get_nx(), Sampling.mhda_sample, 1024),
        # ("Enron-MHRW-1024", enron_data.get_nx(), Sampling.mhrw_sample, 1024),
    ]

    heuristics = [
        ("Random", Heuristics.random_h),
        ("Degree", Heuristics.deg_h),
        ("Discount", Heuristics.deg_discount_h),
        ("Neighbour", Heuristics.mean_neighbour_deg_h),
        ("Betweeeness", Heuristics.betweenness_centrality_h),
        ("LocalClustering", Heuristics.local_clustering_coefficient_h),
        # (Name, Function)
    ]

    seed_sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    #################################################################################

    runs = []
    p = Pool(threads)

    for dataset_name, dataset_network, sampling_method, sample_size in datasets:
        for heuristic_name, heuristic_function in heuristics:
            for seed_size in seed_sizes:
                for trial in range(trials):
                    runs.append(
                        (
                            dataset_name,
                            dataset_network,
                            heuristic_name,
                            heuristic_function,
                            seed_size,
                            1000,
                            trial,
                            sampling_method,
                            sample_size,
                        )
                    )

    rows = []
    all_rows = p.starmap(single_run_ltm, runs)

    # take mean and std dev of each combo of dataset and sample method
    df = pd.concat(all_rows)
    concatenated = pd.DataFrame()
    for heuristic_name, _ in heuristics:
        for dataset_name, _, _, _ in datasets:
            for seed_size in seed_sizes:
                concatenated = pd.concat(
                    [
                        concatenate_individual_runs(
                            df[
                                (df["heuristic"] == heuristic_name)
                                & (df["dataset"] == dataset_name)
                                & (df["n"] == seed_size)
                            ]
                        ),
                        concatenated,
                    ]
                )

    print(concatenated)
    filepath = f"{output_folder_path}/Concatenated-Individual-Runs-LTM.pickle"
    with open(filepath, "wb") as handle:
        pickle.dump(concatenated, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"Completed Concatenation LTM runs and saved to `{filepath}`")

    datasets = concatenated["dataset"].unique()
    heuristics = concatenated["heuristic"].unique()

    tables = []
    for dataset in datasets:
        for heuristic in heuristics:
            table = concatenated[
                (concatenated["dataset"] == dataset)
                & (concatenated["heuristic"] == heuristic)
            ]
            tables.append(table)
            print(table)
            filepath = f"{output_folder_path}/Compiled-LTM-{dataset}-{heuristic}.pickle"
            with open(filepath, "wb") as handle:
                pickle.dump(table, handle, protocol=pickle.HIGHEST_PROTOCOL)

    filepath = f"{output_folder_path}/All-LTM-Compiled-Tables.pickle"
    with open(filepath, "wb") as handle:
        pickle.dump(tables, handle, protocol=pickle.HIGHEST_PROTOCOL)

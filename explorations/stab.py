import argparse
import math
import os
import pickle
import random
import time
from multiprocessing import Pool

import networkx as nx
import numpy as np
import pandas as pd

from Influence_Modelling import Heuristics, Network, Sampling, XsvNetwork

output_folder_path = ""


class CelfHeuristic:
    def __init__(self, p: float = 0.1, q: float = 0.7, model: str = "ICC"):
        self.p = p
        self.q = q
        self.model = model

    def __call__(self, G: nx.DiGraph, n: int = 2) -> list:
        marginal_gain = []
        nodes = [v for v in G.nodes()]
        net = Network.Network("")
        net.set_nx(G)

        for node in nodes:
            if self.model == "ICC":
                _, final, _ = net.run_ICC([node], self.p, 100)
            elif self.model == "DCC":
                _, final = net.run_DCC([node], p=self.p, dec_func=lambda x: x * self.q)
            elif self.model == "LTM":
                _, final = net.run_LTM([node])

            marginal_gain.append(
                (
                    len(
                        [
                            x
                            for (x, data) in final.nodes().data()
                            if data["status"] == "used"
                        ]
                    ),
                    node,
                )
            )

        marginal_gain.sort(reverse=True)
        Q = marginal_gain
        seeds = [Q[0]]
        spread = seeds[0][0]
        Q.pop(0)

        for _ in range(n - 1):
            check = False
            while not check:
                current = Q[0][1]
                seed_nodes = [s for (_, s) in seeds]

                if self.model == "ICC":
                    _, f, _ = net.run_ICC(seed_nodes + [current], self.p, 100)
                elif self.model == "DCC":
                    _, f = net.run_DCC(
                        seed_nodes + [current], self.p, dec_func=lambda x: x * self.q
                    )
                elif self.model == "LTM":
                    _, f = net.run_LTM(seed_nodes + [current])

                f_spread = len(
                    [x for (x, data) in f.nodes().data() if data["status"] == "used"]
                )
                Q[0] = (f_spread - spread, Q[0][1])
                Q.sort(reverse=True)
                check = Q[0][1] == current

            spread += Q[0][0]
            seeds.append(Q[0])
            Q = Q[1:]

        return [seed for (_, seed) in seeds]


class GreedyHeuristic:
    def __init__(self, p: float = 0.1, q: float = 0.7, model: str = "ICC"):
        self.p = p
        self.q = q
        self.model = model

    def __call__(self, G: nx.DiGraph, n: int) -> list:
        net = Network.Network("")
        net.set_nx(G)
        seeds = []

        for _ in range(n):
            best_node = None
            best_spread = -1

            for node in G.nodes():
                if node in seeds:
                    continue
                candidate = seeds + [node]

                if self.model == "ICC":
                    _, final, _ = net.run_ICC(candidate, self.p, 1000)
                elif self.model == "DCC":
                    _, final = net.run_DCC(
                        candidate, p=self.p, dec_func=lambda x: x * self.q
                    )
                elif self.model == "LTM":
                    _, final = net.run_LTM(candidate)

                spread = (
                    sum(
                        1
                        for _, data in final.nodes(data=True)
                        if data["status"] != "inactive"
                    )
                    / final.number_of_nodes()
                )

                if spread > best_spread:
                    best_spread = spread
                    best_node = node

            seeds.append(best_node)

        return seeds


def logk_deg_union_lcc(G: nx.DiGraph, n: int):
    nodes = set()
    [nodes.add(node) for node in Heuristics.deg_h(G, math.ceil(math.log(n)))]
    G.remove_nodes_from(list(nodes))
    [
        nodes.add(node)
        for node in Heuristics.local_clustering_coefficient_h(
            G, n - math.ceil(math.log(n))
        )
    ]
    return list(nodes)


def logk_double_discount_union_lcc(G, n):
    nodes = set()
    [
        nodes.add(node)
        for node in Heuristics.double_deg_discount_h(G, math.ceil(math.log(n)))
    ]
    G.remove_nodes_from(list(nodes))
    [
        nodes.add(node)
        for node in Heuristics.local_clustering_coefficient_h(
            G, n - math.ceil(math.log(n))
        )
    ]
    return list(nodes)


def factor_deg_lcc(G: nx.DiGraph, n: int):
    score = []
    lccs = nx.clustering(G)
    for node in G.nodes():
        score.append((G.degree(node) * (1 - lccs[node]), node))
    score.sort(reverse=True)
    return [x[1] for x in score[:n]]


def inv_deg_lcc(G: nx.DiGraph, n: int):
    score = []
    lccs = nx.clustering(G)
    for node in G.nodes():
        score.append(((G.degree(node) / (1e-6 + lccs[node])), node))
    score.sort(reverse=True)
    return [x[1] for x in score[:n]]


def inv_deg_mnd(G: nx.DiGraph, n: int):
    def __neighbour_deg(G, node):
        neighbour_degrees = [G.degree(n) for n in G.adj[node]]
        if neighbour_degrees == []:
            return 0
        return sum(neighbour_degrees) / len(neighbour_degrees)

    score = []
    for node in G.nodes():
        score.append((G.degree(node) / (1e-6 + __neighbour_deg(G, node)), node))
    score.sort(reverse=True)
    return [x[1] for x in score[:n]]


def weighted_deg_mnd(G: nx.DiGraph, n: int):
    def __neighbour_deg(G, node):
        neighbour_degrees = [G.degree(n) for n in G.adj[node]]
        if neighbour_degrees == []:
            return 0
        return sum(neighbour_degrees) / len(neighbour_degrees)

    mnds = {}
    maximal_mnd = 0
    for node in G.nodes():
        mnds[node] = __neighbour_deg(G, node)
        if mnds[node] > maximal_mnd:
            maximal_mnd = mnds[node]
    score = []
    for node in G.nodes():
        score.append(
            (G.degree(node) * (1 - (1 / (1e-6 + maximal_mnd)) * mnds[node]), node)
        )
    score.sort(reverse=True)
    return [x[1] for x in score[:n]]


def mnd_deg_lcc(G: nx.DiGraph, n: int):
    def __neighbour_deg(G, node):
        neighbour_degrees = [G.degree(n) for n in G.adj[node]]
        if neighbour_degrees == []:
            return 0
        return sum(neighbour_degrees) / len(neighbour_degrees)

    mnds = {}
    maximal_mnd = 0
    score = []
    clust_coefs = nx.clustering(G)
    for node in G.nodes():
        mnds[node] = __neighbour_deg(G, node)
        if mnds[node] > maximal_mnd:
            maximal_mnd = mnds[node]
    for node in G.nodes():
        score.append((G.degree(node) * (1 - clust_coefs[node]) * mnds[node], node))
    score.sort(reverse=True)
    return [x[1] for x in score[:n]]


def deg_bet_cust8(G: nx.DiGraph, n: int):
    score = []
    bet = nx.betweenness_centrality(G)
    for node in G.nodes():
        score.append((G.degree(node) * bet[node], node))
    score.sort(reverse=True)
    return [x[1] for x in score[:n]]


def cust9_messed_up_cust5(G: nx.DiGraph, n: int):
    nodes = set()
    [nodes.add(node) for node in Heuristics.deg_h(G, math.ceil(math.log(n)))]
    G.remove_nodes_from(list(nodes))
    [nodes.add(node) for node in inv_deg_mnd(G, n - math.ceil(math.log(n)))]
    return list(nodes)


def single_run(
    dataset_name: str,
    network: nx.DiGraph,
    heuristic_name: str,
    heuristic_method,
    seed_size: int,
    maximum_iterations: int,
    trial: int,
    sampling_function,
    sample_size: int,
    model,
    p=0.1,
    q=0.7,
):
    start_time = time.time_ns()

    if sampling_function is not None and sample_size is not None:
        network = sampling_function(network, sample_size)
    # elif isinstance(network, str):
    #    with open(f"{output_folder_path}/networks/{network}", "rb") as f:
    #        network = pickle.load(f)
    elif isinstance(network, str):
        if os.path.isabs(network) or os.path.exists(network):
            # Full or relative path provided directly (e.g. from --network_location)
            network_path = network
        else:
            # Legacy behaviour: bare filename, look in output_folder_path/networks/
            network_path = f"{output_folder_path}/networks/{network}"
        with open(network_path, "rb") as f:
            network = pickle.load(f)

    filepath: str = (
        f"{output_folder_path}/{model}-{heuristic_name}-{network if isinstance(network, str) else dataset_name}-{seed_size}-{trial}.pickle"
    )

    if os.path.isfile(filepath):
        print("Terminating Trial early, already completed")
        with open(filepath, "rb") as f:
            return pickle.load(f)

    seeds = heuristic_method(network, seed_size)
    start_coverage = seed_size / len(list(network.nodes()))
    N = Network.Network("")
    N.set_nx(network)
    iterations, final = None, None

    if model not in ["ICC", "DCC", "LTM"]:
        model = "ICC"

    if model == "ICC":
        iterations, final, hist = N.run_ICC(seeds, p, maximum_iterations)
    elif model == "DCC":
        iterations, final = N.run_DCC(seeds, p=p, dec_func=lambda x: x * q)
    else:
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
                        if data["status"] == "used"
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
    with open(filepath, "wb") as handle:
        pickle.dump(result, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(
            f"""Completed a trial of {heuristic_name} and saved to file at `{filepath}`"""
        )
    return result


def sample_helper(sampling_method, base, size, label):
    return (sampling_method(base, size), label)


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
        f"{output_folder_path}/Concatenated-ICC-{heuristic_name}-{seed_size}.pickle"
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

    parser = argparse.ArgumentParser("python independent_cascade.py")
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
    parser.add_argument(
        "--samples",
        "-s",
        help="The number of samples of each network to run trials over. 0 will denote running a sample for each trial",
        type=int,
        default=10,
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Diffusion model to use: ICC, DCC, or LTM",
        type=str,
        default="ICC",
    )
    parser.add_argument(
        "--p",
        help="Propagation probability for ICC model",
        type=float,
        default=0.1,
    )
    parser.add_argument(
        "--q",
        help="Lambda scaling factor for DCC model (lambda = q * 0.7)",
        type=float,
        default=0.7,
    )
    parser.add_argument(
        "--network_location",
        "-n",
        help="Path to a folder of pre-sampled network pickle files to reuse across invocations. "
        "If omitted, networks are sampled fresh and saved to --output_location/networks.",
        type=str,
        default=None,
    )
    args = parser.parse_args()

    # create the intermediate output folder
    output_folder_path = args.output_location
    if not os.path.exists(args.output_location):
        os.makedirs(args.output_location)
    threads = args.processes
    trials = args.trials
    model = args.model.upper()
    p_val = args.p
    q_val = args.q
    network_location = args.network_location
    samples = args.samples
    logfile = f"{output_folder_path}/log.txt"

    enron_data = XsvNetwork.XsvNetwork("enron")
    airports_data = XsvNetwork.XsvNetwork("airports")
    p2p_data = XsvNetwork.XsvNetwork("p2p")
    twitter_data = XsvNetwork.XsvNetwork("twitter")

    # THIS IS THE BIT TO EDIT
    ################################################################################
    datasets = [
        # (Label, Networkx Datastructure, Sampling Method, number of nodes to sample)
        # ("Enron-MHDA-4096", enron_data.get_nx(), Sampling.mhda_sample, 4096),
        ("Enron-MHDA-1000", enron_data.get_nx(), Sampling.mhda_sample, 1000),
        ("Airports-MHDA-1000", airports_data.get_nx(), Sampling.mhda_sample, 1000),
        ("p2p-MHDA-1000", p2p_data.get_nx(), Sampling.mhda_sample, 1000),
        ("twitter-MHDA-1000", twitter_data.get_nx(), Sampling.mhda_sample, 1000),
        # ("Enron-MHRW-1024", enron_data.get_nx(), Sampling.mhrw_sample, 1024),
    ]
    heuristics = [
        #    ("Greedy_proper", GreedyHeuristic(p_val, q_val, model)),
        ("CELF_proper", CelfHeuristic(p_val, q_val, model)),
        ("cust1", logk_deg_union_lcc),
        ("cust2", logk_double_discount_union_lcc),
        ("cust3", factor_deg_lcc),
        ("cust4", inv_deg_lcc),
        ("cust5", inv_deg_mnd),
        ("cust6", weighted_deg_mnd),
        ("cust7", mnd_deg_lcc),
        ("deg_bet_cust8", deg_bet_cust8),
        ("lcc", Heuristics.local_clustering_coefficient_h),
        ("cust9", cust9_messed_up_cust5),
        # ("Random", Heuristics.random_h),
        ("Degree", Heuristics.deg_h),
        # (Name, Function)
    ]
    # seed_sizes = [10, 20]
    seed_sizes = [10, 50, 100, 150, 200, 250, 300]
    #################################################################################

    runs = []
    p = Pool(threads)

    # speedup based on the computing the samples in parallel
    print("Preparing Sampling")
    sampled_networks = {}
    if network_location is not None:
        # Reuse an existing bank of pre-sampled networks from another run.
        # Expects files named  <label>-<k>  (same convention as the saver below).
        print(f"Loading pre-sampled networks from {network_location}")
        for label, _, _, _ in datasets:
            matches = sorted(
                f for f in os.listdir(network_location) if f.startswith(f"{label}-")
            )
            if not matches:
                raise FileNotFoundError(
                    f"No pre-sampled networks found for dataset '{label}' "
                    f"in {network_location}"
                )
            sampled_networks[label] = [
                os.path.join(network_location, f) for f in matches
            ]
            print(f"  {label}: found {len(matches)} sample(s)")
    elif samples > 0 and network_location is None:
        # Original behaviour: sample fresh and save under output_location/networks.
        if not os.path.exists(f"{output_folder_path}/networks"):
            os.makedirs(f"{output_folder_path}/networks")

        for label, _, _, _ in datasets:
            sampled_networks[label] = []

        samples_pool = []
        for label, base, method, size in datasets:
            for k in range(samples):
                path = f"{output_folder_path}/networks/{label}-{k}"
                if not os.path.exists(path):
                    samples_pool.append((method, base, size, f"{label}-{k}"))
                sampled_networks[label].append(path)

        sampled_nets = p.starmap(sample_helper, samples_pool)
        for sample, label_k in sampled_nets:
            with open(f"{output_folder_path}/networks/{label_k}", "wb") as f:
                pickle.dump(sample, f, protocol=pickle.HIGHEST_PROTOCOL)
        print(sampled_nets)

    print(sampled_networks)

    print("Preparing Trials")
    for dataset_name, dataset_network, sampling_method, sample_size in datasets:
        for heuristic_name, heuristic_function in heuristics:
            for seed_size in seed_sizes:
                for trial in range(trials):
                    runs.append(
                        (
                            dataset_name,
                            (
                                dataset_network
                                if sampled_networks == {}
                                else sampled_networks[dataset_name][
                                    math.floor(random.random() * samples)
                                ]
                            ),
                            heuristic_name,
                            heuristic_function,
                            seed_size,
                            1000,  # Iteration limit, possibly too small for some networks
                            trial,
                            sampling_method if sampled_networks == {} else None,
                            sample_size,
                            model,
                            p_val,
                            q_val,
                        )
                    )

    all_rows = p.starmap(single_run, runs)
    print("Starting Compilation")
    # take mean and std dev of each combo of dataset and sample method
    existing_rows = []
    for file in os.listdir(output_folder_path):
        if file.startswith(f"{model}-") and file.endswith(".pickle"):
            with open(os.path.join(output_folder_path, file), "rb") as f:
                existing_rows.append(pickle.load(f))

    df = pd.concat(existing_rows)
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
    filepath = f"{output_folder_path}/Concatenated-Individual-Runs-{model}.pickle"
    with open(filepath, "wb") as handle:
        pickle.dump(concatenated, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print(f"Completed Concatenation {model} runs and saved to `{filepath}`")

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
            filepath = (
                f"{output_folder_path}/Compiled-{model}-{dataset}-{heuristic}.pickle"
            )
            with open(filepath, "wb") as handle:
                pickle.dump(table, handle, protocol=pickle.HIGHEST_PROTOCOL)

    filepath = f"{output_folder_path}/All-{model}-Compiled-Tables.pickle"
    with open(filepath, "wb") as handle:
        pickle.dump(tables, handle, protocol=pickle.HIGHEST_PROTOCOL)

import argparse
import math
import os
import pickle
import random
import time
from multiprocessing import Pool
import random
from collections import defaultdict
from copy import deepcopy
import networkx as nx
from networkx.algorithms.community.quality import modularity
from networkx.utils.mapped_queue import MappedQueue
import pandas as pd

def build_heuristics(model: str, p: float, q: float):
    from Influence_Modelling import Heuristics
    return [
        #("Com", com_method),
#        ("CELF", CelfHeuristic(p, q, model)),
        #("lcc", Heuristics.local_clustering_coefficient_h),
        ("Degree", Heuristics.deg_h),
        ("Deg-div-mnd", cust5),
        ("LCC", Heuristics.local_clustering_coefficient_h),
        ("Bet", Heuristics.betweenness_centrality_h)
#("hindex", custom_hindex)
    ]

SEED_SIZES = [300]
#SEED_SIZES = [10, 25,  50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300]

def custom_hindex(G: nx.DiGraph, n:int):
    score = []
    for node in G.nodes():
        score.append((__h_index(G, n), node))
    score.sort(reverse=True)
    return [x[1] for x in score[:n]]

def __h_index(G: nx.DiGraph, node:int):
    neighbour_degrees = sorted(
        [G.degree(n) for n in G.neighbors(node)],
        reverse=True
    )
    h = 0
    for i, deg in enumerate(neighbour_degrees, start=1):
        if deg >= i:
            h = i
        else:
            break
    return h

def cust5(G: nx.DiGraph, n: int):
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

def constant_threshold(G, n):
    return 0.95

class CelfHeuristic:
    def __init__(self, p: float = 0.1, q: float = 0.7, model: str = "ICC", thres_func = constant_threshold):
        self.p = p
        self.q = q
        self.model = model
        self.thres_func = thres_func

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
                if not net.thresholds:
                    net.initialise_thresholds(self.thres_func)
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


from Influence_Modelling import Network, Sampling, XsvNetwork

HeuristicFn = callable


def build_datasets():
    enron = XsvNetwork.XsvNetwork("enron")
    airports = XsvNetwork.XsvNetwork("airports")
    p2p = XsvNetwork.XsvNetwork("p2p")
    twitter = XsvNetwork.XsvNetwork("twitter")
    physics = XsvNetwork.XsvNetwork("physics")
    twitch = XsvNetwork.XsvNetwork("twitch")

    return [
        ("Enron-MHDA-1000", enron.get_nx(), Sampling.mhda_sample, 1000),
#        ("Airports-MHDA-1000", airports.get_nx(), Sampling.mhda_sample, 1000),
#        ("P2P-MHDA-1000", p2p.get_nx(), Sampling.mhda_sample, 1000),
#        ("Twitter-MHDA-1000", twitter.get_nx(), Sampling.mhda_sample, 1000),
#        ("Physics-MHDA-1000", physics.get_nx(), Sampling.mhda_sample, 1000),
#        ("Twitch-MHDA-1000", twitch.get_nx(), Sampling.mhda_sample, 1000),
    ]




def single_run(
    dataset_name: str,
    network,  # nx.DiGraph  OR  path string (pre-sampled pickle)
    heuristic_name: str,
    heuristic_fn: HeuristicFn,
    seed_size: int,
    max_iterations: int,
    trial: int,
    sampling_fn,  # callable or None
    sample_size: int,
    model: str,
    p: float,
    q: float,
    output_dir: str,
) -> pd.DataFrame:
    """Run one trial and return (or reload) a single-row DataFrame."""

    start_ns = time.time_ns()

    # --- resolve network -------------------------------------------------------
    if sampling_fn is not None and sample_size is not None:
        network = sampling_fn(network, sample_size)
    elif isinstance(network, str):
        with open(network, "rb") as f:
            network = pickle.load(f)

    # --- short-circuit if already done ----------------------------------------
    filepath = os.path.join(
        output_dir,
        f"{model}-{heuristic_name}-{dataset_name}-{seed_size}-{trial}.pickle",
    )
    if os.path.isfile(filepath):
        print(f"[skip] {filepath}")
        with open(filepath, "rb") as f:
            return pickle.load(f)

    # --- select seeds ----------------------------------------------------------
    seeds = heuristic_fn(network, seed_size)

    # --- run diffusion model ---------------------------------------------------
    net = Network.Network("")
    net.set_nx(network)

    if model == "ICC":
        _iters, final, _hist = net.run_ICC(seeds, p, max_iterations)
    elif model == "DCC":
        _iters, final = net.run_DCC(seeds, p=p, dec_func=lambda x: x * q)
    else:  # LTM
        _iters, final = net.run_LTM(seeds)

    # --- collect results -------------------------------------------------------
    node_statuses = {node: data["status"] for node, data in final.nodes(data=True)}
    n_total = final.number_of_nodes()
    n_active = sum(1 for s in node_statuses.values() if s == "active")
    n_inactive = sum(1 for s in node_statuses.values() if s == "inactive")
    n_used = sum(1 for s in node_statuses.values() if s == "used")

    result = pd.DataFrame(
        [
            {
                "dataset": dataset_name,
                "heuristic": heuristic_name,
                "n": seed_size,
                "start_coverage": seed_size / n_total,
                "end_coverage": (n_total - n_inactive) / n_total,
                "iterations": _iters,
                "time_taken_ns": time.time_ns() - start_ns,
                "active_nodes": n_active,
                "inactive_nodes": n_inactive,
                "used_nodes": n_used,
            }
        ]
    )

    with open(filepath, "wb") as f:
        pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[done] {filepath}")
    return result


def _sample_and_save(method, base_graph, size, label, output_dir):
    """Worker: draw one sample and pickle it; returns path."""
    path = os.path.join(output_dir, "networks", label)
    sample = method(base_graph, size)
    with open(path, "wb") as f:
        pickle.dump(sample, f, protocol=pickle.HIGHEST_PROTOCOL)
    return path


def prepare_samples(datasets, samples, network_location, output_dir, pool):
    """Return {label: [path, ...]} mapping, generating samples when needed."""
    sampled = {}
    if network_location is not None:
        # Reuse an existing bank of pre-sampled networks.
        print(f"Loading pre-sampled networks from {network_location}")
        for label, *_ in datasets:
            matches = sorted(
                os.path.join(network_location, f)
                for f in os.listdir(network_location)
                if f.startswith(f"{label}-")
            )
            if not matches:
                raise FileNotFoundError(
                    f"No pre-sampled networks found for '{label}' in {network_location}"
                )
            sampled[label] = matches
            print(f"  {label}: {len(matches)} sample(s)")
        return sampled

    if samples <= 0:
        return {}  # on-the-fly sampling per trial

    # Fresh sampling: parallelise across all (dataset × sample_index) pairs.
    net_dir = os.path.join(output_dir, "networks")
    os.makedirs(net_dir, exist_ok=True)

    jobs, paths = [], {}
    for label, base, method, size in datasets:
        paths[label] = []
        for k in range(samples):
            path = os.path.join(net_dir, f"{label}-{k}")
            paths[label].append(path)
            if not os.path.exists(path):
                jobs.append((method, base, size, f"{label}-{k}", output_dir))

    if jobs:
        print(f"Sampling {len(jobs)} network(s) in parallel…")
        pool.starmap(_sample_and_save, jobs)

    return paths


# ── RESULT AGGREGATION ─────────────────────────────────────────────────────────


def aggregate(rows: pd.DataFrame) -> pd.DataFrame:
    """Collapse repeated trials into mean ± std for a single (dataset, heuristic, n) group."""
    return pd.DataFrame(
        [
            {
                "dataset": rows["dataset"].iloc[0],
                "heuristic": rows["heuristic"].iloc[0],
                "n": rows["n"].iloc[0],
                "start_coverage": rows["start_coverage"].mean(),
                "start_coverage_std": rows["start_coverage"].std(),
                "end_coverage": rows["end_coverage"].mean(),
                "end_coverage_std": rows["end_coverage"].std(),
                "iterations": rows["iterations"].mean(),
                "iterations_std": rows["iterations"].std(),
                "time_taken_ns": rows["time_taken_ns"].mean(),
                "time_taken_std_ns": rows["time_taken_ns"].std(),
                "infected_nodes": rows["used_nodes"].mean(),
                "infected_nodes_std": rows["used_nodes"].std(),
                "trial_count": len(rows),
            }
        ]
    )


def save_pickle(obj, path):
    with open(path, "wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"[saved] {path}")

def parse_args():
    parser = argparse.ArgumentParser(
        description="Influence maximisation benchmark — seed selection heuristics."
    )
    parser.add_argument(
        "-o",
        "--output_location",
        default="log",
        help="Directory for all output files (default: log)",
    )
    parser.add_argument(
        "-p", "--processes", type=int, default=16, help="Worker processes (default: 16)"
    )
    parser.add_argument(
        "-t",
        "--trials",
        type=int,
        default=30,
        help="Trials per (dataset, heuristic, seed_size) (default: 30)",
    )
    parser.add_argument(
        "-s",
        "--samples",
        type=int,
        default=10,
        help="Pre-sampled networks per dataset; 0 = sample per trial (default: 10)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="ICC",
        choices=["ICC", "DCC", "LTM"],
        help="Diffusion model (default: ICC)",
    )
    parser.add_argument(
        "--p",
        dest="prop_p",
        type=float,
        default=0.1,
        help="Propagation probability for ICC/DCC (default: 0.1)",
    )
    parser.add_argument(
        "--q",
        dest="prop_q",
        type=float,
        default=0.7,
        help="Decay factor for DCC (default: 0.7)",
    )
    parser.add_argument(
        "-n",
        "--network_location",
        default=None,
        help="Path to a folder of pre-sampled network pickles to reuse",
    )
    return parser.parse_args()


def main():
    pd.options.display.max_columns = None
    pd.options.display.max_rows = None
    pd.options.display.expand_frame_repr = False

    args = parse_args()
    out_dir = args.output_location
    model = args.model.upper()
    p_val = args.prop_p
    q_val = args.prop_q
    trials = args.trials
    samples = args.samples

    os.makedirs(out_dir, exist_ok=True)

    datasets = build_datasets()
    heuristics = build_heuristics(model, p_val, q_val)
    seed_sizes = SEED_SIZES

    pool = Pool(args.processes)

    # ── sampling ───────────────────────────────────────────────────────────────
    print("Preparing samples…")
    sampled_networks = prepare_samples(
        datasets, samples, args.network_location, out_dir, pool
    )

    # ── build run list ─────────────────────────────────────────────────────────
    print("Building trial list…")
    runs = []
    for dataset_name, dataset_network, sampling_fn, sample_size in datasets:
        for heuristic_name, heuristic_fn in heuristics:
            for seed_size in seed_sizes:
                for trial in range(trials):
                    if sampled_networks:
                        network_arg = sampled_networks[dataset_name][
                            math.floor(random.random() * samples)
                        ]
                        active_sampler = None
                    else:
                        network_arg = dataset_network
                        active_sampler = sampling_fn

                    runs.append(
                        (
                            dataset_name,
                            network_arg,
                            heuristic_name,
                            heuristic_fn,
                            seed_size,
                            1000,
                            trial,
                            active_sampler,
                            sample_size,
                            model,
                            p_val,
                            q_val,
                            out_dir,
                        )
                    )

    # ── run ────────────────────────────────────────────────────────────────────
    print(f"Running {len(runs)} trial(s) across {args.processes} worker(s)…")
    all_rows = pool.starmap(single_run, runs)
    pool.close()
    pool.join()

    # ── aggregate ──────────────────────────────────────────────────────────────
    print("Aggregating results…")

    # Reload all per-trial pickles so we pick up any that were cached from a
    # previous run (all_rows already includes freshly computed ones).
    existing = []
    for fname in os.listdir(out_dir):
        if fname.startswith(f"{model}-") and fname.endswith(".pickle"):
            with open(os.path.join(out_dir, fname), "rb") as f:
                existing.append(pickle.load(f))

    df = pd.concat(existing, ignore_index=True)

    summary = pd.concat(
        [
            aggregate(
                df[(df["heuristic"] == h) & (df["dataset"] == d) & (df["n"] == s)]
            )
            for h, _ in heuristics
            for d, *_ in datasets
            for s in seed_sizes
        ],
        ignore_index=True,
    )

    save_pickle(summary, os.path.join(out_dir, f"Summary-{model}.pickle"))
    print(summary)

    # Per-(dataset, heuristic) compiled tables
    for dataset in summary["dataset"].unique():
        for heuristic in summary["heuristic"].unique():
            table = summary[
                (summary["dataset"] == dataset) & (summary["heuristic"] == heuristic)
            ]
            save_pickle(
                table,
                os.path.join(out_dir, f"Compiled-{model}-{dataset}-{heuristic}.pickle"),
            )
            print(table)

    save_pickle(
        summary,
        os.path.join(out_dir, f"All-{model}-Compiled-Tables.pickle"),
    )


if __name__ == "__main__":
    main()


from fcntl import F_SEAL_SEAL
from genericpath import isfile
import math
from multiprocessing import Pool
import os
import pickle
import random
import time
from typing import Callable
import networkx as nx
import pandas as pd

from Influence_Modelling import Heuristics, Network, Sampling


def write(object, filepath):
    with open(filepath, "wb") as file_handle:
        pickle.dump(object, file_handle, protocol=pickle.HIGHEST_PROTOCOL)


def read(filepath):
    with open(filepath, "rb") as file_handle:
        return pickle.load(file_handle)


class Dataset:
    def __init__(
        self,
        label: str,
        data: nx.DiGraph,
        sampling_method: Callable[[nx.DiGraph, int], nx.DiGraph] | None,
        sample_size: int = 1024,
    ) -> None:
        self.textual_label = label
        self.data = data
        self.sampling_method: Callable[[nx.DiGraph, int], nx.DiGraph] = (
            sampling_method if sampling_method is not None else Sampling.no_sample
        )
        self.sample_size = sample_size

        if sampling_method is not None:
            # check sample sizes
            if sample_size <= 0:
                raise Exception("[Dataset] Sample Size Needs to be >= to size 1")
            # check sampling method
            if not callable(sampling_method):
                raise Exception(
                    "[Dataset] Need the sampling method to be a valid function"
                )

    def perform_sample(self):
        return Dataset(
            self.textual_label, self.sampling_method(self.data, self.sample_size), None
        )


class Heuristic:
    def __init__(self, label: str, heuristic_method) -> None:
        self.textual_label = label
        self.heuristic = heuristic_method


class Run:
    def __init__(
        self,
        dataset: Dataset,
        heuristic: Heuristic,
        seed_size: int,
        trial_number: int,
        method: str,
        path_prepend: str,
    ) -> None:
        self.dataset = dataset
        self.heuristic = heuristic
        self.seed_size = seed_size
        self.trial_number = trial_number
        self.method = method
        self.path_prepend = path_prepend

    def _generate_path(self):
        return f"{self.method}-{self.heuristic.heuristic.__str__().split(' ')[1]}-{self.dataset.textual_label}-{self.seed_size}-{self.trial_number}"

    def compute(self):
        path = f"{self.path_prepend}/{self._generate_path()}.pickle"
        if os.path.isfile(f"{self._generate_path()}.pickle"):
            return
        seeds = self.heuristic.heuristic(self.dataset.data, self.seed_size)
        start_coverage = self.seed_size / len(list(self.dataset.data.nodes()))
        start_time = time.time_ns()
        N = Network.Network("", "", False)
        N.set_nx(self.dataset.data)
        iterations, final = N.run_ICC(seeds, 0.1, 10000)
        end_coverage = len(
            [data for _, data in final.nodes().data() if data["status"] != "inactive"]
        ) / len(list(final.nodes()))
        end_time = time.time_ns()

        result = pd.DataFrame(
            data=[
                [
                    self.dataset.textual_label,
                    self.heuristic.heuristic.__str__().split(" ")[1],
                    self.seed_size,
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

        write(result, path)


class Experiment:
    def __init__(
        self,
        heuristics: list[Heuristic],
        datasets: list[Dataset],
        seed_sizes: list[int],
        trials: int,
        unique_samples_count: int,
        output_path: str,
        threads: int,
    ) -> None:
        self.output_path = output_path
        self.threads = threads
        self.unique_samples_count = (
            unique_samples_count if self.unique_samples_count >= 1 else 0
        )
        self.trials = trials
        self.seed_sizes = seed_sizes
        self.datasets = datasets
        self.heuristics = heuristics
        self.p = Pool(self.threads)
        self.samples = {}

    def generate_samples(self):
        if self.unique_samples_count <= 0:
            self.unique_samples_count = 1
        for i in range(self.unique_samples_count):
            for ds in self.datasets:
                sample = f"{ds.textual_label}-{ds.sample_size}-{ds.sampling_method}-{i}"
                # check the filesystem
                local = read(f"{self.output_path}/networks/{sample}")
                if local is not None:
                    self.samples[sample] = local
                # if we don't have it then run the sample
                if sample not in self.samples:
                    self.samples[sample] = ds.perform_sample()
                    write(self.samples[sample], f"{self.output_path}/networks/{sample}")

    def compute_trials(self):
        trials = []
        for trial_number in range(self.trials):
            for heuristic in self.heuristics:
                for seed_size in self.seed_sizes:
                    for ds in self.datasets:
                        trials.append(
                            Run(
                                self.samples[
                                    f"{ds.textual_label}-{ds.sample_size}-{ds.sampling_method}-{math.floor(random.random() * self.unique_samples_count)}"
                                ],
                                heuristic,
                                seed_size,
                                trial_number,
                                "ICC",
                                f"{self.output_path}/runs",
                            )
                        )
        self.p.starmap(lambda trial: trial.compute(), trials)

    def _create_file_structure(self) -> None:
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)
        if self.unique_samples_count > 0:
            if not os.path.exists(f"{self.output_path}/networks"):
                os.makedirs(f"{self.output_path}/networks")

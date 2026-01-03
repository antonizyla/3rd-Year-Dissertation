import ast
import importlib.resources
import os
from pathlib import Path

import networkx as nx

from Influence_Modelling.Network import Network


class XsvNetwork(Network):
    """
    XsvNetwork Class: Load networks from CSV/TSV files or preloaded datasets.

    Extends the base Network class to support loading network data from:
    - CSV/TSV files with customizable separators
    - Preloaded datasets: "airports", "p2p", "twitter"
    - Files with edge weights or metadata

    Supports various edge formats:
    - `u v` (simple edge)
    - `u v weight` (weighted edge)
    - `u v {metadata}` (edge with dictionary metadata)

    Example usage:

        # Load from preloaded dataset
        net = XsvNetwork("project", "my_network", "airports")

        # Load from custom CSV file
        net = XsvNetwork("project", "my_network", "data.csv", separator=",")

        # Load TSV with custom separator
        net = XsvNetwork("project", "my_network", "data.tsv", separator="\t")
    """

    def __init__(
        self,
        filepath: str,
        separator: str = ",",
        verbose: bool = False,
    ) -> None:
        """
        Initialize XsvNetwork from file or preloaded dataset.

        :param str project: Name of project (links to SQLite database file)
        :param str name: Name of the network
        :param str filepath: Path to file or preloaded dataset name
                           ("airports", "p2p", "twitter")
        :param str separator: Field separator (default ",")
        :param bool verbose: Enable verbose logging (default False)
        """
        super().__init__("", verbose)
        self.__filepath = filepath
        self.__G = nx.empty_graph()
        self.__v = verbose
        self.__H = nx.empty_graph()
        self.__sep = separator
        self.__edge_list_to_graph(self.__read_file_to_str())

    def __read_file_to_str(self) -> list[str]:
        # Packaged with the library
        if self.__filepath == "airports":
            self.__sep = " "
            data = importlib.resources.open_binary(
                "Influence_Modelling.datasets", "usairport.tsv"
            )
            return data.read().decode("utf-8").split("\n")
        elif self.__filepath == "enron":
            self.__sep = "\t"
            data = importlib.resources.open_binary(
                "Influence_Modelling.datasets", "enron.txt"
            )
            return data.read().decode("utf-8").split("\n")
        elif self.__filepath == "p2p":
            self.__sep = "\t"
            data = importlib.resources.open_binary(
                "Influence_Modelling.datasets", "p2p-Gnutella04.txt"
            )
            return data.read().decode("utf-8").split("\n")
        elif self.__filepath == "twitter":
            self.__sep = " "
            data = importlib.resources.open_binary(
                "Influence_Modelling.datasets", "twitter_combined.txt"
            )
            return data.read().decode("utf-8").split("\n")
        # Own files
        absolute_path: str = ""
        if os.path.isfile(self.__filepath):
            absolute_path = self.__filepath
        elif os.path.isfile(os.path.join(os.getcwd(), self.__filepath)):
            absolute_path = os.path.join(os.getcwd(), self.__filepath)
        return Path(absolute_path).read_text().split("\n")

    def __edge_list_to_graph(self, contents) -> None:
        for line in contents:
            line = line.replace("\r", "")
            # line is of the format 1. `u v {data: ...}`
            split_line = line.split(self.__sep)
            if len(split_line) == 2:
                self.__H.add_edge(split_line[0], split_line[1])
                if self.__v:
                    print(
                        f"""[SV Network] Added edge between 
                        {split_line[0]} and {split_line[1]}"""
                    )
            elif len(split_line) == 3:
                if split_line[2].startswith("{") and split_line[2].endswith("}"):
                    # if third element is a dict parse it
                    self.__H.add_edge(
                        split_line[0], split_line[1], ast.literal_eval(split_line[2])
                    )
                    if self.__v:
                        print(
                            f"""[SV Network] Added edge between {split_line[0]} 
                            and {split_line[1]} with data {split_line[2]}"""
                        )
                else:
                    # can use the third element as a weight
                    self.__H.add_edge(
                        split_line[0], split_line[1], weight=int(split_line[2])
                    )
                    if self.__v:
                        print(
                            f"""[SV Network] Added edge between {split_line[0]}
                              and {split_line[1]} with weight {split_line[2]}"""
                        )
            else:
                print(f"[SV Network] Error Reading row with content `{line}`")
        self.__G = self.__H

    def get_nx(self):
        return self.__G

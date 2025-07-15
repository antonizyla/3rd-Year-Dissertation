import ast
import importlib.resources
import os
from pathlib import Path

import networkx as nx

from Influence_Modelling.Network import Network


class XsvNetwork(Network):
    def __init__(
        self,
        project: str,
        name: str,
        filepath: str,
        seperator: str = ",",
        verbose: bool = False,
    ) -> None:
        super().__init__(project, name)
        self.__filepath = filepath
        self.__G = nx.empty_graph()
        self.__v = verbose
        self.__H = nx.empty_graph()
        self.__sep = seperator
        self.__edge_list_to_graph(self.__read_file_to_str())

    def __read_file_to_str(self) -> list[str]:
        # Pacakged with the library
        if self.__filepath == "airports":
            self.__sep = " "
            data = importlib.resources.open_binary(
                "Influence_Modelling.datasets", "usairport.tsv"
            )
            return data.read().decode("utf-8").split("\n")
        elif self.__filepath == "p2p":
            self.__sep = " "
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
        """
        Returns the networkx graph object.
        """
        return self.__G

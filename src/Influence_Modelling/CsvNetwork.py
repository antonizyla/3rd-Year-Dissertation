from Network import Network

import ast
import os
from pathlib import Path
import networkx as nx

"""
Class for dealing with input from a csv file
"""


class Net_CSV(Network):
    def __init__(self, project: str, name: str, filepath: str):
        self.__filepath = filepath

        self.__edge_list_to_graph(self.__read_file_to_str())

        super().__init__(project, name)

    def __read_file_to_str(self, verbose=False) -> list[str]:
        absolute_path: str = ""
        if os.path.isfile(self.__filepath):
            absolute_path = self.__filepath
        elif os.path.isfile(os.path.join(os.path.curdir, self.__filepath)):
            absolute_path = os.path.join(os.path.curdir, self.__filepath)

        # read and return the file
        return Path(absolute_path).read_text().split("\n")

    def __edge_list_to_graph(self, contents):
        self.H = nx.empty_graph()
        for line in contents:
            # line is of the format 1. `u v {data: ...}`
            split_line = line.split(",")
            if len(split_line) == 2:
                self.H.add_edge(split_line[0], split_line[1])
            elif len(split_line) == 3:
                self.H.add_edge(
                    split_line[0], split_line[1], ast.literal_eval(split_line[2])
                )  # type: ignore
            else:
                print(f"[CSV Network] Error Reading row: {line}")
        self.__G = self.H

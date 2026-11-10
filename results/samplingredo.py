import networkx as nx
import pandas as pd
import numpy as np

from multiprocessing import pool
from Influence_Modelling import XsvNetwork, Metrics, Network, Sampling

def apply_metric_calcs(G: nx.DiGraph, method_func, method_name, network_name):
  pass 

networks = [
  ("Enron", XsvNetwork.XsvNetwork("enron"))
]

methods = [
  ("MHDA", Sampling.mhda_sample),
  ("MHRW", Sampling.mhrw_sample),
  ("BFS", Sampling.bfs_sample),
  ("SNS", Sampling.snowball_sample)
]

computations = []

for network_name, G in networks:
  for method_name, method_func in methods:
    computations.append((G, method_func, method_name, network_name))
    
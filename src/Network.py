import networkx as nx
import uuid
import sqlite3
from Db import initialise_database
import ast


class Network:
    """
    Initialise a new empty Graph - included methods for different types of graph representation
    """

    def __init__(self, project: str, name: str) -> None:
        self.network_id: str = str(uuid.uuid4())
        self.G: nx.DiGraph = nx.empty_graph()
        self.name: str = name
        con: sqlite3.Connection | None = initialise_database(project)
        if con is not None:
            self.con: sqlite3.Connection = con

    """
        Save the network into database to not require keeping original data sources around whenever need to use them.
    """

    def save_db(self, verbose=False) -> bool:
        edge_list: list[str] = [line for line in nx.generate_edgelist(self.G)]
        query = """
            insert into networks (id, name, network) values (?, ?, ?);
        """  # id, name, blob
        try:
            cur: sqlite3.Cursor = self.con.cursor()
            cur.execute(query, (self.network_id, self.name, str(edge_list)))
            self.con.commit()
        except:
            print("[Network] Error Saving to Database")
            return False
        return True

    """
        Used to take in a UUID and populate this network object with it's data from the database.
    """

    def load_from_db(self, name: str, verbose=False) -> bool:
        query = """
            select * from networks where name = ?
        """
        cur: sqlite3.Cursor = self.con.cursor()
        res: sqlite3.Cursor = cur.execute(
            "select * from networks where name = ?", (name,)
        )
        temp_record = res.fetchone()
        self.network_id = temp_record[0]
        self.name = name
        try:
            edges_list: list[str] = ast.literal_eval(temp_record[2])
            edges = []
            for edge in edges_list:
                sp: list[str] = edge.split()
                edges.append((sp[0], sp[1], ast.literal_eval(sp[2])))
            self.G.add_edges_from(edges)
            if verbose:
                print(f"[Network Verbose] Loaded {len(self.G.edges)} edges into graph")
        except:
            print("[Network] Error Occured in Reading file")
            return False
        return True

    def run_ICC(seed_nodes):
        pass

    def run_DCC(seed_nodes):
        pass

    def run_LTM(seed_nodes):
        pass

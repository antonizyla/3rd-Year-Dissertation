import networkx as nx
import uuid

class Network:

    """
        Initialise a new empty Graph - included methods for different types of graph representation
    """
    def __init__(self) -> None:
        self.network_id: uuid.UUID = uuid.uuid4()
        self.G: nx.DiGraph = nx.empty_graph()
        pass

    """
        Save the network into database to not require keeping original data sources around whenever need to use them.
    """
    def save_db(self) -> bool:
        return True
    
    """
        Used to take in a UUID and populate this network object with it's data from the database.
    """
    def load_from_db(self, network_id: uuid.UUID) -> bool :
        return True

    def run_ICC(seed_nodes):
        pass

    def run_DCC(seed_nodes):
        pass 

    def run_LTM(seed_nodes):
        pass 
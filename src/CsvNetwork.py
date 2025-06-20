from Network import Network


"""
Class for dealing with different types of graph input
"""
class Net_CSV(Network):

    def __init__(self, filepath: str):
        self.filepath = filepath
        super().__init__()

    # helper for init to load file and place into nx format.
    # allows for saving it into db later.
    def to_nx():
        pass
    
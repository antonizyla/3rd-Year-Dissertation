from Network import Network

"""
Class for dealing with input from a csv file
"""


class Net_CSV(Network):
    def __init__(self, project: str, name: str, filepath: str):
        self.filepath = filepath
        super().__init__(project, name)

    # helper for init to load file and place into nx format.
    # allows for saving it into db later.
    def to_nx():
        pass

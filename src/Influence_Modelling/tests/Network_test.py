import os

import Influence_Modelling.Network as Net


def test_invalid_project():
    net = Net.Network("ABC", "name")  # noqa: F841
    # there doesn't exist a file called ABC
    # expected behaviour is to create one
    if not os.path.isfile("ABC"):
        assert False
    assert True


def test_malformed_sqlite():
    # the given project path has a file but the file is unrelated

    # write a text file
    f = open("TestFile", "w")
    f.write("Text File Contents")
    f.close()

    n = Net.Network("TestFile", "Network")
    assert n.save_db() == ""  # should not save as it's invalid

    os.remove("TestFile")

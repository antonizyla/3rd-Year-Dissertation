import pickle


def write(object, filepath):
    with open(filepath, "wb") as file_handle:
        pickle.dump(object, file_handle, protocol=pickle.HIGHEST_PROTOCOL)


def read(filepath):
    with open(filepath, "rb") as file_handle:
        return pickle.load(file_handle)

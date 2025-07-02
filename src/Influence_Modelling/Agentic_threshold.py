class Agentic_threshold_model:
    def __init__(self) -> None:
        self.__agent_types = ["Student", "Teacher", "Parent"]
        self.__agents = []

        self.__relationship_matrix: dict[str, list[str]] = {
            "Student": ["Teacher", "Student"],
            "Teacher": ["Student", "Parent", "Teacher"],
            "Parent": ["Student", "Teacher", "Parent"],
        }

    def __network(self):
        # net = Network()
        pass

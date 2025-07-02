from Db import initialise_database, query_all_networks

import os
import sqlite3
import sys


def prompt_for_input(prompt: str, letters: list[str], numbers: list[int]) -> str | int:
    while True:
        choice: str = input(prompt)
        if choice.isnumeric():
            if int(choice) in numbers:
                return int(choice)
        else:
            if choice in letters:
                return choice


def initial_load_print(con: sqlite3.Connection):
    print("Welcome to Influence Modelling Framework!")
    print("===================================================")
    print("Select an Option:")
    print("1. Import Data")
    print("2. Load Data")
    print("3. Run Model on Data")
    print("4. Save Results")
    c: str | int = prompt_for_input(">>> ", ["q", "Q"], [1, 2, 3, 4])
    match c:
        case "q":
            print("[Exiting Application]")
            sys.exit(0)
        case "Q":
            print("[Exiting Application]")
            sys.exit(0)
        case 1:
            print("Not Implemented")
            initial_load_print(con)
        case 2:
            print("[Going to Data Loading]")
            load_data(con)
        case 3:
            print("Not Implemented")
            initial_load_print(con)
        case 4:
            print("Not Implemented")
            initial_load_print(con)


def initial_load(con: sqlite3.Connection):
    print("Welcome to Influence Modelling Framework")
    workspace = input_workspace()
    print(workspace)


def input_workspace():
    print("Select a workspace folder")
    print("-------------------------")
    print("n. Create a new folder")
    directories = [
        dir
        for dir in os.listdir(os.getcwd())
        if os.path.isdir(os.path.join(os.getcwd(), dir))
    ]
    print("--Available Directories: --")
    for index, dir in enumerate(directories):
        print(f"{index}. ./{dir}/")
    choice: str | int = prompt_for_input(
        "Choose and option: ", ["n", "q"], [x + 1 for x in range(len(directories))]
    )
    if type(choice) is str:
        if choice == "n":
            print("[Moving to New Workspace Creation Screen]")
            return "n"
        else:
            print("[Quiting Program]")
            return "q"
    elif type(choice) is int:
        return str(directories[choice - 1])


def load_data(con: sqlite3.Connection):
    print("[Loading Data] Entering Loading Data")
    print("Networks in Database: ")
    networks: list[dict[str, str]] = query_all_networks(con)
    for i, network in enumerate(networks):
        print(f"{i + 1}. Name: {network['name']}, Id: {network['id']}")
    print("Select a network to work on, or 'q' to go back")

    c: str | int = prompt_for_input(
        ">>> ", ["q", "Q"], [i + 1 for i in range(len(networks))]
    )
    if type(c) is int:
        work_on_network(networks[c - 1]["id"], networks[c - 1]["name"])
    else:
        print("[Returning to Main Menu]")
        initial_load_print(con)
        return


def work_on_network(networkId: str, networkName: str):
    print(f"Working on Network: {networkName} with Id: {networkId}")


if __name__ == "__main__":
    # make this be over a filepath for a set of sqlite file which
    # will act as 'projects'
    project_file = "db"
    c: sqlite3.Connection | None = initialise_database(project_file)
    if c is None:
        print(f"[Error] Cannot establish connection to database `{project_file}`")
        sys.exit(1)
    con: sqlite3.Connection = c

    initial_load(con)

    sys.exit(0)

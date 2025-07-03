import os
import sqlite3


def initialise_database(path, verbose=False) -> sqlite3.Connection | None:
    if os.path.exists(os.path.join(os.getcwd(), path)):
        if verbose:
            print("[Database] File Found - Connection Successful")
        con: sqlite3.Connection = sqlite3.connect(path)
        try:
            cur = con.cursor()
            cur.execute("PRAGMA integrity_check")
        except sqlite3.DatabaseError:
            print(
                "[Database] Given File is not a valid Sqlite Database File, "
                "choose a different file"
            )
            return None
        return con
    else:
        if verbose:
            print("[Database] File Not Found - Creating one")
        con: sqlite3.Connection = sqlite3.connect(os.path.join(os.getcwd(), path))
        return con


def create_tables(con: sqlite3.Connection) -> bool:
    query = """
        CREATE TABLE IF NOT EXISTS networks(
            id varchar(128) primary key,
            name varchar(50) not null,
            network text not null
        );
    """
    cur: sqlite3.Cursor = con.cursor()
    cur.execute(query)
    return networks_table_exists(con)


def delete_networks_table_contents(con: sqlite3.Connection) -> bool:
    query = """
        Drop table networks;
    """
    cur: sqlite3.Cursor = con.cursor()
    cur.execute(query)
    create_tables(con)
    return networks_table_exists(con)


def networks_table_exists(con: sqlite3.Connection) -> bool:
    cur: sqlite3.Cursor = con.cursor()
    res: sqlite3.Cursor = cur.execute("SELECT name FROM sqlite_master")
    if res.fetchone()[0] == "networks":
        return True
    return False


def query_all_networks(con: sqlite3.Connection) -> list[dict[str, str]]:
    cur: sqlite3.Cursor = con.cursor()
    cur.execute("select name, id from networks")
    rows = cur.fetchall()
    r = []
    for row in rows:
        r.append({"name": row[0], "id": row[1]})
    return r


def close(con: sqlite3.Connection):
    con.close()

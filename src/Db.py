import sqlite3
import os


def initialise_database(path) -> sqlite3.Connection | None:
    if os.path.exists(os.path.join(os.getcwd(), path)):
        print("[Database] File Found - Connection Successful")
        con: sqlite3.Connection = sqlite3.connect(path)
        return con
    else:
        print("[Database] File Not Found - Please Create a DB file for Sqlite to use")
        return None


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


def query_all_networks(con: sqlite3.Connection)->list[dict[str, str]]:
    cur = con.cursor()
    res = cur.execute("select name, id from networks")
    rows = cur.fetchall()
    r = []
    for row in rows:
        r.append({'name': row[0], 'id': row[1]})
    return r

def close(con: sqlite3.Connection):
    con.close()

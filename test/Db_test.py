import os
import sqlite3

from Db import initialise_database


def test_initialise_db():
    f = open("File", "w")
    f.close()
    try:
        r = initialise_database("File")
        assert type(r) is sqlite3.Connection
        assert type(r) is not None
    finally:
        os.remove("File")


def test_init_db_incorrect_type():
    f = open("File", "w")
    f.write("Text file")
    f.close()

    try:
        r = initialise_database("File")
        assert type(r) is not sqlite3.Connection
    finally:
        os.remove("File")


def test_init_db_not_exist():
    r = initialise_database("File")
    assert type(r) is sqlite3.Connection

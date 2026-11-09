import sqlite3
import sys
import os

if len(sys.argv) != 2:
    print("Usage Error: requires `python3 scriptname <Database Path>`")
    sys.exit()

# error in sqlite path
if not os.path.isfile(sys.argv[1]):
    print("Error in specified SQLite Database Location")
    sys.exit()

print("Attempting to Open Database conection")
con = sqlite3.connect(sys.argv[1])
cursor = con.cursor()

res = cursor.execute(
    "CREATE TABLE emails (emailID INTEGER PRIMARY KEY ASC, sender TEXT, recipients TEXT, messageID Text)"
)
res = cursor.execute(
    "insert into emails select ROWID, SUBSTR (message, INSTR (message, 'From: ') + 6, ABS( INSTR (message, 'From: ') + 7 - INSTR (message, 'To: '))) as sender, SUBSTR (message,INSTR (message, 'To: ') + 4,ABS(INSTR (message, 'To: ') + 5 - INSTR (message, 'Subject: '))) as recipients, substr(message, INSTR(message, '-ID: ')+5, ABS(INSTR(message, '-ID: ')-INSTR(message, 'Date: ')+6)) from foo;"
)
res = cursor.execute(
    "create table edges ( edgeID INTEGER PRIMARY KEY ASC,inNode TEXT Not null,outNode TEXT not null);"
)

print("Ingesting modified data into script")

res = cursor.execute("select count(1) from foo")
if res.fetchone() is None:
    print("Database is not in correct format")
    print(
        "Import data into the database using the interactive shell into a table called `foo`"
    )
    sys.exit()

print("Ingesting Data from temp table into script")

res = cursor.execute("Select sender, recipients from emails")

edge_pairs: list[list[str]] = []

for r in res.fetchall():
    for recipient in r[1].split(", "):
        edge_pairs.append(
            [r[0].removesuffix("\n"), recipient.removesuffix("\n").removeprefix("\n\t")]
        )

print("Ingested Rows, Count: ", len(edge_pairs))

stmt = """Insert into edges (edgeId, inNode, outNode) values (?, ?, ?)"""
for i, e in enumerate(edge_pairs):
    cursor.execute(stmt, (i, e[0], e[1]))

con.commit()

print("Completed Insertion of Rows")
print("Removing Temporary Tables Table")

cursor.execute("Drop table emails")
cursor.execute("Drop table foo")

print("Completed temporary data removal")

print("Creating Nodes from edgeset")
res = cursor.execute(
    "Create table nodes (nodeId integer primary key asc, nodeVal unique Text)"
)

res = cursor.execute("Insert into nodes select distinct inNode from edges")

cursor.close()
con.close()

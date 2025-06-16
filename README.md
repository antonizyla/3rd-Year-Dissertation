# Antoni Zyla 3rd Year Project

**Abstract:** Influence Maximization Evaluation Research Platform

Design and Implement a Tool for running various sampling techniques on networks, allowing
for ’slot in’ testing of various heuristics and comparison against existing papers. Operating on
Independant Cascade, Decreasing Cascade and Linear Threshold Models.

## Functionality as of right now

- Import Data into an sqlite database from enron_emails csv files. slices out the to and from parts of emails into a set of edges for each email. Adds them to the database in a table called 'edges' -> there are about 3 million of them.
- Needs the csv imported into the database under the table `foo` with columns of `file` and `message`

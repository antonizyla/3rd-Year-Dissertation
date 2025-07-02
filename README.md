# Antoni Zyla 3rd Year Project

**Abstract:** Influence Maximization Evaluation Research Platform

Design and Implement a Tool for running various sampling techniques on networks, allowing
for ’slot in’ testing of various heuristics and comparison against existing papers. Operating on
Independant Cascade, Decreasing Cascade and Linear Threshold Models.

# Usage

### Prerquisities
1. `Python 3.13` (lower versions not tested but very likely to work)
2. `Pip` (via global system or a virtual env)

## Installation

### From Source

1. Download the Source Code using Git
```bash
git clone git@github.com:antonizyla/3rdyearproject
```
2. Enter Downloaded Directory
```bash
cd 3rdyearproject/
```
3. Install Python Dependencies (This can be global or into a venv)
```bash
pip install -r requirements.txt
```
**This is the stage where you would modify the code and then pacakge it for your own use**

4. Package the source into a wheel
```bash
python3 -m build
```
5. Install the package onto your system
```bash
pip install dist/influence_modelling-*.whl
```

### Using Package Files

1. Download the package from github repository
```bash
wget https://github.com/antonizyla/3rdyearproject/blob/main/dist/influence_modelling-(version).whl
```
2. Install (globally or in a venv)
```bash
pip install influence_modelling-(version).whl
``` 
## Removal

1. Remove from system via pip
```bash
pip uninstall Influence_Modelling
```
2. Delete downloaded file or source directory
```bash
rm influence_modelling-(version).whl
```

# Usign the Package in Python files
```python
from Influence_Modelling import Network as Net

N = Net.Network(...) # create a network
N.load_from_db("path") # load a premade network from disk
N.run_DCC(N.deg_discount(5)) # run a simulation on the network
```
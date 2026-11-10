# Antoni Zyla (U5527350) Dissertation Repo

![Final Report](https://github.com/antonizyla/3rdyearproject/blob/main/submission/Report.pdf) Scored 73%

# **Abstract:** 

Influence maximisation is the process of choosing a subset of population within a network to max-
imise the spread of an idea or concept under a certain model of propagation. Computing the
optimal solution is NP hard and therefore not feasible to compute for networks of a practical size.
Existing approaches including the greedy algorithm and it’s optimisation produce a good theoret-
ical guarantee as an approximation of the optimal solution but even still tend to scale poorly even
on relatively small networks.

In this paper we propose and evaluate an approach to efficiently solving this problem across
three primary models of propagation, the independent cascade model, the decreasing cascade model
and the linear threshold model. We test across six (6) real world networks of varying topologies and
scale, sampled using the Metropolis Hastings Random Walk with Delayed Acceptance (MHDA)
algorithm, a performant and topology preserving method. Statistical analysis is performed using
Mann-Whitney U tests to determine equivalence of distributions, power tests to determine sample
sizes and Cohen’s d to measure effect sizes.

Our proposed heuristic investigates locally computable node metrics in conjunction with net-
work wide measures and metrics. Performance of an approach is highly dependent upon different
network topologies, starting influential set sizes and the underlying community structures of net-
works. Our strongest performing heuristic is a combination of the degree of a node and the mean
degree across it’s neighborhood, it consistently matches or exceeds CELF across all of the networks
under the decreasing cascade model and the linear threshold model at all seed sizes, using a 1000
seed network sample. The ability to be computed with no global knowledge of the network makes
it a very performant option which can scale across vast networks.

We also investigate community based methods, attempting to exploit the properties of the
greedy modularity maximisation community detection algorithm to capture influential nodes in an
efficient manner.

Our results suggest that simple and carefully constructed heuristics can reliably match the
performance of a computationally heavy approximation method across a range of real world network
topologies. We find community based methods perform very well as shown in literature but we are
unable to make gains past that.

## Some Key Results

<img width="939" height="314" alt="image" src="https://github.com/user-attachments/assets/3f8ffbf2-2f83-433c-8c58-d5e1dca81e01" />

The performance characteristics of key heuristics are shown in the above table.

<img width="840" height="699" alt="image" src="https://github.com/user-attachments/assets/ee5efd04-aeff-42cf-900b-cad843d268fa" />

The influence performance characteristics of the methods shown across LTM models. Pages 17-19 of report go into detail about the performance and it's statistical significance.

<img width="1072" height="317" alt="image" src="https://github.com/user-attachments/assets/4f0185f4-6dfa-4bc3-8381-dd5844ff3490" />

Interchangeability of results between CELF with Monte Carlo method and repeatedly running CELF with just one random descision per iteration shown to be equivalent over the required number of samples to eliminate sample variance giving a massive performance uplift.



## Usage of Code

### Prerquisities
1. `Python 3.10` or above
2.  `Pip` (via global system or a virtual env)

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
python3.xx -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
**This is the stage where you would modify the code and then pacakge it for your own use**

4. Package the source into a wheel
```bash
python -m build
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
N.run_DCC(N.deg_discount(5)) # run a simulation on the network
```

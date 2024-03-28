# Rocket_GraphPlan
This is a Python implementation of the GraphPlan algorithm.

The domain used is the Rocket domain with the 'has-fuel' proposition.

The algorithm is implemented in the file `graphplan.py` and the domain is defined in the file `domain.py`.

## Usage
To run the algorithm, the simplest way is to run the `main.py` file. This will run the algorithm while building a complete trace containing the expansion of the graph and the extraction process (backtracking to find intermediate plans is shown with indentation and I can't say I'm not proud of it).

The trace file is then saved at the root of the project.

You can use any initial state and goal state by creating a text file that follows the format of the `r_factX.txt` files and changing the `main.py` file to read the file you created.

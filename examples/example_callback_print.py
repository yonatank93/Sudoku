"""Example of a basic callback function that prints how many empty cells remain
in each iteration.
"""

import json
from pathlib import Path

from sudoku import Sudoku


# Load the problem
data_path = (
    Path(__file__).resolve().parent.parent / "data" / "9by9" / "board_11.json"
)
with open(data_path, "r") as f:
    data = json.load(f)

# Instantiate the Sudoku board
board = Sudoku(
    data["board"],
    allowed_values=data["allowed_values"],
    block_dim=data["block_dim"],
)


# Define a custom callback function
def callback(board_inst):
    """Print how many cells are still empty."""
    nempty_cell = len(board_inst.empty_cells)
    print("Iteration:", board_inst.niter, "Number of empty cells:", nempty_cell)


# Solve the problem
board.solve(callback)

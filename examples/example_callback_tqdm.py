"""Example of a callback function that displays a progress bar based on how many
empty cells remain in each iteration.
"""

import json
from pathlib import Path
from tqdm import tqdm

from sudoku import Sudoku


# Load the problem
data_path = (
    Path(__file__).resolve().parent.parent / "data" / "9by9" / "board_10.json"
)
with open(data_path, "r") as f:
    data = json.load(f)

# Instantiate the Sudoku board
board = Sudoku(
    data["board"],
    allowed_values=data["allowed_values"],
    block_dim=data["block_dim"],
)
total_cells = len(data["allowed_values"]) ** 2

# Instantiate the progress bar
pbar = tqdm(total=total_cells, desc="Completion")


# Define a custom callback function
def callback(board_inst):
    """Display a progress bar showing the completion of the board."""
    nempty_cell = len(board_inst.empty_cells)
    pbar.n = 0
    pbar.update(total_cells - nempty_cell)
    pbar.refresh()


# Solve the problem
board.solve(callback)
pbar.close()

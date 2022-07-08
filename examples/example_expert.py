"""Note that in the currnt version (07/04), this problem cannot be solved."""


import json
from tqdm import tqdm

import numpy as np

from sudoku import Board


# Load the problem
data = json.load(open("../data/board_10.json", "r"))

# Instantiate the board
board = Board(data["board"])

# pbar = tqdm(total=81, desc="Completion")


# Define a custom callback function
def callback(board_inst):
    """This callback function will print how many tiles are still empty."""
    nempty_tile = len(board_inst.empty_tiles)
    print("Iteration:", board_inst.niter, "Number of empty tiles:", nempty_tile)
    # pbar.n = 0
    # pbar.update(81 - nempty_tile)
    # pbar.refresh()


# Solve the problem
board.solve(callback)
# pbar.close()

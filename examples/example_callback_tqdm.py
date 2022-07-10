"""In this script, I give an example on a callback function that display
progress bar based on how many empty tiles are in each iteration.
"""


import json
from tqdm import tqdm

from sudoku import Board


# Load the problem
data = json.load(open("../data/board_10.json", "r"))

# Instantiate the board
board = Board(data["board"])

# Instantiate the progress bar
pbar = tqdm(total=81, desc="Completion")


# Define a custom callback function
def callback(board_inst):
    """This callback function display a progress bar that shows the completion
    of the board. This is done by counting the number of empty tiles.
    """
    nempty_tile = len(board_inst.empty_tiles)
    pbar.n = 0
    pbar.update(81 - nempty_tile)
    pbar.refresh()


# Solve the problem
board.solve(callback)
pbar.close()

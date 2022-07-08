"""In this script, I give an example on a basic callback function that prints
how many empty tiles in each iteration.
"""

import json

from sudoku import Board


# Load the problem
data = json.load(open("../data/board_11.json", "r"))

# Instantiate the board
board = Board(data["board"])


# Define a custom callback function
def callback(board_inst):
    """This callback function will print how many tiles are still empty."""
    nempty_tile = len(board_inst.empty_tiles)
    print("Iteration:", board_inst.niter, "Number of empty tiles:", nempty_tile)


# Solve the problem
board.solve(callback)

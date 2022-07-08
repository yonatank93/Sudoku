from pathlib import Path
import glob
import copy
import json

import numpy as np

from sudoku import Board

board_files = glob.glob("../data/board_*.json")
exclude_board = ["board_11.json"]

test_board_files = copy.copy(board_files)
for exclude in exclude_board:
    test_board_files = [f for f in test_board_files if exclude not in f]
test_board_files = [Path(f).absolute() for f in test_board_files]


def test_solve():
    for board_file in test_board_files:
        # Load the test data including the board problem and solution
        data = json.load(open(board_file, "r"))
        problem = data["board"]
        solution = data["solution"]

        # Instantiate the board
        board = Board(problem)
        # Solve the problem
        board.solve()

        # Assertion
        assert np.allclose(board.board, solution)


if __name__ == "__main__":
    test_solve()

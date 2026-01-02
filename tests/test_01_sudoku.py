from pathlib import Path
import glob
import copy
import json

import numpy as np

from sudoku import Sudoku


# Define a custom callback function
def callback(board_inst):
    """This callback function will print how many cells are still empty."""
    nempty_cell = len(board_inst.empty_cells)
    print("Iteration:", board_inst.niter, "Number of empty cells:", nempty_cell)


def solve_example_problems(path, exclude_board=[]):
    board_files = sorted(glob.glob(str(Path(path) / "board_*.json")))

    # Exclude some boards if needed
    test_board_files = copy.copy(board_files)
    for exclude in exclude_board:
        test_board_files = [f for f in test_board_files if exclude not in f]
    test_board_files = [Path(f).absolute() for f in test_board_files]

    for board_file in test_board_files:
        print(board_file.name)
        # Load the test data including the board problem and solution
        data = json.load(open(board_file, "r"))
        board = data["board"]
        solution = data["solution"]

        # Instantiate the board
        init_args = {
            "allowed_values": data["allowed_values"],
            "block_dim": data["block_dim"],
        }
        S = Sudoku(board, **init_args)
        # Solve the problem
        S.solve(callback)

        # Assertion
        assert np.allclose(S.board, solution)
        print()


def test_solve_6by6():
    print("Testing 6x6 boards")
    solve_example_problems("../data/6by6")


def test_solve_9by9():
    print("Testing 9x9 boards")
    solve_example_problems("../data/9by9")


def test_solve_16by16():
    print("Testing 16x16 boards")
    solve_example_problems("../data/16by16")


if __name__ == "__main__":
    test_solve_6by6()
    test_solve_9by9()
    test_solve_16by16()

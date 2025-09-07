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


def solve_example_problems(path, exclude_board=[], init_args={}):
    board_files = sorted(glob.glob(str(Path(path) / "board_*.json")))

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
        S = Sudoku(board, **init_args)
        # Solve the problem
        S.solve(callback)

        # Assertion
        assert np.allclose(S.board, solution)
        print()


def test_solve_6by6():
    solve_example_problems(
        "../data/6by6",
        init_args={"allowed_values": list(range(1, 7)), "nblocks_columns": 2},
    )


def test_solve_9by9():
    solve_example_problems(
        "../data/9by9",
        init_args={"allowed_values": list(range(1, 10)), "nblocks_columns": 3},
    )


def test_solve_16by16():
    solve_example_problems(
        "../data/16by16",
        init_args={"allowed_values": list(range(1, 17)), "nblocks_columns": 4},
    )


if __name__ == "__main__":
    test_solve_6by6()
    test_solve_9by9()
    test_solve_16by16()

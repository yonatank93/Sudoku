"""Generate Sudoku problem. This is done by first populating an empty board (all values
are zero) randomly with random numbers between 1 to 9 (inclusive) and solving the problem.
Then, values in the solved board are randomly removed. In this way, the generated board
will be (more likely to be) solvable.
"""

from copy import deepcopy
import numpy as np
from .main import Board
from .utils import _blockPrint, _enablePrint


def _create_initial_board() -> np.ndarray:
    """Create an initial board to solve by populating randomly populating an empty board.

    Returns
    -------
    np.ndarray
        An initial board that is mostly empty, with randomly populated tiles.
    """
    # Randomly populating an empty board
    nvals = np.random.randint(1, 5)
    vals = np.random.randint(1, 10, nvals)
    idx_add = np.random.randint(0, 9, (nvals, 2))
    board_init = np.zeros((9, 9), dtype=int)
    for val, idx in zip(vals, idx_add):
        board_init[idx[0], idx[1]] = val
    return board_init


def _solve_board(board: np.ndarray) -> np.ndarray:
    """Solve the board.

    Returns
    -------
    np.ndarray
        A solved board.
    """
    # Solve the generated board
    B = Board(deepcopy(board))
    B.solve()
    board_solved = B.board
    return board_solved


def _remove_elements(board: np.ndarray, nremove: int) -> np.ndarray:
    """Randomly remove elements from a solved board.

    Parameters
    ----------
    board: np.ndarray
        An array representing a solved board.
    nremove: int
        Number of tiles to remove.

    Returns
    -------
    np.ndarray
        Similar to input solved board, but with random tiles that are empty.
    """
    # Removing random elements
    assert nremove > 0, "You don't want any empty tile? Not fun."
    assert nremove < 81, "Are you sure you want to have an entirely empty board?"
    board_problem = deepcopy(board)
    ii = 0
    while ii < nremove:
        row, col = np.random.randint(0, 9, 2)
        if board_problem[row, col] != 0:
            board_problem[row, col] = 0
            ii += 1
        else:
            continue
    return board_problem


def _get_ntiles_to_remove(level: int) -> int:
    """Get the number of tiles to remove, given the level of problem requested.

    The number of tiles to remove is a random number between (10 * (level-1)), exclusive,
    to (10 * level), inclusive.

    Parameters
    ----------
    level int range(1, 9)
        Requested level of difficulty. Lower number means easier level of difficulty.

    Returns
    -------
    int
        Number of tiles to remove.
    """
    lb = (level - 1) * 10 + 1  # inclusive
    ub = level * 10 + 1  # exclusive
    nremove = np.random.randint(lb, ub)
    return nremove


def generate_problem(level: int = 3) -> np.ndarray:
    """Main function to generate a Sudoku problem board.

    To generate the problem board, we first solve a randomly generated Sudoku board, then
    randomly removing the tiles. The requested level determine the number of empty tiles.
    The number of tiles to remove is a random number between (10 * (level-1)), exclusive,
    to (10 * level), inclusive.

    Parameters
    ----------
    level int range(1, 9)
        Requested level of difficulty. Lower number means easier level of difficulty.

    Returns
    -------
    np.ndarray
        A generated Sudoku problem board.
    """
    assert isinstance(level, int), "Difficulty level can only be an integer number"
    assert 1 <= level <= 8, "Difficulty level ranges from 1 to 8 only"
    while True:
        try:
            _blockPrint()
            # Initially, randomly populate en empty board
            board_init = _create_initial_board()
            # Solve this initial board
            board_solved = _solve_board(board_init)
            # Randomly remove elements from the solved board
            nremove = _get_ntiles_to_remove(level)
            board_problem = _remove_elements(board_solved, nremove)
            _enablePrint()
            break
        except IndexError:
            pass

    return board_problem

"""Generate Sudoku problem. This is done by first populating an empty board (all values
are zero) randomly with random numbers between 1 to 9 (inclusive) and solving the problem.
Then, values in the solved board are randomly removed. In this way, the generated board
will be (more likely to be) solvable.
"""

from copy import deepcopy
import numpy as np
from .board import Board
from .utils import _blockPrint, _enablePrint


def _create_initial_board() -> np.ndarray:
    """Create an initial board to solve by populating randomly populating an empty board.

    Returns
    -------
    np.ndarray
        An initial board that is mostly empty, with randomly populated tiles.
    """
    nums = np.arange(1, 10)  # These are possible numbers in the board
    # Initialize empty board
    board_init = np.zeros((9, 9), dtype=int)
    # Populate row 0
    board_init[0] = np.random.permutation(nums)
    # Populate block 0
    possible_nums = list(set(nums) - set(board_init[0, :3]))
    board_init[1:3, :3] = np.random.permutation(possible_nums).reshape(2, 3)
    # Populate column 0
    possible_nums = list(set(nums) - set(board_init[:3, 0]))
    board_init[3:, 0] = np.random.permutation(possible_nums)
    # Populate block 4
    possible_nums = set(nums) - set(board_init[0, 3:6]) - set(board_init[3:6, 0])
    possible_nums = np.append(
        np.zeros(9 - len(possible_nums), dtype=int), list(possible_nums)
    )  # Zeros padding
    board_init[3:6, 3:6] = np.random.permutation(possible_nums).reshape(3, 3)
    # Populate block 8
    possible_nums = set(nums) - set(board_init[0, 6:]) - set(board_init[6:, 0])
    possible_nums = np.append(
        np.zeros(9 - len(possible_nums), dtype=int), list(possible_nums)
    )  # Zeros padding
    board_init[6:, 6:] = np.random.permutation(possible_nums).reshape(3, 3)

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

    Here, we decide on the maximum and minimum number of tiles to retain in the board,
    then we partition the range into bins, each corresponding to a lower bound and upper
    bound of the number of tiles to remove for each level. For a given level, the number
    of tiles removed is a random number between this lower and upper bounds, with some
    small padding to separate difficulty of subsequent levels.

    Parameters
    ----------
    level: int range(1, 5)
        Requested level of difficulty. Lower number means easier level of difficulty.

    Returns
    -------
    int
        Number of tiles to remove.
    """
    pad = 3  # Padding to make subsequent levels more distinct
    # These are the maximum and minimum number of tiles retained in the board
    min_retained = 15 - pad  # Exclusive
    max_retained = 70 + pad  # Inclusive
    # These are the minimum and maximum number of tiles to remove
    min_removed = 81 - max_retained
    max_removed = 81 - min_retained
    nbins = 5  # Level ranges from 1 to 10 (both inclusive)
    # Compute bins
    bin_edges = np.linspace(min_removed, max_removed, nbins + 1)
    bins = [
        (int(np.round(bin_edges[i]) + 3), int(np.round(bin_edges[i + 1])) - 3)
        for i in range(len(bin_edges) - 1)
    ]
    # Given level, we randomly select the number of tiles to remove
    lb, ub = bins[level - 1]
    nremove = np.random.randint(lb, ub)
    return nremove


def generate_problem(level: int = 3) -> np.ndarray:
    """Main function to generate a Sudoku problem board.

    To generate the problem board, we first solve a randomly generated Sudoku board, then
    randomly removing the tiles. The requested level determine the number of empty tiles.

    Parameters
    ----------
    level: int range(1, 5)
        Requested level of difficulty. Lower number means easier level of difficulty.

    Returns
    -------
    np.ndarray
        A generated Sudoku problem board.
    """
    assert isinstance(level, int), "Difficulty level can only be an integer number"
    assert 1 <= level <= 5, "Difficulty level ranges from 1 to 5 only"
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

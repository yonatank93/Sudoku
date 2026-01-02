"""Generate Sudoku problem. This is done by first populating an empty board
(all values are zero) randomly with random numbers within the allowed values
and solving the problem.
Then, values in the solved board are randomly removed. In this way, the
generated board will be (more likely to be) solvable.
"""

import random
from copy import deepcopy
from typing import Union
import numpy as np


def is_valid(
    board: list, row: int, col: int, value: Union[int, str], block_dim: tuple
) -> bool:
    """Check if placing a value in a cell is valid according to Sudoku rules.

    Parameters
    ----------
    board: list
        Current state of the Sudoku board.
    row: int
        Row index of the cell to check.
    col: int
        Column index of the cell to check.
    value: int or str
        Value to place in the cell.
    block_dim: tuple
        A tuple indicating the block dimensions, i.e., number of rows and
        columns in each block.

    Returns
    -------
    bool
        True if placing the value is valid, False otherwise.
    """
    # Check row
    if value in board[row]:
        return False

    # Check column
    for r in range(len(board)):
        if board[r][col] == value:
            return False

    # Check block
    start_r = (row // block_dim[0]) * block_dim[0]
    start_c = (col // block_dim[1]) * block_dim[1]
    for r in range(start_r, start_r + block_dim[0]):
        for c in range(start_c, start_c + block_dim[1]):
            if board[r][c] == value:
                return False

    return True


def find_empty(board: list) -> tuple:
    """Find an empty cell in the Sudoku board.

    Parameters
    ----------
    board: list
        Current state of the Sudoku board.

    Returns
    -------
    tuple
        Row and column indices of the first empty cell found.
    """
    N = len(board)
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return r, c
    return None


def fill_board(board: list, allowed_values: list, block_dim: tuple) -> bool:
    """Main backtracking function to fill the Sudoku board.

    Parameters
    ----------
    board: list
        Current state of the Sudoku board.
    allowed_values: set-like
        A set of allowed values in the Sudoku board.
    block_dim: tuple
        A tuple indicating the block dimensions, i.e., number of rows and
        columns in each block.

    Returns
    -------
    bool
        True if the board is successfully filled, False otherwise.

    Notes
    -----
    This function overwrites the input board in place.
    """
    cell = find_empty(board)
    if not cell:
        return True

    r, c = cell
    nums = allowed_values
    random.shuffle(nums)

    for num in nums:
        if is_valid(board, r, c, num, block_dim):
            board[r][c] = num
            if fill_board(board, allowed_values, block_dim):
                return True
            board[r][c] = 0

    return False


def generate_full_solution(allowed_values: list, block_dim: tuple) -> list:
    """Generate a fully solved Sudoku board using backtracking.

    Parameters
    ----------
    allowed_values: set-like, optional
        A set of allowed values in the Sudoku board. The default is a set of
        integers from 1 to 9, inclusive, which is the normal Sudoku setup.
    block_dim: tuple, optional
        A tuple indicating the block dimensions, i.e., number of rows and
        columns in each block. The default is (3, 3), which is the normal
        Sudoku setup.

    Returns
    -------
    list
        A fully solved Sudoku board.
    """
    # Start with an empty board
    nallowed_values = len(allowed_values)
    board = [
        [0 for _ in range(nallowed_values)] for _ in range(nallowed_values)
    ]
    fill_board(board, allowed_values, block_dim)
    return board


def _remove_elements(board: list, nremove: int) -> np.ndarray:
    """Randomly remove elements from a solved board.

    Parameters
    ----------
    board: list
        Filled sudoku board.
    nremove: int
        Number of cells to remove.

    Returns
    -------
    np.ndarray
        Similar to input solved board, but with random cells that are empty.
    """
    nvals = len(board)  # The same as number of allowed values
    # Removing random elements
    assert nremove > 0, "You don't want any empty cell? Not fun."
    assert (
        nremove < nvals**2
    ), "Are you sure you want to have an entirely empty board?"
    board_problem = deepcopy(board)

    # List of all cell positions and shuffle them
    cells = [(r, c) for r in range(nvals) for c in range(nvals)]
    random.shuffle(cells)

    for ii in range(nremove):
        row, col = cells[ii]
        board_problem[row][col] = 0
    return board_problem


def _get_ncells_to_remove(level: int, nallowed_values: int) -> int:
    """Get the number of cells to remove, given the level of problem requested.

    Here, we decide on the maximum and minimum number of cells to retain in the
    board, then we partition the range into bins, each corresponding to a lower
    bound and upper bound of the number of cells to remove for each level. For
    a given level, the number of cells removed is a random number between this
    lower and upper bounds, with some small padding to separate difficulty of
    subsequent levels.

    Parameters
    ----------
    level: int range(1, 5)
        Requested level of difficulty. Lower number means easier level of
        difficulty.
    nallowed_values: int
        Number of allowed values in the Sudoku board, e.g., 81 for 9-by-9 board.

    Returns
    -------
    int
        Number of cells to remove.
    """
    ncells = nallowed_values**2
    if ncells > 4:
        # Padding to make subsequent levels more distinct
        pad = int(np.sqrt(nallowed_values))
    else:
        # If the board is too small, no padding
        pad = 0
    # These are the maximum and minimum number of cells retained in the board
    min_retained = int(np.floor(0.1 * ncells))  # Exclusive
    max_retained = int(np.ceil(0.9 * ncells))  # Inclusive
    # These are the minimum and maximum number of cells to remove
    min_removed = ncells - max_retained
    max_removed = ncells - min_retained
    nbins = 5  # Level ranges from 1 to 5 (both inclusive)
    # Compute bins
    bin_edges = np.linspace(min_removed, max_removed, nbins + 1)
    bins = [
        (
            int(np.floor(bin_edges[i]) + pad),
            int(np.ceil(bin_edges[i + 1])) - pad,
        )
        for i in range(len(bin_edges) - 1)
    ]
    # Given level, we randomly select the number of cells to remove
    lb, ub = bins[level - 1]
    if ub > lb:
        nremove = np.random.randint(lb, ub)
    else:
        # This is when the board is too small, so that the padded bins might
        # have same lower and upper bounds, or even upper bound is smaller than
        # lower bound. In this case, we just set the number of cells to remove
        # to be the smaller value.
        nremove = min([lb, ub])
    return nremove


def generate_problem(
    level: int = 3,
    allowed_values: list = range(1, 10),
    block_dim: tuple = (3, 3),
    verbose: bool = True,
    return_solution: bool = False,
) -> list:
    """Main function to generate a Sudoku problem board.

    To generate the problem board, we first generate a solved Sudoku board
    using a backtracking algorithm, then randomly removing the cells. The
    requested level determine the number of empty cells.

    Parameters
    ----------
    level: int range(1, 5)
        Requested level of difficulty. Lower number means easier level of
        difficulty.
    allowed_values: set-like, optional
        A set of allowed values in the Sudoku board. The default is a set of
        integers from 1 to 9, inclusive, which is the normal Sudoku setup.
    block_dim: tuple, optional
        A tuple indicating the block dimensions, i.e., number of rows and
        columns in each block. The default is (3, 3), which is the normal
        Sudoku setup.
    verbose: bool, optional
        Whether to print progress messages. The default is True.
    return_solution: bool, optional
        Whether to return the generated solution along with the problem.

    Returns
    -------
    np.ndarray
        A generated Sudoku problem board.
    """
    assert isinstance(
        level, int
    ), "Difficulty level can only be an integer number"
    assert 1 <= level <= 5, "Difficulty level ranges from 1 to 5 only"
    # We allow allowed_values to be a string, but we need to convert it to a
    # list
    if isinstance(allowed_values, str):
        allowed_values = [val for val in allowed_values]
    elif isinstance(allowed_values, set):
        allowed_values = list(allowed_values)
    elif isinstance(allowed_values, range):
        allowed_values = list(allowed_values)

    # Generate a full solution first
    if verbose:
        print("Generating full solution...")
    solution = generate_full_solution(allowed_values, block_dim)
    # Randomly remove elements according to the requested level
    if verbose:
        print("Creating problem by removing elements...")
    nremove = _get_ncells_to_remove(level, len(allowed_values))
    board_problem = _remove_elements(solution, nremove)
    if verbose:
        print("Problem generated.")

    if return_solution:
        return board_problem, solution
    else:
        return board_problem


if __name__ == "__main__":
    problem, solution = generate_problem(level=3)

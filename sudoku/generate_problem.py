"""Generate Sudoku problem. This is done by first populating an empty board
(all values are zero) randomly with random numbers within the allowed values
and solving the problem.
Then, values in the solved board are randomly removed. In this way, the
generated board will be (more likely to be) solvable.
"""

from copy import deepcopy
import numpy as np
from .sudoku import Sudoku
from .cell import Cell
from .utils import _blockPrint, _enablePrint


def _create_initial_board(
    allowed_values: list, nblocks_rows: int, nblocks_columns: int
) -> np.ndarray:
    """Create an initial board to solve.

    This is done by populating the first row, first column, and nonoverlapping
    blocks that form a diagonal from top-left to bottom-right of the board with
    randomly selected values from the list of allowed values of each cell. The
    rest of the cells are left empty (zero). The resulting board forms a
    starting point to generate a solvable problem.

    This approach of populating the board is more likely to produce a solvable
    board than populating random cells in the board. However, it still doesn't
    guarantee that the resulting board is solvable.

    Parameters
    ----------
    allowed_values: set-like, optional
        A set of allowed values in the Sudoku board.
    nblocks_columns: int, optional
        Number of blocks in each column.
    nblocks_rows: int, optional
        Number of blocks in each row.

    Returns
    -------
    np.ndarray
        An initial board that is mostly empty, with randomly populated cells.
    """
    nallowed_values = len(allowed_values)
    nblocks = nblocks_rows * nblocks_columns
    # Initialize empty board
    board_init = np.zeros((nallowed_values, nallowed_values), dtype=int)
    # Indices of the blocks that do not overlap in rows and columns -
    # Populating these blocks randomly will increase the chance of generating
    # a solvable board.
    nonoverlapping_blocks_idx = np.arange(nblocks)[:: (nblocks_columns + 1)]

    # Populate the board
    for ii in range(nallowed_values):
        for jj in range(nallowed_values):
            cell = Cell(
                board_init,
                [ii, jj],
                allowed_values,
                nblocks_rows,
                nblocks_columns,
            )

            block_idx = cell.block_idx
            possible_values = cell.possible_values

            if ii == 0:
                # First row
                populate = True
            elif jj == 0:
                # First column
                populate = True
            elif block_idx in nonoverlapping_blocks_idx:
                # First block
                populate = True
            else:
                populate = False

            if populate:
                # In some cases, there might be no possible values to populate,
                # which indicate that the board is not solvable.
                worth_trying = len(possible_values) > 0
                if worth_trying > 0:
                    board_init[ii, jj] = np.random.choice(possible_values)

    return board_init, worth_trying


def _solve_board(
    board: np.ndarray,
    allowed_values: list,
    nblocks_rows: int,
    nblocks_columns: int,
) -> np.ndarray:
    """Solve the board.

    Parameters
    ----------
    allowed_values: set-like, optional
        A set of allowed values in the Sudoku board.
    nblocks_columns: int, optional
        Number of blocks in each column.
    nblocks_rows: int, optional
        Number of blocks in each row.

    Returns
    -------
    np.ndarray
        A solved board.
    """
    # Solve the generated board
    B = Sudoku(deepcopy(board), allowed_values, nblocks_rows, nblocks_columns)
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
    ii = 0
    while ii < nremove:
        row, col = np.random.randint(0, nvals, 2)
        if board_problem[row, col] != 0:
            board_problem[row, col] = 0
            ii += 1
        else:
            continue
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
    nblocks_rows: int = 3,
    nblocks_columns: int = 3,
    verbose: bool = True,
) -> np.ndarray:
    """Main function to generate a Sudoku problem board.

    To generate the problem board, we first solve a randomly generated Sudoku
    board, then randomly removing the cells. The requested level determine the
    number of empty cells.

    Parameters
    ----------
    level: int range(1, 5)
        Requested level of difficulty. Lower number means easier level of
        difficulty.
    allowed_values: set-like, optional
        A set of allowed values in the Sudoku board. The default is a set of
        integers from 1 to 9, inclusive, which is the normal Sudoku setup.
    nblocks_columns: int, optional
        Number of blocks in each column. The default is 3, which is the normal
        Sudoku setup.
    nblocks_rows: int, optional
        Number of blocks in each row. The default is 3, which is the normal
        Sudoku setup.
    verbose: bool, optional
        Whether to print progress messages. The default is True.

    Returns
    -------
    np.ndarray
        A generated Sudoku problem board.
    """
    assert isinstance(
        level, int
    ), "Difficulty level can only be an integer number"
    assert 1 <= level <= 5, "Difficulty level ranges from 1 to 5 only"
    while True:
        try:
            # _blockPrint()
            # Initially, randomly populate en empty board
            if verbose:
                print("Generating random problem...")
            board_init, worth_trying = _create_initial_board(
                allowed_values, nblocks_rows, nblocks_columns
            )
            if worth_trying:
                print("Check if the problem is solvable...")
                # Try to solve this initial board to make sure that the problem
                # is solvable
                board_solved = _solve_board(
                    board_init, allowed_values, nblocks_rows, nblocks_columns
                )
                # Randomly remove elements from the solved board
                print("Finalizing the problem...")
                nremove = _get_ncells_to_remove(level, len(allowed_values))
                board_problem = _remove_elements(board_solved, nremove)
                # _enablePrint()
                break
            else:
                if verbose:
                    print("Failed to generate a solvable problem. Retrying...")
                pass
        except IndexError:
            if verbose:
                print("Failed to generate a solvable problem. Retrying...")
            pass

    return board_problem

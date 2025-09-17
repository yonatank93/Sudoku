import copy
import random
import time
from datetime import timedelta
from typing import List, Sequence, Callable, Dict

import numpy as np

from sudoku.cell import Cell
from sudoku.groups import Row, Column, Block

default_allowed_values = set(range(1, 10))


def default_callback(board):
    """A default callback function that is called after each iteration in the
    main while loop in :meth:`~sudoku.Board.solve`. It can be used to
    monitor the progress, e.g., by printing the number of empty cells in the
    board. The default behavior does nothing.

    Parameters
    ----------
    board: :class:`~sudoku.Board` instance.
        Instance of the Sudoku board class.
    """
    pass


class Sudoku:
    """A main class to define the Sudoku problem and solve it.

    Parameters
    ----------
    board: array-like
        An array that represent the Sudoku problem. It is represented by a
        square array-like, where the elements of the array give show the value
        in each corresponding cell. The value of zero means that the cell is
        empty.
    allowed_values: set-like, optional
        A set of allowed values in the Sudoku board. The default is a set of
        integers from 1 to 9, inclusive, which is the normal Sudoku setup.
    nblocks_columns: int, optional
        Number of blocks in each column. The default is 3, which is the normal
        Sudoku setup.
    nblocks_rows: int, optional
        Number of blocks in each row. The default is 3, which is the normal
        Sudoku setup.

    Attributes
    ----------
    board: np.ndarray
        An array that represent the Sudoku board. This array is mutated during
        the solving process, and can be called to access the solved board.
    orig_board: np.ndarray
        An array that represent the initial state of the Sudoku board that
        shows the problem.

    Notes
    -----
    We will call a block to refer to a :math:`3 \times 3` block in which no
    numbers can be repeated in that block.
    """

    def __init__(
        self,
        board=None,
        allowed_values=default_allowed_values,
        nblocks_rows=None,
        nblocks_columns=None,
    ):
        self.allowed_values = set(allowed_values)
        self._nallowed_values = len(self.allowed_values)

        if (nblocks_columns is None) and (nblocks_rows is None):
            if len(self.allowed_values) == len(default_allowed_values):
                # Default to the normal Sudoku setup
                self.nblocks_rows = 3
                self.nblocks_columns = 3
            else:
                raise ValueError(
                    "Either nblocks_columns or nblocks_rows must be set."
                )

        if nblocks_rows is not None:
            self.nblocks_rows = nblocks_rows
            if nblocks_columns is None:
                self.nblocks_columns = (
                    self._nallowed_values // self.nblocks_rows
                )
            else:
                self.nblocks_columns = nblocks_columns
        if nblocks_columns is not None:
            self.nblocks_columns = nblocks_columns
            if nblocks_rows is None:
                self.nblocks_rows = (
                    self._nallowed_values // self.nblocks_columns
                )
            else:
                self.nblocks_rows = nblocks_rows
        self._nblocks = self.nblocks_rows * self.nblocks_columns

        # Some checks
        assert self._nallowed_values % self.nblocks_columns == 0, (
            f"Number of values ({self._nallowed_values}) is not divisible by "
            f"nblocks_columns={self.nblocks_columns}"
        )

        assert self._nallowed_values % self.nblocks_rows == 0, (
            f"Number of values ({self._nallowed_values}) is not divisible by "
            f"nblocks_rows={self.nblocks_rows}"
        )

        # Initializations
        self._board = None
        self.orig_board = copy.copy(board)
        self._intermediate_state = {}
        self.niter = 0

        # Set the board
        if board is not None:
            self.board = board

    @property
    def board(self) -> np.ndarray:
        """Return the Sudoku board."""
        return self._board

    @board.setter
    def board(self, board: np.ndarray) -> None:
        """Set the Sudoku board.

        Parameters
        ----------
        board: array-like
            An array that represent the Sudoku problem. It is represented by a
            square array-like with the dimension equals to the length of
            allowed values.
            The elements of the array give the value in each cell, and value of
            zero means that the cell is empty.
        """
        board = np.array(board)

        # Check if the board has the correct shape
        assert board.shape == (
            self._nallowed_values,
            self._nallowed_values,
        ), (
            "The board should be a "
            f"{self._nallowed_values}x{self._nallowed_values} array-like",
        )
        # Check if the values in the given board are valid
        unique_board_values = [
            val for val in np.unique(board.flatten()) if val != 0
        ]
        values_not_allowed = [
            val for val in unique_board_values if val not in self.allowed_values
        ]
        assert len(values_not_allowed) == 0, (
            f"The board contains values ({values_not_allowed}) that are not "
            f"in the allowed values ({self.allowed_values})."
        )

        self._board = np.asarray(board)
        self.validate_board()
        if self.orig_board is None:
            self.orig_board = copy.copy(board)

    def validate_board(self):
        """Validate the board by checking if there is any repeated, non-zero
        values within the groups (rows, columns, and blocks)
        """
        groups_collection = [self.rows, self.columns, self.blocks]
        for groups in groups_collection:
            for ii, group in enumerate(groups):
                nonzero_vals = [val for val in group.values if val != 0]
                assert len(nonzero_vals) == len(
                    set(nonzero_vals)
                ), f"Board is invalid; there is a repetition in {group}"

    def update_board_value(self, val: float, cell: Cell):
        board = copy.copy(self.board)
        board[cell.row_idx, cell.column_idx] = val
        self.board = board

    @property
    def rows(self) -> List[Row]:
        """A list of Row's in the board.

        Returns
        -------
        rows: list
            A list that contains :class:`~sudoku.groups.Row` for each row in
            the board.
        """
        return [
            Row(self.board, idx, self.allowed_values)
            for idx in range(self._nallowed_values)
        ]

    @property
    def columns(self) -> List[Column]:
        """A list of Column's in the board.

        Returns
        -------
        columns: list
            A list that contains :class:`~sudoku.groups.Column` for each column
            in the board.
        """
        return [
            Column(self.board, idx, self.allowed_values)
            for idx in range(self._nallowed_values)
        ]

    @property
    def blocks(self) -> List[Block]:
        """A list of Block's in the board.

        Returns
        -------
        blocks: list
            A list that contains :class:`~sudoku.groups.Block` for each block
            in the board.
        """
        return [
            Block(
                self.board,
                idx,
                (
                    self._nallowed_values // self.nblocks_rows,
                    self._nallowed_values // self.nblocks_columns,
                ),
                self.allowed_values,
            )
            for idx in range(self._nblocks)
        ]

    @property
    def cells(self) -> np.array:
        """Return the cells in a 2D array.

        Returns
        -------
        cells: np.ndarray
            A 2D array of the same shape as the board that contains
            :class:`~sudoku.cell.Cell` for each cell in the board.
        """
        return np.array(self._cells_flatten).reshape(self.board.shape)

    @property
    def _cells_flatten(self) -> List[Cell]:
        """Scan the board and create :class:`~sudoku.cell.Cell` instances.

        Returns
        -------
        cells: list
            A list that contains :class:`~sudoku.cell.Cell` for each cell in
            the board.
        """
        cells = [
            Cell(
                self.board,
                [row, col],
                self.allowed_values,
                self.nblocks_rows,
                self.nblocks_columns,
            )
            for row in range(self._nallowed_values)
            for col in range(self._nallowed_values)
        ]
        return cells

    def get_empty_cells(self, fmt="list") -> Sequence[Cell]:
        """List all the empty cells."""
        if fmt == "list":
            return [cell for cell in self._cells_flatten if cell.is_empty]
        elif fmt == "dict":
            return {
                ii: cell
                for ii, cell in enumerate(self._cells_flatten)
                if cell.is_empty
            }

    def _count_occurence(self) -> Sequence[int]:
        """Count how many time each allowed value shows up in the board."""
        occur = []
        for val in self.allowed_values:
            occur.append(np.sum(self.board == val))
        return occur

    @property
    def solved(self) -> bool:
        """Check if the board is solved."""
        noccur = self._count_occurence()
        if len(self.get_empty_cells()) == 0 and np.all(
            [occ == self._nallowed_values for occ in noccur]
        ):
            return True
        else:
            return False

    def solve(
        self,
        return_board: bool = True,
        callback: Callable = default_callback,
        verbose: bool = False,
    ):
        """Main method to solve the Sudoku problem."""

        start_time = time.perf_counter()
        while not self.solved:
            self.step(verbose)
            callback(self)
        finish_time = time.perf_counter()
        if verbose:
            print("Solving time:", timedelta(seconds=finish_time - start_time))
        if return_board:
            return self.board

    def step(self, verbose: bool = False):
        """Run one step of the algorithm."""

        # Try updating the cells by looking up and comparing the lists of
        # possible values.
        old_cells = copy.copy(self._cells_flatten)  # Cells before the update
        self._update_cells()
        new_cells = copy.copy(self._cells_flatten)  # Cells after the update
        if verbose:
            print(
                f"Iteration {self.niter}: "
                f"{len(self.get_empty_cells())} empty cells left."
            )

        # Compare the cells before and after the update. If the above algorithm
        # fails to update the cells, then try setting one of the cell to a
        # value.
        if self._cells_same(old_cells, new_cells):
            empty_cells_dict = self.get_empty_cells(fmt="dict")
            nposs_vals = [
                len(cell.possible_values) for cell in empty_cells_dict.values()
            ]

            # Check if the attempt failed - This can be done if any empty cell
            # has no possible value.
            if 0 in nposs_vals:
                # The trial fails and need to be reset to the previous cached
                # state. After that, we will try other value to test. So, the
                # previous cached state doesn't need to be popped.
                self._revert_state()
                if verbose:
                    print(f"Search fails, reverting to iteration {self.niter}")
                # Counter the iteration increment below
                self.niter -= 1

            else:
                idx_sort = np.argsort(nposs_vals)
                key_sorted = np.array(list(empty_cells_dict))[idx_sort]
                empty_cells_dict = {
                    ii: empty_cells_dict[ii] for ii in key_sorted
                }
                self._update_intermediate_state(empty_cells_dict)

                # Retrieve data from the last intermediate state
                last_state = self._intermediate_state[self.niter]
                for ii, val in last_state["test_cells"].items():
                    cell = empty_cells_dict[ii]
                    new_vals = set(cell.possible_values) - set(val)
                    if new_vals:
                        value = next(iter(new_vals))
                        self.update_board_value(value, cell)
                        if verbose:
                            print(
                                f"Try setting cell [{cell.row_idx}, "
                                f"{cell.column_idx}] to {value} "
                                f"(possible values: {cell.possible_values})"
                            )
                        break

                    if ii == key_sorted[-1]:
                        # We have exhausted all possible cells and values. Need
                        # to go back 2 steps above. We can't just go back one
                        # step, because we have already tried all possible
                        # values.
                        # Go back one step and delete the cached state.
                        self._revert_state(pop=True)
                        # Go back to the second previous state and start the
                        # test from this state
                        self._revert_state()

                        if verbose:
                            print(
                                "No more values to try, "
                                f"reverting to iteration {self.niter}"
                            )
                        # Counter the iteration increment below
                        self.niter -= 1

        self.niter += 1

    def _update_cells(self):
        """Update the cells values."""
        # When the cell only has one possible value
        self._update_cells_from_single_possible_value()
        # Another option is to look if there is any value that can only go into
        # a specific cell, i.e., there is only one occurence in the list of
        # possible values
        for block in range(self._nblocks):
            cells_block = [
                cell
                for cell in self._cells_flatten
                if cell.block_idx == block and cell.is_empty
            ]
            self._update_cells_from_single_possible_occurence(cells_block)
        for row in range(self._nallowed_values):
            cells_row = [
                cell
                for cell in self._cells_flatten
                if cell.row_idx == row and cell.is_empty
            ]
            self._update_cells_from_single_possible_occurence(cells_row)
        for column in range(self._nallowed_values):
            cells_column = [
                cell
                for cell in self._cells_flatten
                if cell.column_idx == column and cell.is_empty
            ]
            self._update_cells_from_single_possible_occurence(cells_column)

    def _update_cells_from_single_possible_value(self):
        """Update the cells that have only one possible value."""
        ncells = len(self._cells_flatten)
        while True:
            n = 0
            for ii in range(ncells):
                cell = self._cells_flatten[ii]
                if cell.is_empty:
                    if len(cell.possible_values) == 1:
                        # There is only 1 possible value that can go into this
                        # empty cell
                        self.update_board_value(cell.possible_values[0], cell)
                        n += 1
            if n == 0:
                break

    def _update_cells_from_single_possible_occurence(
        self, cells_group: Sequence[Cell]
    ):
        """Look at a single group (block, row, or column) and see if we can
        solve any in that group by looking if there is a value in the list of
        possible values of an empty cell that is not in the list of possible
        values in other empty cells within the same group. If such value
        exists, then we can only put that value in that cell.
        """
        for cell in cells_group:
            for val in cell.possible_values:
                val_in_other_cell = False
                for cl in cells_group:
                    if cl != cell:
                        if val in cl.possible_values:
                            val_in_other_cell = True
                            break
                if not val_in_other_cell:
                    self.update_board_value(val, cell)
                    break

    def _update_intermediate_state(self, test_cells: Dict[int, Cell]):
        """Update the information of the intermediate state."""
        self._intermediate_state.setdefault(
            self.niter, {"board": self.board.copy(), "test_cells": {}}
        )

        for ii, cell in test_cells.items():
            self._intermediate_state[self.niter]["test_cells"].setdefault(
                ii, []
            )

            test_values = cell.possible_values.copy()
            tried_values = self._intermediate_state[self.niter]["test_cells"][
                ii
            ]
            for val in test_values:
                if val not in tried_values:
                    self._intermediate_state[self.niter]["test_cells"][
                        ii
                    ].append(val)
                    break

    def _revert_state(self, pop=False):
        """Revert to the previous state."""
        # Revert the previous state
        self.niter = list(self._intermediate_state)[-1]
        self.board = self._intermediate_state[self.niter]["board"]
        if pop:
            self._intermediate_state.pop(self.niter)

    def _cells_same(self, cells1: Sequence[Cell], cells2: Sequence[Cell]):
        """Compare the cells, check if they are the same."""
        cells1_dict = self._cells_to_dict_possible_values(cells1)
        cells2_dict = self._cells_to_dict_possible_values(cells2)
        return cells1_dict == cells2_dict

    @staticmethod
    def _cells_to_dict_possible_values(cells: Sequence[Cell]) -> Dict:
        """Convert the list of cells into dictionary. The dictionary only
        contains the possible values.
        """
        cells_dict = {}
        for cell in cells:
            if cell.is_empty:
                cells_dict.update(
                    {(cell.row_idx, cell.column_idx): cell.possible_values}
                )
        return cells_dict

    # def display(self):
    #     """Display the Sudoku board."""
    #     print("#" * 37)
    #     for ii in range(self.nblocks_rows):
    #         rows = self.board[(ii * 3) : ((ii + 1) * 3)]
    #         for jj, row in enumerate(rows):
    #             self._print_one_row(row)
    #             if jj < 2:
    #                 print("#" + ("-" * 11 + "#") * 3)
    #         print("#" * 37)

    # @staticmethod
    # def _print_one_row(row_array):
    #     """Print one row of the board."""
    #     b = [str(el) if el != 0 else " " for el in row_array]
    #     print(
    #         "#"
    #         + f" {b[0]} | {b[1]} | {b[2]} "
    #         + "#"
    #         + f" {b[3]} | {b[4]} | {b[5]} "
    #         + "#"
    #         + f" {b[6]} | {b[7]} | {b[8]} "
    #         + "#"
    #     )

    def display(self):
        """Temporary display method until the old style is back."""
        print(self.board)

    def reset(self):
        """Reset the Sudoku problem."""
        self.board = self.orig_board
        self._intermediate_state = {}
        self.niter = 0

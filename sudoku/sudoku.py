import pickle
import copy
import time
from datetime import timedelta
from typing import List, Sequence, Callable, Dict, Union

import numpy as np

from sudoku.cell import Cell, empty_cell_repr
from sudoku.groups import Row, Column, Block

default_allowed_values = range(1, 10)


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
        An array-like that represent the Sudoku problem. It is represented by a
        square array-like, where the elements of the array give show the value
        in each corresponding cell. The value of zero means that the cell is
        empty.
    allowed_values: set-like, optional
        A set of allowed values in the Sudoku board. The default is a set of
        integers from 1 to 9, inclusive, which is the normal Sudoku setup.
    block_dim: tuple, optional
        A tuple that represent the dimension (height, width) of each block. The
        default is (3, 3), which is the normal Sudoku setup.

    Attributes
    ----------
    board: array-like
        An array-like that represent the Sudoku board. This array is mutated
        during the solving process, and can be called to access the solved
        board.
    orig_board: array-like
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
        block_dim=(3, 3),
    ):
        self.allowed_values = (
            [val for val in allowed_values]
            if isinstance(allowed_values, str)
            else allowed_values
        )
        self._nallowed_values = len(self.allowed_values)
        assert self._nallowed_values > 0, "The allowed values cannot be empty."
        assert len(self.allowed_values) == len(
            set(self.allowed_values)
        ), "The allowed values should not contain duplicates."

        # Check block dimensions
        self.block_dim = block_dim
        self._nblocks = self.block_dim[0] * self.block_dim[1]
        assert self._nblocks == self._nallowed_values, (
            "The dimension of block is incorrect. "
            "The product of the dimensions must equal to the number of allowed values."
        )

        # Initializations
        self._board = None
        self.orig_board = copy.deepcopy(board)
        self._intermediate_state = {}
        self.niter = 0
        self._nstep_call = 0

        # Set the board
        if board is not None:
            self.board = copy.deepcopy(board)

    @property
    def board(self) -> Union[list, np.ndarray]:
        """Return the Sudoku board."""
        return self._board

    @board.setter
    def board(self, board: Union[list, np.ndarray]) -> None:
        """Set the Sudoku board.

        Parameters
        ----------
        board: array-like
            An array-like that represent the Sudoku problem. It is represented
            by a square array-like with the dimension equals to the length of
            allowed values.
            The elements of the array give the value in each cell, and value of
            zero means that the cell is empty.
        """
        # Convert the format as necessary
        _board = []
        for rows in board:
            if isinstance(rows, str):
                _board.append([val for val in rows])
            else:
                _board.append(rows)
        board = copy.deepcopy(_board)
        # Check if the board has the correct shape
        assert np.array(board).shape == (
            self._nallowed_values,
            self._nallowed_values,
        ), (
            "The board should be a "
            f"{self._nallowed_values}x{self._nallowed_values} array-like",
        )
        # Check if the values in the given board are valid
        unique_board_values = list(
            set(
                [el for row in board for el in row if el not in empty_cell_repr]
            )
        )
        values_not_allowed = [
            val for val in unique_board_values if val not in self.allowed_values
        ]
        assert len(values_not_allowed) == 0, (
            f"The board contains values ({values_not_allowed}) that are not "
            f"in the allowed values ({self.allowed_values})."
        )

        self._board = copy.deepcopy(board)
        self.validate_board()
        if self.orig_board is None:
            self.orig_board = copy.deepcopy(board)

    def validate_board(self):
        """Validate the board by checking if there is any repeated, non-zero
        values within the groups (rows, columns, and blocks)
        """
        groups_collection = [self.rows, self.columns, self.blocks]
        for groups in groups_collection:
            for ii, group in enumerate(groups):
                nonzero_vals = [
                    val for val in group.values if val not in empty_cell_repr
                ]
                assert len(nonzero_vals) == len(
                    set(nonzero_vals)
                ), f"Board is invalid; there is a repetition in {group}"

    def update_board_value(self, val: float, cell: Cell):
        board = copy.deepcopy(self.board)
        board[cell.row_idx][cell.column_idx] = val
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
                self.block_dim,
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
        return np.array(self._cells_flatten).reshape(np.array(self.board).shape)

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
            Cell(self.board, [row, col], self.allowed_values, self.block_dim)
            for row in range(self._nallowed_values)
            for col in range(self._nallowed_values)
        ]
        return cells

    def _get_empty_cells(self, fmt="list") -> Sequence[Cell]:
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
            occur.append(sum(cell == val for row in self.board for cell in row))
        return occur

    @property
    def solved(self) -> bool:
        """Check if the board is solved."""
        noccur = self._count_occurence()
        if len(self._get_empty_cells()) == 0 and np.all(
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
        """Run one step of the algorithm.

        Each step can only be one attempt to update the board from a single
        occuring value or testing to set a cell to a value, but not both
        """

        # Try updating the cells by looking up and comparing the lists of
        # possible values.
        old_cells = copy.deepcopy(
            self._cells_flatten
        )  # Cells before the update
        self._update_cells()
        new_cells = copy.deepcopy(self._cells_flatten)  # Cells after the update
        if verbose:
            print(
                f"Iteration {self.niter}: "
                f"{len(self._get_empty_cells())} empty cells left."
            )

        # Compare the cells before and after the update. If the above algorithm
        # fails to update the cells, then try setting one of the cell to a
        # value.
        if self._cells_same(old_cells, new_cells):
            empty_cells_dict = self._get_empty_cells(fmt="dict")
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
                key_sorted = [list(empty_cells_dict)[ii] for ii in idx_sort]
                empty_cells_dict = {
                    ii: empty_cells_dict[ii] for ii in key_sorted
                }
                self._update_intermediate_state(empty_cells_dict)

                # Retrieve data from the last intermediate state
                last_state = self._intermediate_state[self.niter]
                ii = list(last_state["test_cells"])[-1]
                if ii == "EOL":
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

                else:
                    val = last_state["test_cells"][ii]
                    # for ii, val in last_state["test_cells"].items():
                    cell = empty_cells_dict[ii]
                    new_vals = sorted(
                        list(set(cell.possible_values) - set(val[:-1]))
                    )
                    if new_vals:
                        value = new_vals[0]
                        self.update_board_value(value, cell)
                        if verbose:
                            print(
                                f"Try setting cell [{cell.row_idx}, "
                                f"{cell.column_idx}] to {value} "
                                f"(possible values: {cell.possible_values})"
                            )
                #     break

                # if ii == key_sorted[-1]:
                #     # We have exhausted all possible cells and values. Need
                #     # to go back 2 steps above. We can't just go back one
                #     # step, because we have already tried all possible
                #     # values.
                #     # Go back one step and delete the cached state.
                #     self._revert_state(pop=True)
                #     # Go back to the second previous state and start the
                #     # test from this state
                #     self._revert_state()

                #     if verbose:
                #         print(
                #             "No more values to try, "
                #             f"reverting to iteration {self.niter}"
                #         )
                #     # Counter the iteration increment below
                #     self.niter -= 1

        self.niter += 1
        self._nstep_call += 1

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

        break_outer_loop = False
        state_updated = False
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
                    break_outer_loop = True
                    state_updated = True
                    break

            if break_outer_loop:
                break

        if not state_updated:
            self._intermediate_state[self.niter]["test_cells"].update(
                {"EOL": None}
            )

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

    def save_state(self, filename: str):
        """Save the current state of the Sudoku to a pickle file."""
        with open(filename, "wb") as f:
            pickle.dump(
                {
                    "board": self.board,
                    "orig_board": self.orig_board,
                    "allowed_values": self.allowed_values,
                    "block_dim": self.block_dim,
                    "intermediate_state": self._intermediate_state,
                    "niter": self.niter,
                    "nstep_call": self._nstep_call,
                },
                f,
            )

    def load_state(self, filename: str):
        """Load the state of the Sudoku from a pickle file."""
        with open(filename, "rb") as f:
            state = pickle.load(f)

        self.board = state["board"]
        self.orig_board = state["orig_board"]
        self.allowed_values = state["allowed_values"]
        self._nallowed_values = len(self.allowed_values)
        self.block_dim = state["block_dim"]
        self._nblocks = self.block_dim[0] * self.block_dim[1]
        self._intermediate_state = state["intermediate_state"]
        self.niter = state["niter"]
        self._nstep_call = state["nstep_call"]

    def display(self):
        """Display the Sudoku board."""
        # Let's find the maximum number of characters in the allowed values.
        # Sometimes the allowed values may consists of more than 1 character.
        # So, we need to account for this to display the board nicely.
        max_char_len = max([len(str(val)) for val in self.allowed_values])
        # Find how many column separators we need. Column separators include
        # " | " or " # " at the block boundaries.
        ncol_separators = (self._nallowed_values - 1) * 3
        # Now, this is how many characters we need to print in each row. Note
        # that we also need the board borders.
        nchar_per_row = (
            self._nallowed_values * (max_char_len)
            + ncol_separators
            + 4  # for borders "# " and " #"
        )

        # Print the top border
        print("#" * nchar_per_row)
        # Print rows
        board = self.board.copy()
        for ii, row in enumerate(board):
            # First, add " " padding to each value in the row if needed
            row_val = []
            for val in row:
                # For the empty cell, we just print empty spaces
                if val == 0:
                    val = " "
                if len(str(val)) < max_char_len:
                    row_val.append(
                        " " * (max_char_len - len(str(val))) + str(val)
                    )
                else:
                    row_val.append(str(val))
            # Add the border and column separators. It is still in a list
            # because next we need to replace some of the separators with "#"
            # for block separation.
            row_str_list = list("# " + " | ".join(row_val) + " #")
            # Replace some colulmn separators with "#"
            separator_idx = [
                idx for idx, ch in enumerate(row_str_list) if ch == "|"
            ]  # This is where we need to replace "|" with "#"
            for jj, idx in enumerate(separator_idx):
                if (jj + 1) % self.block_dim[1] == 0:
                    row_str_list[idx] = "#"
            # Finally, we can print the row
            row_str = "".join(row_str_list)
            print(row_str)

            # Now, we also need to take care of the row separators
            emDash = "\u2014"
            if (ii + 1) % self.block_dim[0] != 0:
                # This is for normal row separator
                row_separator = list("#" + emDash * (nchar_per_row - 2) + "#")
                # But we need to replace separator with either "+" at the column
                # boundaries or "#" at the block column boundaries.
                for jj, idx in enumerate(separator_idx):
                    if (jj + 1) % self.block_dim[1] == 0:
                        row_separator[idx] = "#"
                    else:
                        row_separator[idx] = "+"
                print("".join(row_separator))
            else:
                # And this is for the block row separator
                print("#" * nchar_per_row)

    def reset(self):
        """Reset the Sudoku problem."""
        self.board = self.orig_board
        self._intermediate_state = {}
        self.niter = 0
        self._nstep_call = 0

import copy
import time
from datetime import timedelta
from typing import List, Callable, Dict

import numpy as np

from sudoku.tile import Tile


def default_callback(board):
    """A default callback function that is called after each iteration in the
    main while loop in :meth:`~sudoku.Board.solve`. It can be used to
    monitor the progress, e.g., by printing the number of empty tiles in the
    board. The default behavior does nothing.

    Parameters
    ----------
    board: :class:`~sudoku.Board` instance.
        Instance of the Sudoku board class.
    """
    pass


class Board:
    """A main class to define the Sudoku problem and solve it.

    Parameters
    ----------
    board: array-like (9, 9,)
        An array that represent the Sudoku problem. It is represented by a
        :math:`9 \times 9` array-like, where the elements of the array give
        show the value in each corresponding tile. The value of zero means that
        the tile is empty.

    Attributes
    ----------
    board: np.ndarray (9, 9,)
        An array that represent the Sudoku board. This array is mutated during
        the solving process, and can be called to access the solved board.
    orig_board: np.adarray (9, 9,)
        An array that represent the initial state of the Sudoku board that
        shows the problem.

    Notes
    -----
    We will call a block to refer to a :math:`3 \times 3` block in which no
    numbers can be repeated in that block.
    """

    def __init__(self, board: np.ndarray):
        self.board = np.asarray(board)
        self.orig_board = copy.copy(self.board)
        assert self.board.shape == (9, 9), ("The board should be a 9x9 array-like",)
        self._intermediate_state = {}
        self.niter = 0

    @property
    def tiles(self) -> Tile:
        """Scan the board and create :class:`~sudoku.tile.Tile` instances.

        Returns
        -------
        tiles: list
            A list that contains :class:`~sudoku.tile.Tile` for each tile in
            the board.
        """
        tiles = [Tile(self.board, row, col) for row in range(9) for col in range(9)]
        return tiles

    @property
    def empty_tiles(self) -> List[Tile]:
        """List all the empty tiles."""
        return [tile for tile in self.tiles if tile.empty]

    def _count_occurence(self) -> List[int]:
        """Count how manny time each number from 1 to 9 shows up in the board."""
        occur = []
        for val in range(1, 10):
            occur.append(np.sum(self.board == val))
        return occur

    @property
    def solved(self) -> np.bool_:
        """Check if the board is solved. If the board is solved, each value
        between 1 and 9 (inclusive) shows up 9 times in the board.
        """
        occur = np.asarray(self._count_occurence())
        if np.all(occur == 9):
            board = self.board
            # Check each row
            for row in board:
                if sorted(row) != list(range(1, 10)):
                    return False

            # Check each column
            for col in range(9):
                if sorted(board[row][col] for row in range(9)) != list(range(1, 10)):
                    return False

            # Check each 3x3 subgrid
            for i in range(0, 9, 3):
                for j in range(0, 9, 3):
                    subgrid = [board[i + x][j + y] for x in range(3) for y in range(3)]
                    if sorted(subgrid) != list(range(1, 10)):
                        return False
            return True
        else:
            return False

    def solve(self, callback: Callable = default_callback, verbose: bool = True):
        """Main method to solve the Sudoku problem."""

        start_time = time.perf_counter()
        while not self.solved:
            self.step(callback)
        finish_time = time.perf_counter()
        if verbose:
            print("Solving time:", timedelta(seconds=finish_time - start_time))

    def step(self, callback: Callable = default_callback, verbose: bool = True):
        """Run one step of the algorithm."""
        # Try updating the tiles by looking up and comparing the lists of
        # possible values.
        old_tiles = copy.deepcopy(self.tiles)  # Tiles before the update
        self._lookup_possible_values()
        new_tiles = copy.deepcopy(self.tiles)  # Tiles after the update

        # Compare the tiles before and after the update. If the above algorithm
        # fails to update the tiles, then try setting one of the tile to a
        # value.
        if self._tiles_same(old_tiles, new_tiles):
            # Store the current state so that we can go back latger if needed.
            self._update_intermediate_state()

            # List the number of possible values for each empty tile.
            nposs_vals = np.array(
                [len(tile.possible_values) for tile in self.empty_tiles]
            )

            if 0 in nposs_vals:
                # There are empty tiles with no possible values. The trial
                # fails and need to be reset to the previous state.
                self._revert_state()
                if verbose:
                    print(f"Search fails, reverting to iteration {self.niter}")
            else:
                # Worth a try. Find the empty tile with fewest possible values.
                # Then, set that tile to one of the number and see if it works.
                # Sort the arrays
                idx_sorted = np.argsort(nposs_vals)
                nposs_vals = nposs_vals[idx_sorted]
                tiles = np.array(self.empty_tiles)[idx_sorted]

                # This index value is to pick the value to set. It is
                # incremented by 1 if we end up at the same state, so that we
                # won't try setting the same tile to the same value twice.
                idx_search = self._intermediate_state[self.niter]["search_idx"]

                # Since we have taken care if there is empty list with 0
                # possible value, then the lowest nposs_vals is 2. But, we
                # still need to terminate if we exhaust the tiles and
                # possible values.
                if idx_search < sum(nposs_vals):
                    # Find which tile and what value to try. We will start
                    # with the empty tile with lowest possible value. Index
                    # stored in _intermediate_state assumes we flatten the
                    # possible values.
                    for ii in range(len(nposs_vals)):
                        nvals = np.sum(nposs_vals[: ii + 1])
                        if not nvals < idx_search:
                            idx_tile = ii
                            idx_val = idx_search - np.sum(nposs_vals[:ii])
                            break
                    tile = tiles[idx_tile]
                    value = tile.possible_values[idx_val]
                    if verbose:
                        print(
                            f"Try setting tile [{tile.row}, {tile.column}] " f"to {value}"
                        )
                    tile.value = value
                    self.board = tile.board
                else:
                    # If on a board we have tried all possible tiles and
                    # values but still not succeeded, we need to go back 1
                    # step.
                    self._revert_state()
                    if verbose:
                        print(
                            "No more values to try, "
                            f"reverting to iteration {self.niter + 1}"
                        )
        self.niter += 1
        callback(self)

    def _lookup_possible_values(self):
        """Update the tiles by looking at the lists of possible values."""
        self._look_for_single_possible_value()
        for block in range(9):
            tiles_block = [
                tile for tile in self.tiles if tile.block[0] == block and tile.empty
            ]
            self._look_for_single_occurence(tiles_block)
        for row in range(9):
            tiles_row = [tile for tile in self.tiles if tile.row == row and tile.empty]
            self._look_for_single_occurence(tiles_row)
        for column in range(9):
            tiles_column = [
                tile for tile in self.tiles if tile.column == column and tile.empty
            ]
        self._look_for_single_occurence(tiles_column)

    def _look_for_single_possible_value(self):
        """Look at the empty tiles of the entire board. To solve the block, we
        look at the tile that has a list of possible values of length 1. This
        means that the item in the list must be the solved value for the tile.
        """
        while True:
            n = 0
            for tile in self.tiles:
                if tile.empty:
                    if len(tile.possible_values) == 1:
                        tile.value = tile.possible_values[0]
                        self.board = tile.board
                        n += 1
            if not n:
                break

    def _look_for_single_occurence(self, tiles_group: List[Tile]):
        """Look at a single group (block, row, or column) and see if we can
        solve any in that group. We look if there is a value in the list of
        possible values of an empty tile that is not in the list of possible
        values in other empty tiles in the same group. If such value exists,
        then we can only put that value in that tile.
        """
        for tile in tiles_group:
            for val in tile.possible_values:
                val_in_other_tile = False
                for tl in tiles_group:
                    if tl != tile:
                        if val in tl.possible_values:
                            val_in_other_tile = True
                            break
                if not val_in_other_tile:
                    tile.value = val
                    self.board = tile.board
                    break

    def _update_intermediate_state(self):
        """Update the information of the intermediate state."""
        if self.niter not in self._intermediate_state:
            # Store the intermediate state
            self._intermediate_state.update(
                {self.niter: {"board": copy.copy(self.board), "search_idx": 0}}
            )
        else:
            # Update the search index so we won't set the same tile with the
            # same value twice.
            self._intermediate_state[self.niter]["search_idx"] += 1

    def _revert_state(self):
        """Revert to the previous state."""
        # Revert the previous state
        self._intermediate_state.pop(self.niter)
        self.niter = list(self._intermediate_state)[-1]
        self.board = self._intermediate_state[self.niter]["board"]
        # Counter adding niter with 1 so that we can get back to
        # the same _intermediate_state.
        self.niter -= 1

    def _tiles_same(self, tiles1: List[Tile], tiles2: List[Tile]):
        """Compare the tiles, check if they are the same."""
        tiles1_dict = self._tiles_to_dict_possible_values(tiles1)
        tiles2_dict = self._tiles_to_dict_possible_values(tiles2)
        return tiles1_dict == tiles2_dict

    @staticmethod
    def _tiles_to_dict_possible_values(tiles: List[Tile]) -> Dict:
        """Convert the list of tiles into dictionary. The dictionary only
        contains the possible values.
        """
        tiles_dict = {}
        for tile in tiles:
            if tile.empty:
                tiles_dict.update({(tile.row, tile.column): tile.possible_values})
        return tiles_dict

    def display(self):
        """Display the Sudoku board."""
        print("#" * 37)
        for ii in range(3):
            rows = self.board[(ii * 3) : ((ii + 1) * 3)]
            for jj, row in enumerate(rows):
                self._print_one_row(row)
                if jj < 2:
                    print("#" + ("-" * 11 + "#") * 3)
            print("#" * 37)

    @staticmethod
    def _print_one_row(row_array):
        """Print one row of the board."""
        b = [str(el) if el != 0 else " " for el in row_array]
        print(
            "#"
            + f" {b[0]} | {b[1]} | {b[2]} "
            + "#"
            + f" {b[3]} | {b[4]} | {b[5]} "
            + "#"
            + f" {b[6]} | {b[7]} | {b[8]} "
            + "#"
        )

    def reset(self):
        """Reset the Sudoku problem."""
        self.board = self.orig_board

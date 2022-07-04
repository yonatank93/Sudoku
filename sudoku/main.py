import copy
import time
from datetime import timedelta

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

    def __init__(self, board):
        self.board = np.asarray(board)
        self.orig_board = copy.copy(self.board)
        assert self.board.shape == (9, 9), (
            "The board should be a 9x9 array-like",
        )

    @property
    def tiles(self):
        """Scan the board and create :class:`~sudoku.tile.Tile` instances.

        Returns
        -------
        tiles: list
            A list that contains :class:`~sudoku.tile.Tile` for each tile in
            the board.
        """
        tiles = [
            Tile(self.board, row, col) for row in range(9) for col in range(9)
        ]
        return tiles

    @property
    def solved(self):
        """Check if the board is solved. The board is solved when there is no
        empty tile, represented by zero value.
        """
        return 0 not in self.board

    def solve(self, callback=default_callback):
        """Main method to solve the Sudoku problem."""

        start_time = time.perf_counter()
        while True:
            self.step()
            callback(self)
            if self.solved:
                break
        finish_time = time.perf_counter()
        print("Solving time:", timedelta(seconds=finish_time - start_time))

    def step(self):
        """Run one step of the algorithm."""
        self._look_for_single_possible_value()
        for block in range(9):
            tiles_block = [
                tile
                for tile in self.tiles
                if tile.block[0] == block and tile.empty
            ]
            self._look_for_single_occurence(tiles_block)
        for row in range(9):
            tiles_row = [
                tile for tile in self.tiles if tile.row == row and tile.empty
            ]
            self._look_for_single_occurence(tiles_row)
        for column in range(9):
            tiles_column = [
                tile
                for tile in self.tiles
                if tile.column == column and tile.empty
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

    def _look_for_single_occurence(self, tiles_group):
        """Look at a single group (block, row, or column) and see if we can
        solve any in that group. Unlike in ``_look_for_single_possible_value``,
        here we look if there is a value in the list of possible values of an
        empty tile that is not in the list of possible values in other empty
        tiles in the same group. If such value exists, then we can only put
        that value in that tile.
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
        b = [str(row) if row != 0 else " " for row in row_array]
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

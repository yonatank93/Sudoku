import copy
import time
from datetime import timedelta

import numpy as np

from sudoku.tile import Tile


class Board:
    def __init__(self, board):
        self.board = np.asarray(board)
        self._orig_board = copy.copy(board)
        assert self.board.shape == (9, 9), (
            "The board should be a 9x9 array-like",
        )

    @property
    def tiles(self):
        """Scan the board and create tiles."""
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

    def solve(self):
        """Solve the sudoku problem."""

        start_time = time.perf_counter()
        while True:
            self._look_for_single_possible_value()
            for block in range(9):
                tiles_block = [
                    tile
                    for tile in self.tiles
                    if tile.block[0] == block and tile.empty
                ]
                self._look_for_single_group(tiles_block)
            for row in range(9):
                tiles_row = [
                    tile
                    for tile in self.tiles
                    if tile.row == row and tile.empty
                ]
                self._look_for_single_group(tiles_row)
            for column in range(9):
                tiles_column = [
                    tile
                    for tile in self.tiles
                    if tile.column == column and tile.empty
                ]
            self._look_for_single_group(tiles_column)

            if self.solved:
                break
        finish_time = time.perf_counter()
        print("Solving time:", timedelta(seconds=finish_time - start_time))

    def _look_for_single_possible_value(self):
        """Solve the tiles by looking at the tiles with only 1 possible value."""
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

    def _look_for_single_group(self, tiles_group):
        """Look at a single group (block, row, or column) and see if we can
        solve any in that group. Unlike in ``_look_for_single_possible_value``,
        here we look if there is a value of possible values in an empty tile
        that is not in the list of possible values in other empty tiles in the
        same group. If such value exists, then we can only put that value in
        that tile.
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

    def reset(self):
        self.board = self._orig_board

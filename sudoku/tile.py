from typing import List
import numpy as np

possible_values = {1, 2, 3, 4, 5, 6, 7, 8, 9}


class Tile:
    """A class to represent the a single tile in Sudoku board.

    Parameters
    ----------
    board: np.ndarray (9, 9,)
        An array that represent the Sudoku board.
    row: int
        Row position of the tile.
    column: int
        Column position of the tile.
    """

    def __init__(self, board: np.ndarray, row: int, column: int):
        self._board = board
        self.row = row
        self.column = column

        self._value = self._board[self.row, self.column]

    @property
    def block(self) -> List:
        """Retrieve the block corresponding to the tile. A block refers to a
        :math:`3 \times 3` block in which no numbers can be repeated in that
        block.

        Returns
        -------
        idx: int
            Index of the block. The diagram below show how the block indices
            correspond to regions on the Sudoku board. ::

                -------------------
                |     |     |     |
                |  0  |  1  |  2  |
                |     |     |     |
                -------------------
                |     |     |     |
                |  3  |  4  |  5  |
                |     |     |     |
                -------------------
                |     |     |     |
                |  6  |  7  |  8  |
                |     |     |     |
                -------------------
        values: np.ndarray (3, 3,)
            The values of the tile in a block.
        """
        row = self.row // 3
        column = self.column // 3
        values = self._board[
            (row * 3) : ((row + 1) * 3), (column * 3) : ((column + 1) * 3)
        ]
        return 3 * row + column, values

    @property
    def value(self):
        """Retrieve the value of the tile."""
        if self._value:
            return self._value
        else:
            return None

    @value.setter
    def value(self, value: int):
        """Set the value of the tile."""
        self._value = value
        self._board[self.row, self.column] = value

    @property
    def board(self) -> np.ndarray:
        """Retrieve the entire board."""
        return self._board

    @board.setter
    def board(self, board: np.ndarray):
        """Set the entire board."""
        self._board = board

    @property
    def empty(self) -> bool:
        """Check if the tile is empty, i.e., has no value."""
        return not bool(self._board[self.row, self.column])

    @staticmethod
    def _values_not_in_range1to9(array) -> List[int]:
        """Get values that don't appear in a list from 1 to 9."""
        values = np.unique(array)
        values = values[values != 0]  # Remove 0 or the empty tile
        poss_vals = sorted(list(possible_values - set(values)))
        return poss_vals

    @property
    def possible_values(self) -> List[int]:
        """Get a list of possible values we can put in the tile. It returns an
        empty list if the tile is not empty, showing that we cannot put any
        other value in that tile.
        """
        if self.empty:
            block = self.block[1].flatten()
            row = self._board[self.row]
            column = self._board[:, self.column]
            filled_values = np.concatenate((block, row, column))
            return self._values_not_in_range1to9(filled_values)
        else:
            return []

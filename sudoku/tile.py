import numpy as np

possible_values = {1, 2, 3, 4, 5, 6, 7, 8, 9}


class Tile:
    def __init__(self, board, row, column):
        self._board = board
        self.row = row
        self.column = column

        self._value = self._board[self.row, self.column]

    @property
    def block(self):
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
    def value(self, value):
        """Set the value of the tile."""
        self._value = value
        self._board[self.row, self.column] = value

    @property
    def board(self):
        return self._board

    @board.setter
    def board(self, board):
        self._board = board

    @property
    def empty(self):
        return not bool(self._board[self.row, self.column])

    @staticmethod
    def _get_possible_values(array):
        values = np.unique(array)
        values = values[values != 0]  # Remove 0 or the empty tile
        poss_vals = list(possible_values - set(values))
        return poss_vals

    @property
    def possible_values(self):
        if self.empty:
            block = self.block[1].flatten()
            row = self._board[self.row]
            column = self._board[:, self.column]
            filled_values = np.concatenate((block, row, column))
            return self._get_possible_values(filled_values)
        else:
            return []

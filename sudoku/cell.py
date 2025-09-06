from typing import Sequence, Tuple
import numpy as np

from .groups import Row, Column, Block


class Cell:
    def __init__(
        self,
        board: np.ndarray,
        loc: Sequence[int],
        allowed_values: Sequence[int],
        nblocks_rows: int,
        nblocks_columns: int,
    ):
        self._board = board
        self.row_idx, self.column_idx = loc
        self.allowed_values = allowed_values

        self.nblocks_columns = nblocks_columns
        self.nblocks_rows = nblocks_rows
        self._block_dim = [
            self.board.shape[0] // self.nblocks_rows,
            self.board.shape[1] // self.nblocks_columns,
        ]
        self.block_idx = self.column_idx // self._block_dim[1] + (
            self.row_idx // self._block_dim[0] * self.nblocks_columns
        )

    @property
    def board(self) -> np.ndarray:
        """Get the entire board."""
        return self._board

    @board.setter
    def board(self, board: np.ndarray) -> None:
        """Set the entire board."""
        self._board = board

    @property
    def row(self):
        return Row(self._board, self.row_idx, self.allowed_values)

    @property
    def column(self):
        return Column(self._board, self.column_idx, self.allowed_values)

    @property
    def block(self):
        return Block(
            self._board, self.block_idx, self._block_dim, self.allowed_values
        )

    @property
    def value(self) -> int:
        """Get the value of the cell."""
        return self._board[self.row_idx, self.column_idx]

    @property
    def is_empty(self) -> bool:
        """Check if the cell is empty, i.e., has no value."""
        return self.value == 0

    @property
    def possible_values(self) -> Sequence[int]:
        """Get a list of possible values we can put in the cell.
        It returns an empty list if the cell is not empty, showing that we cannot
        put any other value in that cell.
        """
        if not self:
            return []
        block_missing_values = set(self.block.missing_values)
        row_missing_values = set(self.row.missing_values)
        column_missing_values = set(self.column.missing_values)
        return sorted(
            list(
                block_missing_values
                & row_missing_values
                & column_missing_values
            )
        )

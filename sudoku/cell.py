from typing import Sequence, Union
import numpy as np

from .groups import Row, Column, Block

empty_cell_repr = [0, "0", None, "", " ", "_"]


class Cell:
    def __init__(
        self,
        board: Union[list, np.array],
        loc: Sequence[int],
        allowed_values: Sequence[int],
        block_dim: Sequence[int],
    ):
        self._board = board
        self.row_idx, self.column_idx = loc
        self.allowed_values = allowed_values

        self._block_dim = block_dim
        self.nblocks_rows = len(board) // block_dim[0]
        self.nblocks_columns = len(board[0]) // block_dim[1]
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
        return self._board[self.row_idx][self.column_idx]

    @property
    def is_empty(self) -> bool:
        """Check if the cell is empty, i.e., has no value."""
        return self.value in [0, "0", None, ""]

    @property
    def possible_values(self) -> Sequence[int]:
        """Get a list of possible values we can put in the cell.
        It returns an empty list if the cell is not empty, showing that we
        cannot put any other value in that cell.
        """
        if not self:
            return []
        block_missing_values = set(self.block.missing_values)
        row_missing_values = set(self.row.missing_values)
        column_missing_values = set(self.column.missing_values)
        combined_missing_values = list(
            block_missing_values & row_missing_values & column_missing_values
        )
        # Sorted
        sorted_missing_values = [
            v for v in self.allowed_values if v in combined_missing_values
        ]
        return sorted_missing_values

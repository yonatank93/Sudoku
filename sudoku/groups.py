from typing import Sequence, Union
from abc import ABC
import numpy as np


class GroupABC(ABC):
    def __init__(
        self,
        board: np.ndarray,
        idx: Union[int, Sequence[int]],
        allowed_values: Sequence[int],
    ):
        self.idx = idx
        self._board = board
        self.allowed_values = allowed_values

    @property
    def board(self) -> np.ndarray:
        """Return the board."""
        return self._board

    @board.setter
    def board(self, board: np.ndarray) -> None:
        """Set the board, e.g., for updating the board after a move."""
        self._board = board

    @property
    def values(self) -> np.ndarray:
        """Return the values in the group as a 1D numpy array."""
        raise NotImplementedError("Subclasses should implement this method.")

    @property
    def missing_values(self) -> Sequence[int]:
        """Return the values that are not present in the group.
        The values listed here are the ones that can be used to fill the group.
        """
        return [v for v in self.allowed_values if v not in self.values]

    @property
    def solved(self) -> bool:
        """Check if the group is solved."""
        return len(self.missing_values) == 0


class Row(GroupABC):
    def __init__(
        self, board: np.ndarray, idx: int, allowed_values: Sequence[int]
    ):
        super().__init__(board, idx, allowed_values)

    @property
    def values(self) -> np.ndarray:
        return self.board[self.idx]

    def __repr__(self):
        return f"Row {self.idx}"


class Column(GroupABC):
    def __init__(
        self, board: np.ndarray, idx: int, allowed_values: Sequence[int]
    ):
        super().__init__(board, idx, allowed_values)

    @property
    def values(self) -> np.ndarray:
        return self.board[:, self.idx]

    def __repr__(self):
        return f"Column {self.idx}"


class Block(GroupABC):
    def __init__(
        self,
        board: np.ndarray,
        idx: int,
        dim: Sequence[int],
        allowed_values: Sequence[int],
    ):
        super().__init__(board, idx, allowed_values)
        self.dim = dim

    @property
    def values(self) -> np.ndarray:
        return self.values_2d.flatten()

    @property
    def values_2d(self) -> np.ndarray:
        board_shape = self.board.shape
        nblock_rows = board_shape[0] // self.dim[0]
        nblock_columns = board_shape[1] // self.dim[1]

        row_start = (self.idx // nblock_columns) * self.dim[0]
        col_start = (self.idx % nblock_columns) * self.dim[1]
        values = self.board[
            row_start : row_start + self.dim[0],
            col_start : col_start + self.dim[1],
        ]
        return values

    def __repr__(self):
        return f"Block {self.idx}"

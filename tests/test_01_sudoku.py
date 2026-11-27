import json
import unittest
from pathlib import Path

from sudoku import Sudoku

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestSudokuBenchmarks(unittest.TestCase):
    def _solve_example_problems(self, subdir: str, exclude_board=()):
        board_files = sorted((DATA_DIR / subdir).glob("board_*.json"))
        test_board_files = [
            f
            for f in board_files
            if not any(exclude in f.name for exclude in exclude_board)
        ]
        self.assertGreater(len(test_board_files), 0, f"No boards in {subdir}")

        for board_file in test_board_files:
            with self.subTest(board=f"{subdir}/{board_file.name}"):
                with open(board_file, "r") as f:
                    data = json.load(f)

                S = Sudoku(
                    data["board"],
                    allowed_values=data["allowed_values"],
                    block_dim=data["block_dim"],
                )
                empty_counts = []
                S.solve(lambda inst: empty_counts.append(len(inst.empty_cells)))

                self.assertTrue(S.solved)
                self.assertEqual(S.board, data["solution"])
                self.assertGreater(len(empty_counts), 0)
                self.assertEqual(empty_counts[-1], 0)

    def test_solve_6by6(self):
        self._solve_example_problems("6by6")

    def test_solve_9by9(self):
        self._solve_example_problems("9by9")

    def test_solve_16by16(self):
        self._solve_example_problems("16by16")


if __name__ == "__main__":
    unittest.main()

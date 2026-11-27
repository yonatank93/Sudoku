import contextlib
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import sudoku
from sudoku import Sudoku
from sudoku.cli import generate_problem as cli_generate
from sudoku.cli import solve as cli_solve
from sudoku.reader import UserInput

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestPublicAPIAndDisplay(unittest.TestCase):
    def test_top_level_exports(self):
        self.assertTrue(hasattr(sudoku, "Sudoku"))
        self.assertTrue(hasattr(sudoku, "generate_problem"))
        self.assertFalse(hasattr(sudoku, "solve"))
        self.assertEqual(
            sudoku.__all__, ["Sudoku", "generate_problem", "__version__"]
        )

    def test_positional_callback_and_empty_cells_property(self):
        board = [
            [1, 2, 3, 4],
            [3, 4, 1, 2],
            [2, 1, 4, 3],
            [4, 3, 2, 0],
        ]
        S = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))
        self.assertEqual(len(S.empty_cells), 1)

        history = []
        result = S.solve(
            lambda inst: history.append((inst.niter, len(inst.empty_cells)))
        )
        self.assertEqual(history, [(1, 0)])
        self.assertEqual(result, S.board)

        S2 = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))
        self.assertIsNone(S2.solve(return_board=False))

    def test_display_blanks_empty_cells_for_int_and_string_boards(self):
        S_str = Sudoku(
            ["1234", "3412", "2143", "4320"],
            allowed_values="1234",
            block_dim=(2, 2),
        )
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            S_str.display()
        self.assertNotIn("0", buf.getvalue())

        # When "0" is an allowed symbol, "0" must print literally while "_" is blanked
        S_zero = Sudoku(
            ["0123", "2301", "1032", "321_"],
            allowed_values="0123",
            block_dim=(2, 2),
        )
        buf2 = io.StringIO()
        with contextlib.redirect_stdout(buf2):
            S_zero.display()
        out2 = buf2.getvalue()
        self.assertIn("0", out2)
        self.assertNotIn("_", out2)
        S_zero.solve()
        self.assertTrue(S_zero.solved)
        self.assertEqual(S_zero.board[3][3], "0")


class TestUserInputAndCLI(unittest.TestCase):
    def test_user_input_allows_zero_as_symbol_and_retries_invalid_rows(self):
        inputs = [
            "012x",  # invalid char -> retry
            "012",  # wrong length -> retry
            "0012",  # repeated '0' -> retry
            "012_",  # valid row 0
            "23-1",  # valid row 1
            "1032",  # valid row 2
            "3210",  # valid row 3
        ]
        buf = io.StringIO()
        with patch("builtins.input", side_effect=inputs), contextlib.redirect_stdout(
            buf
        ):
            ui = UserInput(allowed_values="0123")

        self.assertEqual(
            ui.board,
            [
                ["0", "1", "2", 0],
                ["2", "3", 0, "1"],
                ["1", "0", "3", "2"],
                ["3", "2", "1", "0"],
            ],
        )
        S = Sudoku(ui.board, allowed_values="0123", block_dim=(2, 2))
        S.solve()
        self.assertTrue(S.solved)

    def test_cli_solve_valid_9x9_and_duplicate_allowed_values_retry(self):
        with open(DATA_DIR / "9by9" / "board_01.json", "r") as f:
            b01 = json.load(f)["board"]
        rows_str = ["".join(str(x) for x in r) for r in b01]
        inputs = [
            "1123",  # duplicate allowed values -> retry
            "",  # default '123456789'
            "2 2",  # wrong product -> retry
            "",  # default '3 3'
            *rows_str,
        ]
        buf = io.StringIO()
        with patch("builtins.input", side_effect=inputs), contextlib.redirect_stdout(
            buf
        ):
            cli_solve(["-s"])

        output = buf.getvalue()
        self.assertIn("must not contain duplicates", output)
        self.assertIn("Problem:", output)
        self.assertIn("Solution:", output)

    def test_cli_solve_handles_invalid_and_unsolvable_boards_gracefully(self):
        # Duplicate in column 0 (valid per-row, invalid column)
        inputs_dup = [
            "1234",
            "2 2",
            "1___",
            "1___",
            "____",
            "____",
        ]
        buf1 = io.StringIO()
        with patch(
            "builtins.input", side_effect=inputs_dup
        ), contextlib.redirect_stdout(buf1):
            cli_solve([])
        self.assertIn("Error:", buf1.getvalue())

        # Locally valid but globally unsolvable 4x4
        inputs_unsolvable = [
            "1234",
            "2 2",
            "123_",
            "___4",
            "____",
            "____",
        ]
        buf2 = io.StringIO()
        with patch(
            "builtins.input", side_effect=inputs_unsolvable
        ), contextlib.redirect_stdout(buf2):
            cli_solve([])
        self.assertIn("Error: The Sudoku board has no valid solution.", buf2.getvalue())

    def test_cli_generate_problem_with_solution_and_level_retry(self):
        inputs = ["1234", "2 2", "9", "3"]  # level 9 invalid -> retry with 3
        buf = io.StringIO()
        with patch("builtins.input", side_effect=inputs), contextlib.redirect_stdout(
            buf
        ):
            cli_generate(["-s"])
        output = buf.getvalue()
        self.assertIn("Level should be an integer from 1 to 5", output)
        self.assertIn("Generated problem:", output)
        self.assertIn("Solution:", output)


if __name__ == "__main__":
    unittest.main()

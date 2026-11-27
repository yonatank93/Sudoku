import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from sudoku import Sudoku
from sudoku.cell import empty_cell_repr

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


class TestCellBehavior(unittest.TestCase):
    def test_is_empty_matches_empty_cell_repr(self):
        board = [
            [1, 0, "0", None],
            ["", " ", "_", 2],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        S = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))

        for val in empty_cell_repr:
            self.assertIn(val, [0, "0", None, "", " ", "_"])

        self.assertFalse(S.cells[0, 0].is_empty)
        self.assertFalse(S.cells[1, 3].is_empty)
        for r, c in [(0, 1), (0, 2), (0, 3), (1, 0), (1, 1), (1, 2)]:
            self.assertTrue(
                S.cells[r, c].is_empty,
                f"Expected cell ({r}, {c}) with value {S.cells[r, c].value!r} to be empty",
            )

    def test_possible_values_empty_for_filled_cell(self):
        board = [
            [1, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        S = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))
        self.assertEqual(S.cells[0, 0].possible_values, [])
        self.assertEqual(S.cells[0, 1].possible_values, [2, 3, 4])


class TestBacktrackingAndAllowedValues(unittest.TestCase):
    def test_hard_9x9_boards_normal_and_reversed_allowed_values(self):
        for name in ("board_10.json", "board_12.json"):
            with open(DATA_DIR / "9by9" / name, "r") as f:
                data = json.load(f)
            for reverse in (False, True):
                vals = (
                    list(reversed(data["allowed_values"]))
                    if reverse
                    else data["allowed_values"]
                )
                S = Sudoku(
                    data["board"],
                    allowed_values=vals,
                    block_dim=data["block_dim"],
                )
                S.solve()
                self.assertTrue(S.solved)
                self.assertEqual(S.board, data["solution"])

    def test_16x16_board(self):
        with open(DATA_DIR / "16by16" / "board_01.json", "r") as f:
            data = json.load(f)
        S = Sudoku(
            data["board"],
            allowed_values=data["allowed_values"],
            block_dim=data["block_dim"],
        )
        S.solve()
        self.assertTrue(S.solved)
        self.assertEqual(S.board, data["solution"])

    def test_mixed_type_allowed_values_with_guessing(self):
        S4 = Sudoku(
            [[0] * 4 for _ in range(4)],
            allowed_values=[1, 2, 3, "a"],
            block_dim=(2, 2),
        )
        S4.solve()
        self.assertTrue(S4.solved)

        board6 = [
            ["ab", 0, 5, 0, 0, 0],
            [0, 0, 4, 0, 0, 0],
            [0, "ab", 0, 0, 0, 5],
            [2, 0, 0, 0, 4, 0],
            [0, 0, 0, 3, 0, 0],
            [0, 0, 0, 2, 0, 1],
        ]
        S6 = Sudoku(
            board6,
            allowed_values=[1, 2, 3, 4, 5, "ab"],
            block_dim=(2, 3),
        )
        S6.solve()
        self.assertTrue(S6.solved)

    def test_string_allowed_values_board(self):
        board = [
            "605000",
            "004000",
            "060005",
            "200040",
            "000300",
            "000201",
        ]
        S = Sudoku(board, allowed_values="123456", block_dim=(2, 3))
        S.solve()
        self.assertTrue(S.solved)

    def test_unsolvable_immediate_contradiction_raises_value_error(self):
        # Row 0 needs 4 at (0, 3), but col 3 already has 4 at (1, 3)
        board = [
            [1, 2, 3, 0],
            [0, 0, 0, 4],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        S = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))
        with self.assertRaises(ValueError):
            S.solve()

    def test_unsolvable_deep_backtrack_raises_value_error(self):
        with open(DATA_DIR / "9by9" / "board_10.json", "r") as f:
            board = json.load(f)["board"]
        # Locally valid placement that makes the board globally unsolvable
        board[0][0] = 5
        S = Sudoku(board)
        with self.assertRaises(ValueError):
            S.solve()

    def test_step_on_already_solved_board_is_safe(self):
        board = [
            [1, 2, 3, 4],
            [3, 4, 1, 2],
            [2, 1, 4, 3],
            [4, 3, 2, 1],
        ]
        S = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))
        self.assertTrue(S.solved)
        S.step()
        self.assertTrue(S.solved)
        self.assertEqual(S.board, board)


class TestInPlaceUpdatesAndSolved(unittest.TestCase):
    def test_cell_references_stay_live_during_group_update(self):
        board = [
            [0, 0, 0, 0],
            [0, 0, 2, 0],
            [0, 2, 0, 0],
            [0, 0, 0, 0],
        ]
        S = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))
        cells_block = [c for c in S._cells_flatten if c.block_idx == 0 and c.is_empty]
        board_id = id(S.board)

        S._update_cells_from_single_possible_occurence(cells_block)

        self.assertEqual(id(S.board), board_id)
        self.assertEqual(S.board[0][0], 2)
        self.assertEqual(cells_block[0].value, 2)
        self.assertFalse(cells_block[0].is_empty)
        self.assertEqual(cells_block[0].possible_values, [])

    def test_update_board_value_validation_and_rollback(self):
        board = [
            [1, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
            [0, 0, 0, 0],
        ]
        S = Sudoku(board, allowed_values=[1, 2, 3, 4], block_dim=(2, 2))

        with self.assertRaises(AssertionError):
            S.update_board_value(1, S.cells[0, 1])  # repetition in row 0 / block 0
        self.assertEqual(S.board[0][1], 0)

        with self.assertRaises(AssertionError):
            S.update_board_value(99, S.cells[0, 1])  # disallowed value
        self.assertEqual(S.board[0][1], 0)

        S.update_board_value(2, S.cells[0, 1])
        self.assertEqual(S.board[0][1], 2)

    def test_orig_board_isolation_and_reset(self):
        with open(DATA_DIR / "6by6" / "board_01.json", "r") as f:
            data = json.load(f)
        S = Sudoku(
            data["board"],
            allowed_values=data["allowed_values"],
            block_dim=data["block_dim"],
        )
        orig_copy = copy.deepcopy(data["board"])

        S.solve()
        self.assertTrue(S.solved)
        self.assertEqual(S.orig_board, orig_copy)

        S.reset()
        self.assertEqual(S.board, orig_copy)
        self.assertEqual(S.niter, 0)
        self.assertEqual(S._intermediate_state, {})

        S.solve()
        self.assertTrue(S.solved)
        self.assertEqual(S.board, data["solution"])

    def test_solved_rejects_full_board_with_group_duplicates(self):
        S = Sudoku(
            [[0] * 4 for _ in range(4)],
            allowed_values=[1, 2, 3, 4],
            block_dim=(2, 2),
        )
        # Global digit counts are all 4, but every row has duplicates
        S._board = [
            [1, 1, 1, 1],
            [2, 2, 2, 2],
            [3, 3, 3, 3],
            [4, 4, 4, 4],
        ]
        self.assertFalse(S.solved)


class TestStatePersistence(unittest.TestCase):
    def test_load_state_mismatched_dimensions_and_mid_solve_resume(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Save 6x6 and load into default 9x9 Sudoku()
            with open(DATA_DIR / "6by6" / "board_01.json", "r") as f:
                d6 = json.load(f)
            S6 = Sudoku(
                d6["board"],
                allowed_values=d6["allowed_values"],
                block_dim=d6["block_dim"],
            )
            p6 = os.path.join(tmpdir, "s6.pkl")
            S6.save_state(p6)

            S6_loaded = Sudoku()
            S6_loaded.load_state(p6)
            S6_loaded.solve()
            self.assertTrue(S6_loaded.solved)
            self.assertEqual(S6_loaded.board, d6["solution"])
            self.assertEqual(S6_loaded.orig_board, d6["board"])

            # 2. Mid-solve save/load on 9x9 board_10 with active backtracking state
            with open(DATA_DIR / "9by9" / "board_10.json", "r") as f:
                d10 = json.load(f)
            S10 = Sudoku(
                d10["board"],
                allowed_values=d10["allowed_values"],
                block_dim=d10["block_dim"],
            )
            for _ in range(5):
                S10.step()
            self.assertGreater(len(S10._intermediate_state), 0)
            p10 = os.path.join(tmpdir, "s10.pkl")
            S10.save_state(p10)

            S10_loaded = Sudoku(allowed_values=range(1, 5), block_dim=(2, 2))
            S10_loaded.load_state(p10)
            S10_loaded.solve()
            self.assertTrue(S10_loaded.solved)
            self.assertEqual(S10_loaded.board, d10["solution"])
            self.assertEqual(S10_loaded.orig_board, d10["board"])

            # 3. Save/load when board is None
            S_none = Sudoku(None, allowed_values=range(1, 7), block_dim=(2, 3))
            p_none = os.path.join(tmpdir, "snone.pkl")
            S_none.save_state(p_none)

            S_none_loaded = Sudoku()
            S_none_loaded.load_state(p_none)
            self.assertIsNone(S_none_loaded.board)
            self.assertEqual(S_none_loaded.block_dim, (2, 3))


if __name__ == "__main__":
    unittest.main()

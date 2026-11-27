import random
import unittest
import numpy as np

from sudoku import generate_problem, Sudoku
from sudoku.generate_problem import fill_board, generate_full_solution


class TestGenerateProblem(unittest.TestCase):
    def _runner(self, niter, **init_args):
        """Generate problems across all levels 1..5 and verify each is solvable."""
        rng = np.random.default_rng(1)
        for _ in range(niter):
            level = int(rng.integers(1, 6))
            problem, solution = generate_problem(
                level, return_solution=True, **init_args
            )
            # Returned solution must be valid
            S_sol = Sudoku(solution, **init_args)
            self.assertTrue(S_sol.solved)
            # Non-empty cells in problem must match the returned solution
            for r in range(len(problem)):
                for c in range(len(problem)):
                    if problem[r][c] != 0:
                        self.assertEqual(problem[r][c], solution[r][c])
            # Problem must be solvable
            B = Sudoku(problem, **init_args)
            B.solve()
            self.assertTrue(B.solved, "Generated problem might not be solvable.")

    def test_generate_2by2_all_levels(self):
        for level in range(1, 6):
            problem, solution = generate_problem(
                level=level,
                allowed_values=range(1, 3),
                block_dim=(1, 2),
                seed=level,
                return_solution=True,
            )
            n_empty = sum(cell == 0 for row in problem for cell in row)
            self.assertGreaterEqual(n_empty, 1)
            self.assertLess(n_empty, 4)
            self.assertTrue(
                Sudoku(solution, allowed_values=range(1, 3), block_dim=(1, 2)).solved
            )
            S = Sudoku(problem, allowed_values=range(1, 3), block_dim=(1, 2))
            S.solve()
            self.assertTrue(S.solved)

    def test_generate_4by4(self):
        self._runner(10, allowed_values=range(1, 5), block_dim=(2, 2))

    def test_generate_6by6(self):
        self._runner(10, allowed_values=range(1, 7), block_dim=(2, 3))

    def test_generate_8by8(self):
        self._runner(5, allowed_values=range(1, 9), block_dim=(2, 4))

    def test_generate_9by9(self):
        self._runner(5, allowed_values=range(1, 10), block_dim=(3, 3))

    def test_generate_string_allowed_values(self):
        problem, solution = generate_problem(
            level=3,
            allowed_values="123456",
            block_dim=(2, 3),
            seed=7,
            return_solution=True,
        )
        self.assertTrue(
            Sudoku(solution, allowed_values="123456", block_dim=(2, 3)).solved
        )
        S = Sudoku(problem, allowed_values="123456", block_dim=(2, 3))
        S.solve()
        self.assertTrue(S.solved)

    def test_seed_reproducibility_and_global_rng_isolation(self):
        p1, s1 = generate_problem(level=3, seed=42, return_solution=True)
        p2, s2 = generate_problem(level=3, seed=42, return_solution=True)
        p3, s3 = generate_problem(level=3, seed=99, return_solution=True)

        self.assertEqual(p1, p2)
        self.assertEqual(s1, s2)
        self.assertNotEqual(p1, p3)
        self.assertNotEqual(s1, s3)

        # Global random and numpy RNG states must remain untouched
        random.seed(123)
        np.random.seed(123)
        py_state = random.getstate()
        np_state = np.random.get_state()
        generate_problem(level=3, seed=42)
        self.assertEqual(random.getstate(), py_state)
        self.assertTrue(np.array_equal(np.random.get_state()[1], np_state[1]))

    def test_caller_allowed_values_not_mutated(self):
        vals = [1, 2, 3, 4, 5, 6]
        generate_problem(level=3, allowed_values=vals, block_dim=(2, 3), seed=7)
        self.assertEqual(vals, [1, 2, 3, 4, 5, 6])

        generate_full_solution(vals, (2, 3), seed=7)
        self.assertEqual(vals, [1, 2, 3, 4, 5, 6])

        board = [[0] * 6 for _ in range(6)]
        self.assertTrue(fill_board(board, vals, (2, 3), seed=7))
        self.assertEqual(vals, [1, 2, 3, 4, 5, 6])
        self.assertTrue(Sudoku(board, vals, (2, 3)).solved)

    def test_invalid_inputs_raise_assertion_error(self):
        bad_cases = [
            dict(level=0),
            dict(level=6),
            dict(level=True),
            dict(level=3, allowed_values=[1], block_dim=(1, 1)),
            dict(level=3, allowed_values=[1, 1, 2, 3], block_dim=(2, 2)),
            dict(level=3, allowed_values=[1, 2, 3, 4], block_dim=(3, 3)),
            dict(level=3, allowed_values=[1, 2, 3, 4], block_dim=(0, 4)),
        ]
        for kwargs in bad_cases:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(AssertionError):
                    generate_problem(**kwargs)


if __name__ == "__main__":
    unittest.main()

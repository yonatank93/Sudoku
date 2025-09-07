import numpy as np
from sudoku import generate_problem, Sudoku

np.random.seed(1)


def runner(niter, **init_args):
    """Main function to run test by generating problem and then try to solve it."""
    for _ in range(niter):
        # Setup
        level = np.random.randint(1, 5)
        board = generate_problem(level, **init_args)
        # Solve the board
        B = Sudoku(board, **init_args)
        B.solve()
        # Check
        assert B.solved, "Generated problem might not be solvable."


def test_generate_4by4():
    runner(10, allowed_values=range(1, 5), nblocks_rows=2, nblocks_columns=2)


def test_generate_6by6():
    runner(10, allowed_values=range(1, 7), nblocks_rows=3, nblocks_columns=2)


# def test_generate_8by8():
#     runner(5, allowed_values=range(1, 9), nblocks_rows=4, nblocks_columns=2)


def test_generate_9by9():
    runner(5, allowed_values=range(1, 10), nblocks_rows=3, nblocks_columns=3)


# def test_generate_12by12():
#     runner(1, allowed_values=range(1, 13), nblocks_rows=3, nblocks_columns=4)


# def test_generate_16by16():
#     runner(1, allowed_values=range(1, 17), nblocks_rows=4, nblocks_columns=4)


if __name__ == "__main__":
    test_generate_4by4()
    # test_generate_6by6()
    # test_generate_8by8()
    test_generate_9by9()
    # test_generate_12by12()
    # test_generate_16by16()

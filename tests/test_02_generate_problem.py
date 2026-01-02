import numpy as np
from sudoku import generate_problem, Sudoku

np.random.seed(1)


def runner(niter, **init_args):
    """Main function to run test by generating problem and then try to solve it."""
    print(f"Running {niter} iterations for board {init_args}")
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
    runner(10, allowed_values=range(1, 5), block_dim=(2, 2))


def test_generate_6by6():
    runner(10, allowed_values=range(1, 7), block_dim=(2, 3))


def test_generate_8by8():
    runner(5, allowed_values=range(1, 9), block_dim=(2, 4))


def test_generate_9by9():
    runner(5, allowed_values=range(1, 10), block_dim=(3, 3))


# def test_generate_12by12():
#     runner(1, allowed_values=range(1, 13), block_dim=(4, 3))


# def test_generate_16by16():
#     runner(1, allowed_values=range(1, 17), block_dim=(4, 4))


if __name__ == "__main__":
    test_generate_4by4()
    test_generate_6by6()
    test_generate_8by8()
    test_generate_9by9()
    # test_generate_12by12()
    # test_generate_16by16()

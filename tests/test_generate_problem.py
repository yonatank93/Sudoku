import numpy as np
from sudoku import generate_problem, Board

np.random.seed(1)


# Setup
level = np.random.randint(1, 9)
board = generate_problem(level)


def test_number_empty_tiles():
    """Test if the number of empty tiles in the generated board given the level of
    difficulty is in the expected range, i.e., (10 * (level-1)) (exclsive)
    (10 * level) (inclusive)
    """
    nempty_tiles = np.sum(board == 0)
    # Expected range of the number of empty tiles
    lb = 10 * (level - 1)
    ub = 10 * level
    # Check
    assert (
        lb < nempty_tiles <= ub
    ), "Problem with relating level and number of empty tiles"


def test_board_solvable():
    """Test if the generated board is actually solvable, since we want to generate a
    problem that can be solved, of course.
    """
    # Solve the board
    B = Board(board)
    B.solve()
    # Check
    assert B.solved, "Generated problem might not be solvable."


if __name__ == "__main__":
    test_number_empty_tiles()
    test_board_solvable()

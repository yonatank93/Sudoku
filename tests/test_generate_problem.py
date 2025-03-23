import numpy as np
from sudoku import generate_problem, Board

np.random.seed(1)


# Setup
level = np.random.randint(1, 5)
board = generate_problem(level)


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

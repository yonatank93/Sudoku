"""This example is to give a basic usage of this package to solve a Sudoku
problem.
"""

from sudoku import Board

# Write the problem as a list. Zeros represent empty tiles.
problem = [
    [4, 9, 6, 7, 0, 0, 8, 5, 2],
    [0, 7, 0, 0, 4, 8, 3, 6, 9],
    [0, 0, 0, 6, 9, 0, 0, 0, 1],
    [0, 0, 2, 0, 7, 5, 1, 4, 8],
    [0, 0, 9, 0, 8, 6, 0, 0, 0],
    [0, 8, 7, 4, 1, 0, 9, 0, 6],
    [7, 0, 4, 0, 0, 9, 0, 8, 0],
    [9, 3, 0, 0, 0, 7, 6, 1, 4],
    [0, 0, 8, 0, 5, 0, 2, 0, 7],
]

# Instantiate the board
board = Board(problem)
# Solve the problem
board.solve()
# Print the solved board
board.display()

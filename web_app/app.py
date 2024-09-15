from flask import Flask, render_template, request
from sudoku import Board
import numpy as np

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sudoku_input = []
        for i in range(9):
            row = []
            for j in range(9):
                value = request.form.get(f"cell{i}{j}")
                print(value)
                row.append(int(value) if value else 0)
            sudoku_input.append(row)

        # Solve the sudoku
        solution = solve_sudoku(sudoku_input)

        return render_template("sudoku.html", solution=solution)

    return render_template("sudoku.html", solution=np.zeros((9, 9)))


def solve_sudoku(sudoku_problem):
    sudoku_problem = np.array(sudoku_problem)  # Ensure np.array
    board = Board(sudoku_problem)  # Create a board object
    board.solve(verbose=False)  # Solve the board
    return board.board


if __name__ == "__main__":
    app.run(debug=True)

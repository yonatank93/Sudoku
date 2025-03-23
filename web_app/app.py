from flask import Flask, render_template, request, jsonify
from sudoku import generate_problem, Board
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


@app.route("/generate", methods=["GET"])
def generate_sudoku():
    level = request.args.get(
        "level", default=3, type=int
    )  # Get level from query parameters
    problem = generate_problem(level)
    return jsonify({"problem": problem.tolist()})


@app.route("/check_solution", methods=["POST"])
def check_solution():
    data = request.get_json()  # Get the JSON data from the client
    problem = data.get("problem")
    print(problem)
    # Solve or check if the problem is solved
    solved = Board(problem).solved  # Replace with your solving logic
    return jsonify({"solved": solved})


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, render_template, request, jsonify
from sudoku import generate_problem, Sudoku

app = Flask(__name__)


def _empty_board() -> list:
    return [[0 for _ in range(9)] for _ in range(9)]


def parse_board_form(form) -> list:
    """Parse 9x9 cell inputs from a submitted HTML form."""
    sudoku_input = []
    for i in range(9):
        row = []
        for j in range(9):
            raw = (form.get(f"cell{i}{j}") or "").strip()
            if not raw:
                row.append(0)
            else:
                val = int(raw)
                if not (1 <= val <= 9):
                    raise ValueError(
                        f"Invalid value '{raw}' at cell ({i + 1}, {j + 1}); "
                        "must be between 1 and 9."
                    )
                row.append(val)
        sudoku_input.append(row)
    return sudoku_input


def solve_sudoku(sudoku_problem) -> list:
    """Solve a 9x9 Sudoku puzzle and return the solved board."""
    board = Sudoku(sudoku_problem)
    board.solve(verbose=False)
    return board.board


def check_board_solved(problem) -> bool:
    """Return True if problem is a valid, completely solved 9x9 Sudoku board."""
    try:
        return bool(Sudoku(problem).solved)
    except (AssertionError, ValueError, TypeError):
        return False


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            sudoku_input = parse_board_form(request.form)
        except ValueError as err:
            return render_template(
                "sudoku.html",
                solution=_empty_board(),
                original_puzzle=_empty_board(),
                is_solved=False,
                error_message=str(err),
            )

        # Keep track of the original puzzle before solving
        original_puzzle = [row[:] for row in sudoku_input]

        # Solve the Sudoku
        try:
            solution = solve_sudoku(sudoku_input)
        except (AssertionError, ValueError) as err:
            return render_template(
                "sudoku.html",
                solution=sudoku_input,
                original_puzzle=_empty_board(),
                is_solved=False,
                error_message=str(err),
            )

        return render_template(
            "sudoku.html",
            solution=solution,
            original_puzzle=original_puzzle,
            is_solved=True,
            error_message="",
        )

    return render_template(
        "sudoku.html",
        solution=_empty_board(),
        original_puzzle=_empty_board(),
        is_solved=False,
        error_message="",
    )


@app.route("/generate", methods=["GET"])
def generate_sudoku():
    level = request.args.get("level", default=3, type=int)
    if level is None or not (1 <= level <= 5):
        return (
            jsonify({"error": "Difficulty level must be an integer from 1 to 5."}),
            400,
        )
    problem = generate_problem(level)
    return jsonify({"problem": problem})


@app.route("/check_solution", methods=["POST"])
def check_solution():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "problem" not in data:
        return jsonify({"error": "Missing 'problem' payload.", "solved": False}), 400
    solved = check_board_solved(data.get("problem"))
    return jsonify({"solved": solved})


# Add the main() function to start the Flask app
def main():
    app.run(debug=True)


if __name__ == "__main__":
    main()

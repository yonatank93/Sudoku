import argparse

from flask import Flask, render_template, request, jsonify

from sudoku.web_app.engine import (
    BOARD_PRESETS,
    check_board_solved,
    check_solution_payload,
    empty_board,
    generate_payload,
    normalize_board,
    parse_allowed_values,
    resolve_board_config,
    solve_payload,
    solve_steps_payload,
    solve_sudoku,
    solve_sudoku_steps,
)

app = Flask(__name__)


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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            sudoku_input = parse_board_form(request.form)
        except ValueError as err:
            return render_template(
                "sudoku.html",
                solution=empty_board(),
                original_puzzle=empty_board(),
                is_solved=False,
                error_message=str(err),
            )

        original_puzzle = [row[:] for row in sudoku_input]

        try:
            solution = solve_sudoku(sudoku_input)
        except (AssertionError, ValueError) as err:
            return render_template(
                "sudoku.html",
                solution=sudoku_input,
                original_puzzle=empty_board(),
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
        solution=empty_board(),
        original_puzzle=empty_board(),
        is_solved=False,
        error_message="",
    )


@app.route("/generate", methods=["GET"])
def generate_sudoku():
    level = request.args.get("level", default=3, type=int)
    size = request.args.get("size", default=None, type=str)
    raw_allowed = request.args.get("allowed_values", default=None, type=str)
    block_rows = request.args.get("block_rows", default=None, type=int)
    block_cols = request.args.get("block_cols", default=None, type=int)
    block_dim = (
        (block_rows, block_cols)
        if block_rows is not None and block_cols is not None
        else None
    )

    try:
        payload = generate_payload(
            level=level,
            size=size,
            allowed_values=raw_allowed,
            block_dim=block_dim,
        )
    except (AssertionError, ValueError) as err:
        return jsonify({"error": str(err)}), 400

    return jsonify(payload)


@app.route("/solve", methods=["POST"])
def solve_endpoint():
    data = request.get_json(silent=True)
    try:
        result = solve_payload(data)
    except (AssertionError, ValueError, TypeError) as err:
        return jsonify({"error": str(err)}), 400
    return jsonify(result)


@app.route("/solve_steps", methods=["POST"])
def solve_steps_endpoint():
    data = request.get_json(silent=True)
    try:
        result = solve_steps_payload(data)
    except (AssertionError, ValueError, TypeError) as err:
        return jsonify({"error": str(err)}), 400
    return jsonify(result)


@app.route("/check_solution", methods=["POST"])
def check_solution():
    data = request.get_json(silent=True)
    try:
        result = check_solution_payload(data)
    except ValueError as err:
        return jsonify({"error": str(err), "solved": False}), 400
    return jsonify(result)


def parse_cli_args(argv=None):
    """Parse CLI arguments for the sudoku-play web server."""
    parser = argparse.ArgumentParser(description="Run the Sudoku Flask web app")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host interface to bind to (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Port to listen on (default: 5000)",
    )
    parser.add_argument(
        "--debug",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable or disable Flask debug mode (default: enabled)",
    )
    return parser.parse_args(argv)


# Add the main() function to start the Flask app
def main(argv=None):
    args = parse_cli_args(argv)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()

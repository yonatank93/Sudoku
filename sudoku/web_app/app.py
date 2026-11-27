import argparse
import copy
import time

from flask import Flask, render_template, request, jsonify

from sudoku import generate_problem, Sudoku
from sudoku.cell import empty_cell_repr

app = Flask(__name__)

BOARD_PRESETS = {
    "4x4": {"block_dim": (2, 2), "allowed_values": list("1234")},
    "6x6": {"block_dim": (2, 3), "allowed_values": list("123456")},
    "8x8": {"block_dim": (2, 4), "allowed_values": list("12345678")},
    "9x9": {"block_dim": (3, 3), "allowed_values": list("123456789")},
    "16x16": {"block_dim": (4, 4), "allowed_values": list("123456789abcdefg")},
}


def _empty_board(size: int = 9) -> list:
    return [[0 for _ in range(size)] for _ in range(size)]


def parse_allowed_values(raw) -> list:
    """Parse allowed_values from a list, continuous string, or comma-separated string."""
    if isinstance(raw, str):
        stripped = raw.strip()
        if "," in stripped:
            values = [part.strip() for part in stripped.split(",") if part.strip()]
        else:
            values = list(stripped)
    elif isinstance(raw, (list, tuple, range)):
        values = list(raw)
    else:
        raise ValueError("allowed_values must be a string or list of symbols.")

    if len(values) < 2:
        raise ValueError("At least 2 allowed values are required.")
    if len(values) != len(set(values)):
        raise ValueError("Allowed values must not contain duplicates.")
    return values


def resolve_board_config(
    size: str = None,
    allowed_values=None,
    block_dim=None,
    default_int_9x9: bool = True,
):
    """Resolve and validate (allowed_values, block_dim) from preset or explicit values."""
    if size is not None:
        if size not in BOARD_PRESETS:
            raise ValueError(
                f"Unknown board size '{size}'. "
                f"Choose from: {', '.join(BOARD_PRESETS)}."
            )
        preset = BOARD_PRESETS[size]
        return list(preset["allowed_values"]), tuple(preset["block_dim"])

    if allowed_values is None and block_dim is None:
        if default_int_9x9:
            return list(range(1, 10)), (3, 3)
        preset = BOARD_PRESETS["9x9"]
        return list(preset["allowed_values"]), tuple(preset["block_dim"])

    if allowed_values is None or block_dim is None:
        raise ValueError(
            "Both 'allowed_values' and 'block_dim' must be provided together."
        )

    vals = parse_allowed_values(allowed_values)
    try:
        dim = tuple(int(x) for x in block_dim)
    except (TypeError, ValueError) as exc:
        raise ValueError("block_dim must be two positive integers.") from exc

    if len(dim) != 2 or dim[0] <= 0 or dim[1] <= 0:
        raise ValueError("block_dim must be two positive integers.")
    if dim[0] * dim[1] != len(vals):
        raise ValueError(
            "Product of block dimensions must equal the number of allowed values."
        )
    return vals, dim


def normalize_board(problem, allowed_values: list) -> list:
    """Normalize a 2D board payload so cell values match allowed_values types."""
    if not isinstance(problem, list):
        raise ValueError("Problem must be a 2D list.")

    str_to_canonical = {str(v): v for v in allowed_values}
    allowed_set = set(allowed_values)
    normalized = []

    for row in problem:
        if isinstance(row, str):
            row = list(row)
        elif not isinstance(row, list):
            raise ValueError("Each row in problem must be a list or string.")
        norm_row = []
        for val in row:
            if val in allowed_set:
                norm_row.append(val)
            elif isinstance(val, str) and val.strip() == "":
                norm_row.append(0)
            elif val is None:
                norm_row.append(0)
            elif str(val) in str_to_canonical:
                norm_row.append(str_to_canonical[str(val)])
            elif val in empty_cell_repr:
                norm_row.append(0)
            else:
                norm_row.append(val)
        normalized.append(norm_row)
    return normalized


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


def solve_sudoku(sudoku_problem, allowed_values=None, block_dim=None) -> list:
    """Solve a Sudoku puzzle and return the solved board."""
    vals, dim = resolve_board_config(
        allowed_values=allowed_values, block_dim=block_dim
    )
    norm = normalize_board(sudoku_problem, vals)
    board = Sudoku(norm, allowed_values=vals, block_dim=dim)
    board.solve(verbose=False)
    return board.board


def solve_sudoku_steps(sudoku_problem, allowed_values, block_dim) -> dict:
    """Solve a Sudoku puzzle and record the board after each solver step."""
    norm = normalize_board(sudoku_problem, allowed_values)
    board = Sudoku(norm, allowed_values=allowed_values, block_dim=block_dim)

    if board.solved:
        return {
            "steps": [],
            "solution": copy.deepcopy(board.board),
            "total_steps": 0,
        }

    trace = []
    prev_board = copy.deepcopy(board.board)
    prev_empty = len(board.empty_cells)

    def record_step(inst):
        nonlocal prev_board, prev_empty
        cur_board = copy.deepcopy(inst.board)
        cur_empty = len(inst.empty_cells)
        changed = [
            [r, c]
            for r in range(len(cur_board))
            for c in range(len(cur_board[r]))
            if cur_board[r][c] != prev_board[r][c]
        ]
        trace.append(
            {
                "step": len(trace) + 1,
                "niter": inst.niter,
                "board": cur_board,
                "empty_count": cur_empty,
                "changed": changed,
                "reverted": cur_empty > prev_empty,
            }
        )
        prev_board = cur_board
        prev_empty = cur_empty

    board.solve(callback=record_step, verbose=False)
    return {
        "steps": trace,
        "solution": copy.deepcopy(board.board),
        "total_steps": len(trace),
    }


def compute_hint(
    sudoku_problem,
    allowed_values,
    block_dim,
    row=None,
    col=None,
    mode: str = "cell",
) -> dict:
    """Return candidate values for a cell or reveal one valid cell value."""
    norm = normalize_board(sudoku_problem, allowed_values)
    board = Sudoku(norm, allowed_values=allowed_values, block_dim=block_dim)
    n = len(allowed_values)

    if row is not None or col is not None:
        if row is None or col is None:
            raise ValueError("Both 'row' and 'col' must be specified together.")
        row, col = int(row), int(col)
        if not (0 <= row < n and 0 <= col < n):
            raise ValueError(f"Cell coordinates ({row}, {col}) are out of bounds.")

    if mode == "candidates":
        if row is None:
            raise ValueError("Select a cell to inspect its possible values.")
        cell = board.cells[row, col]
        return {
            "row": row,
            "col": col,
            "is_empty": cell.is_empty,
            "possible_values": list(cell.possible_values),
        }

    if mode != "cell":
        raise ValueError("Hint mode must be 'cell' or 'candidates'.")

    if board.solved:
        return {"already_solved": True}

    empty_cells = board.empty_cells
    if row is not None and board.cells[row, col].is_empty:
        target_cell = board.cells[row, col]
    else:
        target_cell = min(empty_cells, key=lambda c: len(c.possible_values))
        row, col = target_cell.row_idx, target_cell.column_idx

    poss_before = list(target_cell.possible_values)
    board.solve(verbose=False)
    return {
        "already_solved": False,
        "row": row,
        "col": col,
        "value": board.board[row][col],
        "possible_values": poss_before,
    }


def check_board_solved(problem, allowed_values=None, block_dim=None) -> bool:
    """Return True if problem is a valid, completely solved Sudoku board."""
    try:
        vals, dim = resolve_board_config(
            allowed_values=allowed_values, block_dim=block_dim
        )
        norm = normalize_board(problem, vals)
        return bool(Sudoku(norm, allowed_values=vals, block_dim=dim).solved)
    except (AssertionError, ValueError, TypeError):
        return False


def _extract_json_board_request(data):
    """Validate JSON request payload and return (problem, allowed_values, block_dim)."""
    if not isinstance(data, dict) or "problem" not in data:
        raise ValueError("Missing 'problem' payload.")
    vals, dim = resolve_board_config(
        size=data.get("size"),
        allowed_values=data.get("allowed_values"),
        block_dim=data.get("block_dim"),
        default_int_9x9=True,
    )
    return data["problem"], vals, dim


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

        original_puzzle = [row[:] for row in sudoku_input]

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
        vals, dim = resolve_board_config(
            size=size,
            allowed_values=raw_allowed,
            block_dim=block_dim,
            default_int_9x9=(size is None and raw_allowed is None),
        )
        problem = generate_problem(
            level=level, allowed_values=vals, block_dim=dim
        )
    except (AssertionError, ValueError) as err:
        return jsonify({"error": str(err)}), 400

    return jsonify(
        {
            "problem": problem,
            "allowed_values": vals,
            "block_dim": list(dim),
        }
    )


@app.route("/solve", methods=["POST"])
def solve_endpoint():
    data = request.get_json(silent=True)
    try:
        problem, vals, dim = _extract_json_board_request(data)
        norm = normalize_board(problem, vals)
        t0 = time.perf_counter()
        board = Sudoku(norm, allowed_values=vals, block_dim=dim)
        board.solve(verbose=False)
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    except (AssertionError, ValueError, TypeError) as err:
        return jsonify({"error": str(err)}), 400

    return jsonify(
        {
            "solution": board.board,
            "steps": board._nstep_call,
            "elapsed_ms": elapsed_ms,
        }
    )


@app.route("/solve_steps", methods=["POST"])
def solve_steps_endpoint():
    data = request.get_json(silent=True)
    try:
        problem, vals, dim = _extract_json_board_request(data)
        result = solve_sudoku_steps(problem, vals, dim)
    except (AssertionError, ValueError, TypeError) as err:
        return jsonify({"error": str(err)}), 400

    return jsonify(result)


@app.route("/hint", methods=["POST"])
def hint_endpoint():
    data = request.get_json(silent=True)
    try:
        problem, vals, dim = _extract_json_board_request(data)
        result = compute_hint(
            problem,
            vals,
            dim,
            row=data.get("row"),
            col=data.get("col"),
            mode=data.get("mode", "cell"),
        )
    except (AssertionError, ValueError, TypeError) as err:
        return jsonify({"error": str(err)}), 400

    return jsonify(result)


@app.route("/check_solution", methods=["POST"])
def check_solution():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or "problem" not in data:
        return jsonify({"error": "Missing 'problem' payload.", "solved": False}), 400
    try:
        _, vals, dim = _extract_json_board_request(data)
    except ValueError:
        return jsonify({"solved": False})
    solved = check_board_solved(data.get("problem"), vals, dim)
    return jsonify({"solved": solved})


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

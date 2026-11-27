"""Flask-free backend engine shared by both the local Flask server and Pyodide."""

import copy
import time

from sudoku import generate_problem, Sudoku
from sudoku.cell import empty_cell_repr

BOARD_PRESETS = {
    "4x4": {"block_dim": (2, 2), "allowed_values": list("1234")},
    "6x6": {"block_dim": (2, 3), "allowed_values": list("123456")},
    "8x8": {"block_dim": (2, 4), "allowed_values": list("12345678")},
    "9x9": {"block_dim": (3, 3), "allowed_values": list("123456789")},
    "16x16": {"block_dim": (4, 4), "allowed_values": list("123456789abcdefg")},
}


def empty_board(size: int = 9) -> list:
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


def extract_board_request(data):
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


def generate_payload(
    level: int = 3,
    size: str = None,
    allowed_values=None,
    block_dim=None,
) -> dict:
    """Generate a Sudoku problem and return the JSON response payload."""
    if level is None or isinstance(level, bool) or not isinstance(level, int) or not (1 <= level <= 5):
        raise ValueError("Difficulty level must be an integer from 1 to 5.")
    vals, dim = resolve_board_config(
        size=size,
        allowed_values=allowed_values,
        block_dim=block_dim,
        default_int_9x9=(size is None and allowed_values is None),
    )
    problem = generate_problem(level=level, allowed_values=vals, block_dim=dim)
    return {
        "problem": problem,
        "allowed_values": vals,
        "block_dim": list(dim),
    }


def solve_payload(data: dict) -> dict:
    """Solve a JSON board payload and return solution, step count, and elapsed_ms."""
    problem, vals, dim = extract_board_request(data)
    norm = normalize_board(problem, vals)
    t0 = time.perf_counter()
    board = Sudoku(norm, allowed_values=vals, block_dim=dim)
    board.solve(verbose=False)
    elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "solution": board.board,
        "steps": board._nstep_call,
        "elapsed_ms": elapsed_ms,
    }


def solve_steps_payload(data: dict) -> dict:
    """Solve a JSON board payload and return the step-by-step solver trace."""
    problem, vals, dim = extract_board_request(data)
    return solve_sudoku_steps(problem, vals, dim)


def check_solution_payload(data: dict) -> dict:
    """Check whether a JSON board payload is completely and validly solved."""
    if not isinstance(data, dict) or "problem" not in data:
        raise ValueError("Missing 'problem' payload.")
    try:
        _, vals, dim = extract_board_request(data)
    except ValueError:
        return {"solved": False}
    return {"solved": check_board_solved(data.get("problem"), vals, dim)}

import importlib
import json
import sys
import types
import unittest
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent / "sudoku" / "web_app" / "templates"
)

try:
    import flask as _real_flask  # noqa: F401

    HAS_FLASK = True
except ModuleNotFoundError:
    HAS_FLASK = False

try:
    import jinja2

    HAS_JINJA2 = True
except ModuleNotFoundError:
    HAS_JINJA2 = False


def _load_board_01():
    with open(DATA_DIR / "9by9" / "board_01.json", "r") as f:
        return json.load(f)


def _board_to_form(board):
    return {
        f"cell{i}{j}": (str(board[i][j]) if board[i][j] else "")
        for i in range(9)
        for j in range(9)
    }


def _make_flask_stub():
    stub = types.ModuleType("flask")

    class _DummyApp:
        def __init__(self, name):
            self.name = name
            self.routes = {}

        def route(self, path, methods=None):
            def decorator(fn):
                self.routes[path] = fn
                return fn

            return decorator

        def run(self, **kwargs):
            pass

    class _DummyArgs(dict):
        def get(self, key, default=None, type=None):
            if key not in self:
                return default
            val = self[key]
            if type is not None:
                try:
                    return type(val)
                except (ValueError, TypeError):
                    return default
            return val

    class _DummyRequest:
        method = "GET"
        form = {}
        args = _DummyArgs()
        _json = None

        def get_json(self, silent=False):
            return self._json

    stub.Flask = _DummyApp
    stub._DummyArgs = _DummyArgs
    stub.request = _DummyRequest()
    stub.render_template = lambda tmpl, **ctx: (tmpl, ctx)
    stub.jsonify = lambda obj: obj
    return stub


class TestWebAppLogic(unittest.TestCase):
    """Tests web app helpers and route logic without requiring Flask installed."""

    @classmethod
    def setUpClass(cls):
        cls._prev_flask = sys.modules.get("flask")
        cls._prev_webapp = sys.modules.get("sudoku.web_app.app")
        cls._stub = _make_flask_stub()
        sys.modules["flask"] = cls._stub
        sys.modules.pop("sudoku.web_app.app", None)
        cls.webapp = importlib.import_module("sudoku.web_app.app")
        cls.b01 = _load_board_01()

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("sudoku.web_app.app", None)
        if cls._prev_flask is not None:
            sys.modules["flask"] = cls._prev_flask
        else:
            sys.modules.pop("flask", None)
        if cls._prev_webapp is not None:
            sys.modules["sudoku.web_app.app"] = cls._prev_webapp

    def test_parse_board_form_valid_and_invalid(self):
        form = _board_to_form(self.b01["board"])
        self.assertEqual(self.webapp.parse_board_form(form), self.b01["board"])

        with self.assertRaises(ValueError):
            self.webapp.parse_board_form({"cell00": "10"})
        with self.assertRaises(ValueError):
            self.webapp.parse_board_form({"cell00": "0"})
        with self.assertRaises(ValueError):
            self.webapp.parse_board_form({"cell00": "abc"})

    def test_solve_sudoku_and_check_board_solved(self):
        self.assertEqual(
            self.webapp.solve_sudoku(self.b01["board"]), self.b01["solution"]
        )
        self.assertTrue(self.webapp.check_board_solved(self.b01["solution"]))
        self.assertFalse(self.webapp.check_board_solved(self.b01["board"]))

        dup_board = [[1, 1] + [0] * 7] + [[0] * 9 for _ in range(8)]
        self.assertFalse(self.webapp.check_board_solved(dup_board))
        self.assertFalse(self.webapp.check_board_solved(None))
        self.assertFalse(self.webapp.check_board_solved([[1, 2]]))

    def test_index_get_and_post_routes(self):
        req = self._stub.request

        # GET /
        req.method = "GET"
        tmpl, ctx = self.webapp.index()
        self.assertEqual(tmpl, "sudoku.html")
        self.assertFalse(ctx["is_solved"])
        self.assertEqual(ctx["error_message"], "")

        # POST / valid puzzle
        req.method = "POST"
        req.form = _board_to_form(self.b01["board"])
        tmpl, ctx = self.webapp.index()
        self.assertTrue(ctx["is_solved"])
        self.assertEqual(ctx["solution"], self.b01["solution"])
        self.assertEqual(ctx["error_message"], "")

        # POST / duplicate digit in row
        bad_form = _board_to_form(self.b01["board"])
        bad_form["cell00"] = "7"
        req.form = bad_form
        tmpl, ctx = self.webapp.index()
        self.assertFalse(ctx["is_solved"])
        self.assertIn("repetition", ctx["error_message"])

        # POST / unsolvable board
        with open(DATA_DIR / "9by9" / "board_10.json", "r") as f:
            b10 = json.load(f)["board"]
        b10[0][0] = 5
        req.form = _board_to_form(b10)
        tmpl, ctx = self.webapp.index()
        self.assertFalse(ctx["is_solved"])
        self.assertIn("no valid solution", ctx["error_message"])

    def test_generate_and_check_solution_routes(self):
        req = self._stub.request

        # GET /generate valid
        for level in range(1, 6):
            req.args = self._stub._DummyArgs({"level": str(level)})
            res = self.webapp.generate_sudoku()
            self.assertIsInstance(res["problem"], list)
            self.assertEqual(len(res["problem"]), 9)

        # GET /generate out-of-range
        req.args = self._stub._DummyArgs({"level": "99"})
        res, status = self.webapp.generate_sudoku()
        self.assertEqual(status, 400)
        self.assertIn("error", res)

        # POST /check_solution valid, invalid duplicate, missing payload
        req._json = {"problem": self.b01["solution"]}
        self.assertEqual(self.webapp.check_solution(), {"solved": True})

        dup_board = [[1, 1] + [0] * 7] + [[0] * 9 for _ in range(8)]
        req._json = {"problem": dup_board}
        self.assertEqual(self.webapp.check_solution(), {"solved": False})

        req._json = None
        res, status = self.webapp.check_solution()
        self.assertEqual(status, 400)
        self.assertFalse(res["solved"])


@unittest.skipUnless(HAS_JINJA2, "jinja2 is not installed")
class TestWebAppTemplate(unittest.TestCase):
    def setUp(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)))
        self.template = env.get_template("sudoku.html")
        self.empty = [[0] * 9 for _ in range(9)]

    def test_template_fresh_get_not_readonly_or_disabled(self):
        rendered = self.template.render(
            solution=self.empty,
            original_puzzle=self.empty,
            is_solved=False,
            error_message="",
        )
        self.assertIn("const initialSolved = false;", rendered)
        self.assertNotIn('localStorage.setItem("buttonsDisabled"', rendered)
        table_html = rendered.split("<table")[1].split("</table>")[0]
        self.assertNotIn("readonly", table_html)

    def test_template_error_post_preserves_editable_cells_and_shows_error(self):
        partial = [r[:] for r in self.empty]
        partial[0][0] = 5
        rendered = self.template.render(
            solution=partial,
            original_puzzle=self.empty,
            is_solved=False,
            error_message="Board is invalid",
        )
        self.assertIn("const initialSolved = false;", rendered)
        self.assertIn("Board is invalid", rendered)
        table_html = rendered.split("<table")[1].split("</table>")[0]
        self.assertIn('value="5"', table_html)
        self.assertNotIn("readonly", table_html)

    def test_template_solved_post_locks_cells_and_marks_prefilled(self):
        b01 = _load_board_01()
        rendered = self.template.render(
            solution=b01["solution"],
            original_puzzle=b01["board"],
            is_solved=True,
            error_message="",
        )
        self.assertIn("const initialSolved = true;", rendered)
        table_html = rendered.split("<table")[1].split("</table>")[0]
        self.assertEqual(table_html.count("readonly"), 81)
        n_clues = sum(cell > 0 for row in b01["board"] for cell in row)
        self.assertEqual(table_html.count('class="prefilled"'), n_clues)


@unittest.skipUnless(HAS_FLASK, "flask is not installed")
class TestWebAppFlaskIntegration(unittest.TestCase):
    """Full HTTP integration tests using Flask's test_client when installed."""

    def setUp(self):
        import sudoku.web_app.app as webapp

        webapp.app.config["TESTING"] = True
        self.client = webapp.app.test_client()
        self.b01 = _load_board_01()

    def test_get_index(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"const initialSolved = false;", resp.data)

    def test_generate_endpoint(self):
        resp = self.client.get("/generate?level=3")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(len(data["problem"]), 9)

        bad_resp = self.client.get("/generate?level=99")
        self.assertEqual(bad_resp.status_code, 400)

    def test_check_solution_endpoint(self):
        resp_ok = self.client.post(
            "/check_solution", json={"problem": self.b01["solution"]}
        )
        self.assertEqual(resp_ok.status_code, 200)
        self.assertTrue(resp_ok.get_json()["solved"])

        dup = [[1, 1] + [0] * 7] + [[0] * 9 for _ in range(8)]
        resp_dup = self.client.post("/check_solution", json={"problem": dup})
        self.assertEqual(resp_dup.status_code, 200)
        self.assertFalse(resp_dup.get_json()["solved"])

    def test_post_solve_valid_and_invalid(self):
        resp_ok = self.client.post("/", data=_board_to_form(self.b01["board"]))
        self.assertEqual(resp_ok.status_code, 200)
        self.assertIn(b"const initialSolved = true;", resp_ok.data)

        bad_form = _board_to_form(self.b01["board"])
        bad_form["cell00"] = "7"
        resp_bad = self.client.post("/", data=bad_form)
        self.assertEqual(resp_bad.status_code, 200)
        self.assertIn(b"const initialSolved = false;", resp_bad.data)
        self.assertIn(b"repetition", resp_bad.data)


if __name__ == "__main__":
    unittest.main()

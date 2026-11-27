import importlib
import json
import shutil
import subprocess
import sys
import types
import unittest
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TEMPLATE_DIR = (
    Path(__file__).resolve().parent.parent / "sudoku" / "web_app" / "templates"
)
STATIC_DIR = Path(__file__).resolve().parent.parent / "sudoku" / "web_app" / "static"
HAS_NODE = shutil.which("node") is not None

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


class TestWebAppEngine(unittest.TestCase):
    """Direct tests of the Flask-free engine module used by Flask and Pyodide."""

    def test_engine_payload_roundtrip_without_flask(self):
        from sudoku.web_app import engine

        gen = engine.generate_payload(level=3, size="6x6")
        self.assertEqual(gen["block_dim"], [2, 3])
        self.assertEqual(len(gen["problem"]), 6)

        solved = engine.solve_payload(gen)
        self.assertGreater(solved["steps"], 0)
        self.assertTrue(
            engine.check_solution_payload(
                {
                    "problem": solved["solution"],
                    "allowed_values": gen["allowed_values"],
                    "block_dim": gen["block_dim"],
                }
            )["solved"]
        )

        steps = engine.solve_steps_payload(gen)
        self.assertEqual(steps["solution"], solved["solution"])
        self.assertEqual(steps["total_steps"], len(steps["steps"]))

        with self.assertRaises(ValueError):
            engine.generate_payload(level=9)


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

    def test_parse_cli_args(self):
        defaults = self.webapp.parse_cli_args([])
        self.assertEqual(defaults.host, "127.0.0.1")
        self.assertEqual(defaults.port, 5000)
        self.assertTrue(defaults.debug)

        custom = self.webapp.parse_cli_args(
            ["--host", "0.0.0.0", "--port", "8080", "--no-debug"]
        )
        self.assertEqual(custom.host, "0.0.0.0")
        self.assertEqual(custom.port, 8080)
        self.assertFalse(custom.debug)

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

        # GET /generate with multi-dimension presets (4x4, 6x6, 8x8, 16x16) and custom
        for size_key, expected_n in [("4x4", 4), ("6x6", 6), ("8x8", 8), ("16x16", 16)]:
            req.args = self._stub._DummyArgs({"level": "3", "size": size_key})
            res = self.webapp.generate_sudoku()
            self.assertEqual(len(res["problem"]), expected_n)
            self.assertEqual(len(res["allowed_values"]), expected_n)

        req.args = self._stub._DummyArgs(
            {
                "level": "2",
                "allowed_values": "ABCD",
                "block_rows": "2",
                "block_cols": "2",
            }
        )
        res_custom = self.webapp.generate_sudoku()
        self.assertEqual(res_custom["allowed_values"], ["A", "B", "C", "D"])
        self.assertEqual(res_custom["block_dim"], [2, 2])
        self.assertEqual(len(res_custom["problem"]), 4)

        req.args = self._stub._DummyArgs({"level": "3", "size": "99x99"})
        res_bad_size, status = self.webapp.generate_sudoku()
        self.assertEqual(status, 400)
        self.assertIn("error", res_bad_size)

        # POST /check_solution valid, invalid duplicate, missing payload, multi-dim
        req._json = {"problem": self.b01["solution"]}
        self.assertEqual(self.webapp.check_solution(), {"solved": True})

        req._json = {
            "problem": [
                ["1", "2", "3", "4"],
                ["3", "4", "1", "2"],
                ["2", "1", "4", "3"],
                ["4", "3", "2", "1"],
            ],
            "size": "4x4",
        }
        self.assertEqual(self.webapp.check_solution(), {"solved": True})

        dup_board = [[1, 1] + [0] * 7] + [[0] * 9 for _ in range(8)]
        req._json = {"problem": dup_board}
        self.assertEqual(self.webapp.check_solution(), {"solved": False})

        req._json = None
        res, status = self.webapp.check_solution()
        self.assertEqual(status, 400)
        self.assertFalse(res["solved"])

    def test_solve_and_solve_steps_endpoints(self):
        req = self._stub.request

        # POST /solve (9x9 + 6x6 custom)
        req._json = {"problem": self.b01["board"]}
        res_solve = self.webapp.solve_endpoint()
        self.assertEqual(res_solve["solution"], self.b01["solution"])
        self.assertGreater(res_solve["steps"], 0)

        with open(DATA_DIR / "6by6" / "board_01.json", "r") as f:
            b6 = json.load(f)
        req._json = {
            "problem": [[str(c) if c else "" for c in r] for r in b6["board"]],
            "size": "6x6",
        }
        res_6 = self.webapp.solve_endpoint()
        self.assertEqual(
            res_6["solution"], [[str(c) for c in r] for r in b6["solution"]]
        )

        # POST /solve on invalid/unsolvable returns 400
        req._json = {"problem": [[1, 1] + [0] * 7] + [[0] * 9 for _ in range(8)]}
        res_err, status = self.webapp.solve_endpoint()
        self.assertEqual(status, 400)
        self.assertIn("error", res_err)

        # POST /solve_steps
        req._json = {"problem": self.b01["board"]}
        res_steps = self.webapp.solve_steps_endpoint()
        self.assertEqual(res_steps["solution"], self.b01["solution"])
        self.assertEqual(res_steps["total_steps"], len(res_steps["steps"]))
        self.assertGreater(res_steps["total_steps"], 0)
        self.assertEqual(res_steps["steps"][-1]["empty_count"], 0)


@unittest.skipUnless(HAS_JINJA2, "jinja2 is not installed")
class TestWebAppTemplate(unittest.TestCase):
    def setUp(self):
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)))
        env.globals["url_for"] = lambda endpoint, filename="": f"/{endpoint}/{filename}"
        env.filters["tojson"] = json.dumps
        self.template = env.get_template("sudoku.html")
        self.empty = [[0] * 9 for _ in range(9)]

    def test_static_assets_exist(self):
        static_dir = TEMPLATE_DIR.parent / "static"
        self.assertTrue((static_dir / "style.css").is_file())
        self.assertTrue((static_dir / "app.js").is_file())

    def test_template_fresh_get_renders_controls_and_initial_state(self):
        rendered = self.template.render(
            solution=self.empty,
            original_puzzle=self.empty,
            is_solved=False,
            error_message="",
        )
        self.assertIn('data-initial-solved="false"', rendered)
        self.assertIn("/static/style.css", rendered)
        self.assertIn("/static/app.js", rendered)
        self.assertIn('id="boardSize"', rendered)
        self.assertIn('id="themeToggle"', rendered)
        self.assertIn('id="sudokuBoard"', rendered)
        self.assertNotIn('id="hintBtn"', rendered)
        self.assertNotIn('id="candidatesBtn"', rendered)
        self.assertIn('id="stepBtn"', rendered)
        self.assertIn('id="animateBtn"', rendered)
        self.assertIn('id="ioPanel"', rendered)
        self.assertIn('"is_solved": false', rendered)

    def test_template_error_post_embeds_board_and_error(self):
        partial = [r[:] for r in self.empty]
        partial[0][0] = 5
        rendered = self.template.render(
            solution=partial,
            original_puzzle=self.empty,
            is_solved=False,
            error_message="Board is invalid",
        )
        self.assertIn('data-initial-solved="false"', rendered)
        self.assertIn("Board is invalid", rendered)
        self.assertIn('"is_solved": false', rendered)

    def test_template_solved_post_embeds_solved_state(self):
        b01 = _load_board_01()
        rendered = self.template.render(
            solution=b01["solution"],
            original_puzzle=b01["board"],
            is_solved=True,
            error_message="",
        )
        self.assertIn('data-initial-solved="true"', rendered)
        self.assertIn('"is_solved": true', rendered)


@unittest.skipUnless(HAS_NODE, "node is not installed")
class TestWebAppFrontendJS(unittest.TestCase):
    """Syntax-check and unit-test pure frontend JS helpers via Node."""

    def test_app_js_syntax(self):
        app_js = STATIC_DIR / "app.js"
        res = subprocess.run(
            ["node", "--check", str(app_js)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, res.stderr)

    def test_app_js_pure_helpers(self):
        app_js = str(STATIC_DIR / "app.js")
        script = f"""
        const assert = require("assert");
        const app = require({json.dumps(app_js)});

        assert.deepStrictEqual(app.parseCustomSymbols("123456"), ["1","2","3","4","5","6"]);
        assert.deepStrictEqual(app.parseCustomSymbols("A, B, C, D"), ["A","B","C","D"]);
        assert.strictEqual(app.normalizeCellSymbol("A", app.BOARD_PRESETS["16x16"].allowedValues), "a");
        assert.strictEqual(app.normalizeCellSymbol("0", ["0","1","2","3"]), "0");
        assert.strictEqual(app.formatTime(65), "01:05");

        // Peer & conflicts
        assert.strictEqual(app.isSamePeer(0, 0, 1, 2, [2, 3]), true);
        assert.strictEqual(app.isSamePeer(0, 0, 1, 3, [2, 3]), false);
        const dupBoard = [
            ["1", "", "1", ""],
            ["", "1", "", ""],
            ["", "", "", "2"],
            ["", "", "", "2"],
        ];
        const conf = app.findConflicts(dupBoard, [2, 2]);
        assert.ok(conf.has("0,0") && conf.has("0,2") && conf.has("1,1") && conf.has("2,3") && conf.has("3,3"));
        assert.deepStrictEqual(app.countRemainingSymbols(dupBoard, ["1","2","3","4"]), {{"1":1,"2":2,"3":4,"4":4}});

        // Notes auto-cleanup
        const notes = app.createEmptyNotes(4);
        notes[0][0].add("1");
        notes[0][3].add("1").add("2");
        notes[2][2].add("1");
        app.clearPeerNotes(notes, 0, 0, "1", [2, 2]);
        assert.strictEqual(notes[0][0].size, 0);
        assert.strictEqual(notes[0][3].has("1"), false);
        assert.strictEqual(notes[0][3].has("2"), true);
        assert.strictEqual(notes[2][2].has("1"), true);

        // Import / Export serialization roundtrip (standard + '0'-allowed + multi-char)
        const b4 = [["1","","3","4"],["3","4","1","2"],["2","1","4","3"],["4","3","2",""]];
        const txt = app.serializeBoardToText(b4, ["1","2","3","4"]);
        assert.strictEqual(txt, "1034\\n3412\\n2143\\n4320");
        assert.deepStrictEqual(app.parseBoardFromText(txt, ["1","2","3","4"]), b4);

        const bZero = [["0","","2","3"],["2","3","0","1"],["1","0","3","2"],["3","2","1",""]];
        const txtZero = app.serializeBoardToText(bZero, ["0","1","2","3"]);
        assert.strictEqual(txtZero.split("\\n")[0], "0_23");
        assert.deepStrictEqual(app.parseBoardFromText(txtZero, ["0","1","2","3"]), bZero);

        assert.throws(() => app.parseBoardFromText("1234\\n1234", ["1","2","3","4"]));
        assert.throws(() => app.parseBoardFromText("123x\\n3412\\n2143\\n4321", ["1","2","3","4"]));
        """
        res = subprocess.run(
            ["node", "-e", script],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, res.stderr)


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
        self.assertIn(b'data-initial-solved="false"', resp.data)

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
        self.assertIn(b'data-initial-solved="true"', resp_ok.data)

        bad_form = _board_to_form(self.b01["board"])
        bad_form["cell00"] = "7"
        resp_bad = self.client.post("/", data=bad_form)
        self.assertEqual(resp_bad.status_code, 200)
        self.assertIn(b'data-initial-solved="false"', resp_bad.data)
        self.assertIn(b"repetition", resp_bad.data)


if __name__ == "__main__":
    unittest.main()

# Sudoku

My take on creating a Sudoku solver with Python (supporting standard 9x9 boards as well as arbitrary board dimensions and custom symbols).


## Install

Install this package from source:

```bash
$ git clone https://github.com/yonatank93/Sudoku.git
$ pip install Sudoku/
```


## Example

### Solving a 9x9 Board

```python
import json
import sudoku

with open("Sudoku/data/9by9/board_01.json", "r") as f:
    data = json.load(f)

board = sudoku.Sudoku(data["board"])
board.solve(verbose=True)
board.display()
```

### Custom Dimensions, Custom Symbols, and Puzzle Generation

```python
import sudoku

# Generate and solve a 6x6 puzzle with 2x3 blocks
problem = sudoku.generate_problem(
    level=3,
    allowed_values=range(1, 7),
    block_dim=(2, 3),
    seed=42,
)
board = sudoku.Sudoku(problem, allowed_values=range(1, 7), block_dim=(2, 3))
board.solve()
board.display()
```


### Command-Line Interface

#### `sudoku-solve`

Interactive CLI to input and solve a Sudoku problem of any dimension. Press Enter to accept the default 9x9 settings (`'123456789'` and `'3 3'`), then enter each row as a continuous string using `"0"`, `"_"`, or `"-"` for empty cells.

```bash
$ sudoku-solve
Input allowed values as a continuous string (default: '123456789'):
Input block dimension as two integers separated by a space (default: '3 3'):
Input each row of the board below:
478693152
526718493
130425076
300147009
000986000
000532000
000369000
003874900
067251380
```

Options:
* `-s`, `--show-init`: display the initial unsolved board before solving
* `-v`, `--verbose`: show step-by-step solving progress

#### `sudoku-generate`

Interactive CLI to generate a Sudoku puzzle for any allowed values, block dimensions, and difficulty level (`1` easiest to `5` hardest):

```bash
$ sudoku-generate -s
```

Options:
* `-s`, `--return-solution`: display the solution along with the generated problem
* `-v`, `--verbose`: print generation progress messages


### Web App

A web app is also included, built with [Flask](https://flask.palletsprojects.com/en/stable/).
It supports playing and solving puzzles across multiple board dimensions (4x4, 6x6, 8x8, 9x9, 16x16 hex, or custom symbols/block dimensions) with:

* Light / Dark mode toggle
* Row, column, block, and matching-symbol highlighting, plus toggleable conflict detection
* Keyboard navigation (`Arrow` keys, `Backspace`/`Delete`, `Ctrl+Z`/`Ctrl+Y` undo/redo) and an interactive symbol pad with remaining counts
* Pencil marks (Notes mode with automatic peer cleanup) and a pauseable timer
* **Next Step**, **Watch Solve** (animated step-by-step playback), and **Solve All** controls powered by your solver
* **Import / Export** for pasting or copying puzzles in text format

To start the server, execute one of the following commands:

```bash
$ python Sudoku/sudoku/web_app/app.py
$ sudoku-play --host 127.0.0.1 --port 5000
```

Options for `sudoku-play`:
* `--host`: host interface to bind to (default: `127.0.0.1`)
* `--port`: port to listen on (default: `5000`)
* `--debug` / `--no-debug`: enable or disable Flask debug mode (default: enabled)

#### GitHub Pages (In-Browser via Pyodide)

The web app can also be hosted statically on GitHub Pages (e.g. `https://yonatank93.github.io/Sudoku/`) by running the exact same Python solver inside the browser via [Pyodide](https://pyodide.org/) in a Web Worker.

* **Automatic deployment:** Pushing to `main` triggers `.github/workflows/deploy-pages.yml` to build and deploy the static bundle automatically (enable once in **Settings → Pages → Source: GitHub Actions**).
* **Local preview of the static build:**

```bash
$ python3 scripts/build_gh_pages.py --out-dir site
$ python3 -m http.server -d site 8000
```

Then open `http://127.0.0.1:8000/` in your browser.


## Tests

Run the test suite from the repository root:

```bash
$ python3 -m unittest discover -s tests -v
```


## Algorithm

1. For each empty tile, list possible values by only looking at the block, row, and column corresponding to that tile.
2. Try to solve the tile by only looking at the list of possible values for that tile.
That is, if the list of possible values only contains one item, then that value must be for that tile.
3. Compare the list of possible values of tiles in the same block.
If there is an item in the list of possible values of a tile that is not in the same kind of list for the other tiles, then that value can only be in that tile.
4. Do the same as step 3 for tiles in the same row and column.
5. Terminate if all tiles are filled.

Special case:
If the empty tiles for before and after applying step 1-4 above are the same, then the algorithm above cannot proceed further.
In this case, find the tile with least number of possible values and set that tile to one of the possible values.
Then, continue with the algorithm above again.


## Disclaimer

This algorithm works for all examples included with this repo!
However, this is probably not the best algorithm for solving Sudoku.


## Contact

Feel free to reach out to my email: kurniawanyo@outlook.com

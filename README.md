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
The web app allows users to play Sudoku and solve problems using a graphical user interface (GUI), if preferred.
To start the server, execute one of the following commands:

```bash
$ python Sudoku/sudoku/web_app/app.py
$ sudoku-play
```


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

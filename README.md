# Sudoku

My take on creating a Sudoku solver with Python


## Install

Install this pacakge from the source:

``` bash
$ git clone https://github.com/yonatank93/Sudoku.git
$ pip install Sudoku/
```

## Example

``` Python
In [1]: import json, sudoku

In [2]: data = json.load(open("Sudoku/data/board_1.json", "r"))

In [3]: board = sudoku.Board(data["board"])

In [4]: board.solve()
Solving time: 0:00:00.018726

In [5]: board.display()
#####################################
# 4 | 7 | 8 # 6 | 9 | 3 # 1 | 5 | 2 #
#-----------#-----------#-----------#
# 5 | 2 | 6 # 7 | 1 | 8 # 4 | 9 | 3 #
#-----------#-----------#-----------#
# 1 | 3 | 9 # 4 | 2 | 5 # 8 | 7 | 6 #
#####################################
# 3 | 8 | 5 # 1 | 4 | 7 # 6 | 2 | 9 #
#-----------#-----------#-----------#
# 7 | 4 | 2 # 9 | 8 | 6 # 5 | 3 | 1 #
#-----------#-----------#-----------#
# 6 | 9 | 1 # 5 | 3 | 2 # 7 | 4 | 8 #
#####################################
# 8 | 5 | 4 # 3 | 6 | 9 # 2 | 1 | 7 #
#-----------#-----------#-----------#
# 2 | 1 | 3 # 8 | 7 | 4 # 9 | 6 | 5 #
#-----------#-----------#-----------#
# 9 | 6 | 7 # 2 | 5 | 1 # 3 | 8 | 4 #
#####################################

In [6]:
```

## Algorithm

1. For each empty tile, list possible values by only looking at the block, row, and collumn corresponding to that tile.
2. Try to solve the tile by only looking at the list of possible values for that tile.
That is, if the list of possible values only contains one item, then that value must be for that tile.
3. Compare the list of possible values of tiles in the same block.
If there is an item in the list of possible values of a tile that is not in the same kind of list for the other tiles, then that value can only be in that tile.
4. Do the same as step 3 for tiles in the same row and column.
5. Terminate if all tiles are filled.


## Disclaimer

For sure this is not the best algorithm for solving Sudoku.
For example, this algorithm can solve boards 1 to 5 in the data, but cannot for boards 6 to 8.

# Sudoku
My take on creating a Sudoku solver with Python

## Algorithm

1. Scan the board
   * Store the value given for each tile. `0` means the tile is empty.
   * Store the location of the block, row, and column for each tile.
3. Scan over each block and list the possible values for each empty tile
4. Scan over each row and update the list of possible values.
5. Scan over each column and update the list of possible values.

## Disclaimer

I don't think this is the best algorithm.

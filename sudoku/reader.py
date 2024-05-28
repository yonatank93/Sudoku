import numpy as np


class UserInput:
    """Interactive method to input the sudoku board.

    Input numbers in each row without any space. Each row should be 9 characters long.
    If the tile is empty, input either "_" (underscore), "-" (dash), " " (empty space), or
    "0".

    Example
    -------
    "123 5_780" is a valid input, where the 4th, 6th, and 9th positions are empty.

    Notes
    -----
    * Each input row should contain 9 characters, including the "empty" characters.
    * Each number 1-9 should only appear at most 1 time in each input row.
    """

    empty_char = ["_", "-", " ", "0"]  # These characters indicate that the tile is empty

    def __init__(self):
        print("Input each row of the board below:")
        self.board = np.zeros((9, 9), dtype=int)
        for ii in range(9):  # There are 9 rows
            self.board[ii] = self.request_line()

    def update_row(self, row):
        """Update the entry of the specified row, with 0-base index."""
        self.board[row] = self.request_line()

    def request_line(self):
        """Request input line and do post-processing."""
        # ii = 0
        while True:
            # Request input
            line = input()

            # Do a bunch of checks
            try:
                # For each line, there should be 9 elements, for a standard sudoku
                self.check_length(line)
                # Each number 1-9 should only appear at most 1 time
                self.check_uniqueness(line)

                # End of check, convert the line string into array
                line = self.convert_to_array(line)
                break
            except AssertionError:
                continue

        return line

    @staticmethod
    def check_length(line):
        """Each line should contain 9 characters for a standard sudoku."""
        if len(line) != 9:
            print("Please input this row again, make sure there are 9 characters:")
            raise AssertionError

    def check_uniqueness(self, line):
        """In each row, the number 1-9 should only appear at most 1 time."""
        # Count how many times 1-9 appear in the line
        occurence = np.array([line.count(str(num)) for num in range(1, 10)])
        unique = np.all(occurence < 2)
        if not unique:
            print("Repeated number detected, please re-enter the row:")
            raise AssertionError

    def convert_to_array(self, line):
        """Convert the line string into a vector of length 9."""
        line_array = []
        for char in line:
            if char in self.empty_char:
                line_array.append(0)
            else:
                line_array.append(int(char))
        return np.array(line_array)

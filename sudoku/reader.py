from collections import Counter


class UserInput:
    """Interactive method to input the sudoku board.

    Input numbers in each row without any space. If the cell is empty, input
    either "_" (underscore), "-" (dash), or "0".

    Example
    -------
    "123-5_780" is a valid input, where the 4th, 6th, and 9th positions are
    empty.

    Notes
    -----
    * Input values should be among the allowed values (default: "123456789").
    * If there are N allowed values, each input row should have N characters,
      including the "empty" characters.
    * Each element in allowed values should only appear at most 1 time in each
      input row.
    """

    empty_char = [
        "_",
        "-",
        "0",
    ]  # These characters indicate that the cell is empty

    def __init__(self, allowed_values="123456789"):
        self.allowed_values = allowed_values
        self._nallowed = len(allowed_values)
        print("Input each row of the board below:")
        self.board = []
        for ii in range(self._nallowed):
            self.board.append(self.request_line())

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
                # Check if all characters are valid
                self.check_validity(line)
                # For each line, there should be self._nallowed  elements
                self.check_length(line)
                # Each element should only appear at most 1 time
                self.check_uniqueness(line)

                # End of check, convert the line string into list
                line = self.convert_to_list(line)
                break
            except AssertionError:
                continue

        return line

    def check_validity(self, line):
        """Check if all characters in the line are valid (either allowed values
        or empty).
        """
        for char in line:
            if char not in self.allowed_values and char not in self.empty_char:
                print(
                    f"Invalid character '{char}' detected. "
                    "Please use allowed values or empty characters."
                )
                raise AssertionError

    def check_length(self, line):
        """Each line should contain 9 characters for a standard sudoku."""
        if len(line) != self._nallowed:
            print(
                "Please input this row again, "
                f"make sure there are {self._nallowed} characters:"
            )
            raise AssertionError

    def check_uniqueness(self, line):
        """In each row, the element should only appear at most 1 time."""
        # Count how many times 1-9 appear in the line
        counter = Counter(line)
        for key, count in counter.items():
            if key in self.empty_char:
                continue
            if count > 1:
                print("Repeated number detected, please re-enter the row:")
                raise AssertionError

    def convert_to_list(self, line):
        """Convert the line string into a list."""
        line_array = []
        for char in line:
            if char in self.empty_char:
                line_array.append(0)
            else:
                line_array.append(char)
        return line_array

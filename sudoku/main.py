import argparse

from .reader import UserInput
from .board import Board


def main(argv=None):
    arg_parser = argparse.ArgumentParser(description="Sudoku solver command line tool")
    arg_parser.add_argument(
        "-s",
        "--show-init",
        dest="show_init",
        default=False,
        help="Show initial, unsolved  board",
    )
    args = arg_parser.parse_args(argv)

    board_input = UserInput()
    board = Board(board_input.board)
    if args.show_init:
        board.display()

    board.solve()
    print("Solution:")
    board.display()

import argparse

from .reader import UserInput
from .board import Board


def main(argv=None):
    arg_parser = argparse.ArgumentParser(description="Sudoku solver command line tool")
    arg_parser.add_argument(
        "-s",
        "--show-init",
        dest="show_init",
        action="store_true",
        help="Show initial, unsolved  board",
    )
    arg_parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Show the steps of the solving process",
    )
    args = arg_parser.parse_args(argv)

    board_input = UserInput()
    board = Board(board_input.board)
    if args.show_init:
        print()
        print("Problem:")
        board.display()
        print()

    board.solve(verbose=args.verbose)
    print("Solution:")
    board.display()

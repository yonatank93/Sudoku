import argparse

from .reader import UserInput
from .sudoku import Sudoku
from .generate_problem import generate_problem as gen_prob


def solve(argv=None):
    arg_parser = argparse.ArgumentParser(
        description="Sudoku solver command line tool"
    )
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

    # Allowed values input
    allowed_values = input(
        "Input allowed values as a continuous string (default: '123456789'): "
    )
    if allowed_values == "":
        allowed_values = "123456789"

    # Block dimention input
    while True:
        try:
            block_dim_input = input(
                "Input block dimension as two integers separated by a space "
                "(default: '3 3'): "
            )
            if block_dim_input == "":
                block_dim_input = "3 3"
            block_dim = tuple(int(x) for x in block_dim_input.split())

            # Checks
            if len(block_dim) != 2:
                raise ValueError("Block dimension should be two integers.")
            if block_dim[0] * block_dim[1] != len(allowed_values):
                raise ValueError(
                    "Product of block dimensions should equal "
                    "the number of allowed values."
                )
            break
        except ValueError as ve:
            print(f"Invalid input: {ve}")
            print("Please try again.")

    # Board input
    board_input = UserInput(allowed_values=allowed_values)
    board = Sudoku(
        board_input.board, allowed_values=allowed_values, block_dim=block_dim
    )
    if args.show_init:
        print()
        print("Problem:")
        board.display()
        print()

    board.solve(verbose=args.verbose)
    print("Solution:")
    board.display()


def generate_problem(argv=None):
    arg_parser = argparse.ArgumentParser(
        description="Sudoku problem generator tool"
    )
    arg_parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Show the steps of the solving process",
    )
    arg_parser.add_argument(
        "-s",
        "--return-solution",
        dest="return_solution",
        action="store_true",
        help="Return the solution along with the problem",
    )
    args = arg_parser.parse_args(argv)

    # Ask for input arguments
    # Allowed values input
    allowed_values = input(
        "Input allowed values as a continuous string (default: '123456789'): "
    )
    if allowed_values == "":
        allowed_values = "123456789"

    # Block dimention input
    while True:
        try:
            block_dim_input = input(
                "Input block dimension as two integers separated by a space "
                "(default: '3 3'): "
            )
            if block_dim_input == "":
                block_dim_input = "3 3"
            block_dim = tuple(int(x) for x in block_dim_input.split())

            # Checks
            if len(block_dim) != 2:
                raise ValueError("Block dimension should be two integers.")
            if block_dim[0] * block_dim[1] != len(allowed_values):
                raise ValueError(
                    "Product of block dimensions should equal "
                    "the number of allowed values."
                )
            break
        except ValueError as ve:
            print(f"Invalid input: {ve}")
            print("Please try again.")

    # Problem level input
    while True:
        try:
            level_input = input(
                "Input difficulty level as an integer from 1 (easiest) to 5 "
                "(hardest) (default: 3): "
            )
            if level_input == "":
                level_input = "3"
            level = int(level_input)

            # Checks
            if not (1 <= level <= 5):
                raise ValueError("Level should be an integer from 1 to 5.")
            break
        except ValueError as ve:
            print(f"Invalid input: {ve}")
            print("Please try again.")

    # Generate problem
    board_problem = gen_prob(
        level=level,
        allowed_values=allowed_values,
        block_dim=block_dim,
        verbose=args.verbose,
        return_solution=args.return_solution,
    )
    if args.return_solution:
        problem, solution = board_problem
    else:
        problem = board_problem

    # Instantiate Sudoku object so we can use internal method to display the
    # board nicely.
    S = Sudoku(problem, allowed_values, block_dim)
    print("\nGenerated problem:")
    S.display()

    # If requested, show solution
    if args.return_solution:
        S.board = solution
        print("\nSolution:")
        S.display()

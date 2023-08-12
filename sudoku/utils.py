import os
import sys


def _blockPrint():
    """Block output from print function."""
    sys.stdout = open(os.devnull, "w")


def _enablePrint():
    """Enable showing output of pring function."""
    sys.stdout = sys.__stdout__

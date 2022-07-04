#!/usr/bin/env python
import setuptools
import re

# List of dependecy packages
with open("requirements.txt") as f:
    install_requires = [line.strip() for line in f.readlines()]

# Find packages
packages = setuptools.find_packages()

# Description of the package
with open("README.md") as f:
    lines = f.readlines()
description = lines[1].strip()
long_description = "".join(lines)

# Get the current version number
with open("sudoku/__init__.py") as fd:
    version = re.search('__version__ = "(.*)"', fd.read()).group(1)


setuptools.setup(
    name="sudoku",
    version=version,
    author="Yonatan Kurniawan",
    author_email="kurniawanyo@outlook.com",
    url="https://github.com/yonatank93/Sudoku",
    description=description,
    long_description=long_description,
    install_requires=install_requires,
    packages=packages,
    classifiers=["Programming Language :: Python :: 3"],
    include_package_data=True,
    python_requires=">=3.6",
)

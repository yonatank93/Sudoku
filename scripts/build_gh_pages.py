#!/usr/bin/env python3
"""Build a self-contained static site for GitHub Pages (Pyodide mode)."""

import argparse
import json
import shutil
import zipfile
from pathlib import Path

import jinja2

REPO_ROOT = Path(__file__).resolve().parent.parent
WEB_APP_DIR = REPO_ROOT / "sudoku" / "web_app"
TEMPLATE_DIR = WEB_APP_DIR / "templates"
STATIC_DIR = WEB_APP_DIR / "static"

STATIC_FILES = ("style.css", "app.js", "pyodide_worker.js")

PACKAGE_FILES = (
    "sudoku/__init__.py",
    "sudoku/cell.py",
    "sudoku/groups.py",
    "sudoku/sudoku.py",
    "sudoku/generate_problem.py",
    "sudoku/web_app/__init__.py",
    "sudoku/web_app/engine.py",
)


def build_site(out_dir: Path) -> Path:
    """Generate the static GitHub Pages bundle inside out_dir."""
    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Render index.html from the shared Jinja2 template using relative asset URLs
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)))
    env.globals["url_for"] = (
        lambda endpoint, filename="": f"./{filename}" if endpoint == "static" else "./"
    )
    env.filters["tojson"] = json.dumps
    template = env.get_template("sudoku.html")

    empty = [[0 for _ in range(9)] for _ in range(9)]
    rendered = template.render(
        solution=empty,
        original_puzzle=empty,
        is_solved=False,
        error_message="",
        app_mode="pyodide",
    )
    (out_dir / "index.html").write_text(rendered, encoding="utf-8")
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")

    # Copy static assets
    for fname in STATIC_FILES:
        shutil.copy2(STATIC_DIR / fname, out_dir / fname)

    # Bundle pure-Python sudoku package (no Flask dependency) for Pyodide
    zip_path = out_dir / "sudoku_pkg.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel_path in PACKAGE_FILES:
            src = REPO_ROOT / rel_path
            if not src.is_file():
                raise FileNotFoundError(f"Expected package file not found: {src}")
            zf.write(src, arcname=rel_path)

    return out_dir


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Build static GitHub Pages bundle for Sudoku web app."
    )
    parser.add_argument(
        "--out-dir",
        default=str(REPO_ROOT / "site"),
        help="Output directory for the static site (default: ./site)",
    )
    args = parser.parse_args(argv)
    out = build_site(Path(args.out_dir))
    print(f"Built static Sudoku site in {out}")


if __name__ == "__main__":
    main()

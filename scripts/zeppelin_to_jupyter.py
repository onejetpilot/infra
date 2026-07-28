#!/usr/bin/env python3
"""Convert a Zeppelin .zpln note to a viewable Jupyter .ipynb notebook."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def source_lines(text: str) -> list[str]:
    return text.splitlines(keepends=True) or [""]


def convert_cell(text: str) -> dict:
    stripped = text.lstrip()
    if stripped.startswith("%md"):
        content = stripped[3:].lstrip("\r\n")
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": source_lines(content),
        }

    if stripped.startswith("%gp"):
        content = stripped[3:].lstrip("\r\n")
    else:
        content = text

    # Raw cells preserve Greenplum/Cloudberry SQL without incorrectly sending
    # it to the Python kernel. They can later be converted to %%sql cells when
    # a SQL Jupyter extension is deliberately configured.
    return {
        "cell_type": "raw",
        "metadata": {"format": "text/x-sql"},
        "source": source_lines(content),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    note = json.loads(args.source.read_text(encoding="utf-8-sig"))
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "> Конвертировано из Zeppelin. SQL-ячейки сохранены как Raw, "
                "поскольку интерпретатор `%gp` не является частью Jupyter.\n"
            ],
        }
    ]
    cells.extend(
        convert_cell(paragraph.get("text", ""))
        for paragraph in note.get("paragraphs", [])
        if paragraph.get("text", "").strip()
    )

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3"},
            "zeppelin_source": args.source.name,
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    args.destination.write_text(
        json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"{len(cells)} cells -> {args.destination}")


if __name__ == "__main__":
    main()

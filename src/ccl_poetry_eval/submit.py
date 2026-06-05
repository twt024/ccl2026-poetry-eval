from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .io_utils import read_json_or_jsonl, write_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge task outputs into one submission JSON.")
    parser.add_argument("--task1")
    parser.add_argument("--task2")
    parser.add_argument("--task3")
    parser.add_argument("--task4")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    submission: dict[str, Any] = {}
    for task in ("task1", "task2", "task3", "task4"):
        path = getattr(args, task)
        if not path:
            continue
        submission[task] = read_json_or_jsonl(Path(path))
    write_json(args.output, submission)


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

Record = dict[str, Any]


def ensure_parent(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def load_json_records(path: str | Path) -> list[Record]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(source)

    if source.suffix.lower() in {".jsonl", ".jl"}:
        records: list[Record] = []
        with source.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                line = line.strip()
                if not line:
                    continue
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError(f"{source}:{line_no} is not a JSON object")
                records.append(value)
        return records

    value = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return _coerce_records(value)

    if isinstance(value, dict):
        for key in ("data", "records", "items", "examples", "train", "dev", "test"):
            nested = value.get(key)
            if isinstance(nested, list):
                return _coerce_records(nested)

        # Some datasets are keyed by id: {"001": {...}, "002": {...}}.
        if all(isinstance(item, dict) for item in value.values()):
            records = []
            for key, item in value.items():
                record = dict(item)
                record.setdefault("id", key)
                records.append(record)
            return records

        return [value]

    raise ValueError(f"Unsupported JSON root type in {source}: {type(value).__name__}")


def _coerce_records(values: list[Any]) -> list[Record]:
    records: list[Record] = []
    for index, value in enumerate(values):
        if isinstance(value, dict):
            records.append(value)
        else:
            records.append({"id": index, "value": value})
    return records


def write_json(path: str | Path, value: Any) -> None:
    target = ensure_parent(path)
    target.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: str | Path, records: list[Record]) -> None:
    target = ensure_parent(path)
    with target.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_json_or_jsonl(path: str | Path) -> Any:
    source = Path(path)
    if source.suffix.lower() in {".jsonl", ".jl"}:
        return load_json_records(source)
    return json.loads(source.read_text(encoding="utf-8"))


def find_submission_template(start: str | Path = ".") -> Path:
    root = Path(start).resolve()
    candidates: list[Path] = []
    for directory in [root, *root.parents]:
        candidates.extend(directory.glob("*.json"))

    for candidate in candidates:
        try:
            value = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict):
            continue
        if all(isinstance(value.get(task), list) for task in ("task1", "task2", "task3", "task4")):
            return candidate

    raise FileNotFoundError(
        "Could not find official submission template JSON. "
        "Place the downloaded sample JSON in the project root or pass --template explicitly."
    )

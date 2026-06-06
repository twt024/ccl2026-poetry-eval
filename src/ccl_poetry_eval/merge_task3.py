from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .io_utils import find_submission_template, read_json_or_jsonl, write_json

ID_KEYS = ("idx", "id", "qid", "question_id", "sample_id", "poem_id")
SPLIT_RE = re.compile(r"[\uff0c,\uff1b;\n\u3001|]+")
BAD_ANSWERS = {
    "",
    "unknown",
    "null",
    "none",
    "\u4e0d\u77e5\u9053",
    "\u4e0d\u786e\u5b9a",
    "\u65e0\u6cd5\u786e\u5b9a",
    "\u65e0\u6cd5\u5224\u65ad",
}
WRAPPER_CHARS = "[]\"'`" + "\u201c\u201d\u2018\u2019"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge multiple task3 outputs by slot-level voting.")
    parser.add_argument("--inputs", nargs="+", required=True, help="Task3 JSON files to merge.")
    parser.add_argument("--output", required=True, help="Merged task3 JSON output.")
    parser.add_argument("--template", default="auto", help="Official submission sample JSON, or auto.")
    parser.add_argument("--report", help="Optional JSON report path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    template_records = load_task3_template(args.template)
    candidate_sets = [load_task3_records(path) for path in args.inputs]
    merged, report = merge_task3(candidate_sets, template_records, args.inputs)
    write_json(args.output, merged)
    if args.report:
        write_json(args.report, report)


def load_task3_template(template: str) -> list[dict[str, Any]]:
    path = find_submission_template(".") if template.lower() == "auto" else Path(template)
    data = read_json_or_jsonl(path)
    if not isinstance(data, dict) or not isinstance(data.get("task3"), list):
        raise ValueError(f"Template does not contain task3 list: {path}")
    return data["task3"]


def load_task3_records(path: str | Path) -> list[dict[str, Any]]:
    data = read_json_or_jsonl(path)
    if not isinstance(data, list):
        raise ValueError(f"Task3 input must be a JSON list: {path}")
    return data


def merge_task3(
    candidate_sets: list[list[dict[str, Any]]],
    template_records: list[dict[str, Any]],
    input_names: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    stats = Counter()
    per_input_nonempty = defaultdict(int)

    for index, template in enumerate(template_records):
        expected_count = expected_answer_count(template)
        candidates = [
            normalize_answer_list(get_record_answer(records, index), expected_count)
            for records in candidate_sets
        ]

        answer: list[str] = []
        for slot in range(expected_count):
            choice = choose_slot_answer(candidates, slot)
            answer.append(choice)
            if choice:
                stats["filled_slots"] += 1
            else:
                stats["empty_slots"] += 1

        full_votes = Counter(tuple(items) for items in candidates if all(items))
        if full_votes and full_votes.most_common(1)[0][1] > 1:
            stats["full_answer_majority_rows"] += 1

        for input_index, items in enumerate(candidates):
            if any(items):
                per_input_nonempty[input_names[input_index]] += 1

        result = copy_identifiers(template, index)
        result["answer"] = answer
        merged.append(result)

    report = {
        "rows": len(merged),
        "inputs": input_names,
        "stats": dict(stats),
        "nonempty_rows_by_input": dict(per_input_nonempty),
    }
    return merged, report


def get_record_answer(records: list[dict[str, Any]], index: int) -> Any:
    if index >= len(records):
        return []
    record = records[index]
    if not isinstance(record, dict):
        return []
    return record.get("answer", [])


def expected_answer_count(template: dict[str, Any]) -> int:
    answer = template.get("answer")
    if isinstance(answer, list) and answer:
        return len(answer)
    return 1


def normalize_answer_list(value: Any, expected_count: int) -> list[str]:
    raw_items = value if isinstance(value, list) else [value]
    items = [clean_text(item) for item in raw_items]
    items = [item for item in items if is_good_answer(item)]

    expanded: list[str] = []
    for item in items:
        if len(items) < expected_count:
            parts = [clean_text(part) for part in SPLIT_RE.split(item)]
            parts = [part for part in parts if is_good_answer(part)]
            expanded.extend(parts if len(parts) > 1 else [item])
        else:
            expanded.append(item)

    return expanded[:expected_count] + [""] * max(0, expected_count - len(expanded))


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False)
    value = re.sub(r"\s+", "", value)
    value = re.sub(r"^(?:answer|\u7b54\u6848|\u8f93\u51fa)[:\uff1a]?", "", value, flags=re.IGNORECASE)
    value = value.strip()
    value = value.strip(WRAPPER_CHARS)
    value = value.strip("\u3002\uff0c\uff1b\uff1a\uff01\uff1f,.!?;:")
    return value


def is_good_answer(text: str) -> bool:
    return clean_for_vote(text).lower() not in BAD_ANSWERS


def clean_for_vote(text: str) -> str:
    return re.sub(r"[\s\u3002\uff0c\uff1b\uff1a\uff01\uff1f,.!?;:]", "", text)


def choose_slot_answer(candidates: list[list[str]], slot: int) -> str:
    originals: dict[str, str] = {}
    votes: Counter[str] = Counter()

    for items in candidates:
        if slot >= len(items):
            continue
        answer = clean_text(items[slot])
        if not is_good_answer(answer):
            continue
        key = clean_for_vote(answer)
        votes[key] += 1
        originals.setdefault(key, answer)

    if not votes:
        return ""

    best_count = votes.most_common(1)[0][1]
    tied = {key for key, count in votes.items() if count == best_count}

    # Resolve ties by input order: earlier candidate files are treated as higher priority.
    for items in candidates:
        if slot >= len(items):
            continue
        key = clean_for_vote(clean_text(items[slot]))
        if key in tied:
            return originals[key]
    return originals[votes.most_common(1)[0][0]]


def copy_identifiers(template: dict[str, Any], index: int) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in ID_KEYS:
        if key in template:
            result[key] = template[key]
    if not result:
        result["idx"] = index
    return result


if __name__ == "__main__":
    main()

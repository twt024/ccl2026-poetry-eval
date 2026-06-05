from __future__ import annotations

import argparse
from typing import Any

from .io_utils import find_submission_template, read_json_or_jsonl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate submission schema against sample JSON.")
    parser.add_argument("--submission", required=True)
    parser.add_argument("--template", default="auto")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    submission = read_json_or_jsonl(args.submission)
    template_path = find_submission_template(".") if args.template.lower() == "auto" else args.template
    template = read_json_or_jsonl(template_path)
    errors = validate_submission(submission, template)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("submission schema ok")


def validate_submission(submission: Any, template: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(submission, dict):
        return ["submission root must be a JSON object"]
    if not isinstance(template, dict):
        return ["template root must be a JSON object"]

    for task in ("task1", "task2", "task3", "task4"):
        task_items = submission.get(task)
        template_items = template.get(task)
        if not isinstance(task_items, list):
            errors.append(f"{task} must be a list")
            continue
        if not isinstance(template_items, list):
            continue
        if len(task_items) != len(template_items):
            errors.append(f"{task} length mismatch: got {len(task_items)}, expected {len(template_items)}")
            continue
        for index, (item, expected) in enumerate(zip(task_items, template_items)):
            errors.extend(validate_item(task, index, item, expected))
    return errors


def validate_item(task: str, index: int, item: Any, expected: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(item, dict):
        return [f"{task}[{index}] must be an object"]
    if not isinstance(expected, dict):
        return errors

    if item.get("idx") != expected.get("idx"):
        errors.append(f"{task}[{index}].idx mismatch: got {item.get('idx')}, expected {expected.get('idx')}")

    required_keys = set(expected.keys())
    missing = sorted(required_keys - set(item.keys()))
    if missing:
        errors.append(f"{task}[{index}] missing keys: {missing}")

    if task == "task1":
        errors.extend(validate_task1(index, item, expected))
    elif task == "task2":
        if item.get("flag") not in {0, 1, "0", "1"}:
            errors.append(f"task2[{index}].flag must be 0 or 1")
    elif task == "task3":
        if not isinstance(item.get("answer"), list):
            errors.append(f"task3[{index}].answer must be a list")
    elif task == "task4":
        if item.get("answer") not in {"A", "B", "C", "D"}:
            errors.append(f"task4[{index}].answer must be A/B/C/D")
    return errors


def validate_task1(index: int, item: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("ans_qa_words", "ans_qa_sents"):
        value = item.get(field)
        target = expected.get(field)
        if not isinstance(value, dict):
            errors.append(f"task1[{index}].{field} must be an object")
            continue
        if isinstance(target, dict) and set(value.keys()) != set(target.keys()):
            errors.append(f"task1[{index}].{field} keys mismatch")
    if item.get("choose_id") not in {"A", "B", "C", "D"}:
        errors.append(f"task1[{index}].choose_id must be A/B/C/D")
    return errors


if __name__ == "__main__":
    main()

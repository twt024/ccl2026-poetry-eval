from __future__ import annotations

import argparse
import json
import re
from typing import Any

from .io_utils import find_submission_template, load_json_records, read_json_or_jsonl, write_json

ID_KEYS = ("idx", "id", "qid", "question_id", "sample_id", "poem_id")
CHOICE_RE = re.compile(r"(?<![A-Z])([ABCD])(?![A-Z])", re.IGNORECASE)
BLANK_RE = re.compile(r"_{2,}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert raw model output into task answers.")
    parser.add_argument("--task", required=True, choices=["task1", "task2", "task3", "task4"])
    parser.add_argument("--input", required=True, help="Raw JSONL produced by infer.py.")
    parser.add_argument("--output", required=True, help="Postprocessed JSON file.")
    parser.add_argument(
        "--template",
        default="auto",
        help="Official submission sample JSON for schema keys. Use 'auto' to discover it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_records = load_json_records(args.input)
    template_path = resolve_template_path(args.template)
    templates = load_task_templates(template_path, args.task) if template_path else {}
    answers = [
        postprocess_record(args.task, record, templates.get(template_key(record)))
        for record in raw_records
    ]
    write_json(args.output, answers)


def postprocess_record(
    task: str,
    raw_record: dict[str, Any],
    template_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = raw_record.get("input")
    if not isinstance(source, dict):
        source = {}
    parsed = extract_json(raw_record.get("raw_output", ""))
    if not isinstance(parsed, dict):
        parsed = {}

    result = copy_identifiers(source, raw_record, template_record)
    if task == "task1":
        expected_words = template_keys(template_record, "ans_qa_words") or source.get("qa_words", [])
        expected_sents = template_keys(template_record, "ans_qa_sents") or source.get("qa_sents", [])
        result["ans_qa_words"] = normalize_answer_map(
            parsed.get("ans_qa_words", parsed.get("qa_words", {})),
            expected_words,
        )
        result["ans_qa_sents"] = normalize_answer_map(
            parsed.get("ans_qa_sents", parsed.get("qa_sents", {})),
            expected_sents,
        )
        result["choose_id"] = normalize_choice(
            parsed.get("choose_id", parsed.get("answer", "")),
            raw_record.get("raw_output", ""),
        )
        return result

    if task == "task2":
        flag = normalize_flag(parsed.get("flag"))
        result["flag"] = flag
        result["answer"] = normalize_text(parsed.get("answer", "")) if flag else ""
        return result

    answer = parsed.get("answer", parsed.get("output", parsed.get("result", "")))
    if task == "task4":
        answer = normalize_choice(answer, raw_record.get("raw_output", ""))
    elif task == "task3":
        if answer == "":
            answer = raw_record.get("raw_output", "")
        answer = normalize_fill_answer(
            answer,
            expected_count=expected_answer_count(source, template_record),
        )
    else:
        answer = normalize_text(answer)
    result["answer"] = answer
    return result


def extract_json(text: Any) -> Any:
    if not isinstance(text, str):
        return None
    cleaned = strip_code_fence(text.strip())
    for candidate in json_candidates(cleaned):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def strip_code_fence(text: str) -> str:
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def json_candidates(text: str) -> list[str]:
    candidates = [text]
    for left, right in (("{", "}"), ("[", "]")):
        start = text.find(left)
        end = text.rfind(right)
        if start != -1 and end != -1 and start < end:
            candidates.append(text[start : end + 1])
    return candidates


def normalize_flag(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return 1 if value else 0
    text = normalize_text(value).lower()
    positive_tokens = ("\u6709", "\u662f", "\u5305\u542b")
    negative_tokens = ("\u65e0", "\u5426", "\u4e0d\u542b")
    if text in {"1", "true", "yes", "y"} or any(token in text for token in positive_tokens):
        return 1
    if text in {"0", "false", "no", "n"} or any(token in text for token in negative_tokens):
        return 0
    return 0


def normalize_choice(value: Any, raw_text: Any = "") -> str:
    text = normalize_text(value)
    match = CHOICE_RE.search(text)
    if match:
        return match.group(1).upper()
    match = CHOICE_RE.search(normalize_text(raw_text))
    if match:
        return match.group(1).upper()
    return text[:1].upper() if text else ""


def normalize_answer_map(value: Any, expected_keys: Any) -> dict[str, str]:
    keys = [str(item) for item in expected_keys] if isinstance(expected_keys, list) else []
    if isinstance(value, dict):
        normalized = {normalize_text(key): normalize_text(item) for key, item in value.items()}
        if keys:
            return {key: normalized.get(key, "") for key in keys}
        return normalized

    if isinstance(value, list):
        items = [normalize_text(item) for item in value]
        if keys:
            return {key: items[index] if index < len(items) else "" for index, key in enumerate(keys)}

    if keys:
        return {key: "" for key in keys}
    return {}


def normalize_fill_answer(value: Any, expected_count: int = 1) -> list[str]:
    raw_items = value if isinstance(value, list) else [value]
    items = [strip_answer_noise(normalize_text(item)) for item in raw_items]
    items = [item for item in items if item]

    parts: list[str] = []
    for item in items:
        if len(items) < expected_count:
            split_items = [
                strip_answer_noise(part)
                for part in re.split(r"[\uff0c,\uff1b;\n\u3001|]+", item)
                if strip_answer_noise(part)
            ]
            parts.extend(split_items if len(split_items) > 1 else [item])
        else:
            parts.append(item)

    if not parts:
        parts = []
    return parts[:expected_count] + [""] * max(0, expected_count - len(parts))


def strip_answer_noise(text: str) -> str:
    text = re.sub(r"^answer\s*[:：]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^[\[\]\"'“”‘’\s]+|[\[\]\"'“”‘’\s]+$", "", text)
    return text.strip()


def expected_answer_count(source: dict[str, Any], template_record: dict[str, Any] | None) -> int:
    if isinstance(template_record, dict) and isinstance(template_record.get("answer"), list):
        return max(1, len(template_record["answer"]))
    return expected_fill_count(source)


def expected_fill_count(source: dict[str, Any]) -> int:
    question = normalize_text(source.get("que", source.get("question", "")))
    return max(1, len(BLANK_RE.findall(question)))


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+", " ", json.dumps(value, ensure_ascii=False)).strip()


def template_key(raw_record: dict[str, Any]) -> str:
    source = raw_record.get("input")
    if isinstance(source, dict):
        for key in ID_KEYS:
            if source.get(key) is not None:
                return str(source[key])
    for key in ("id", "source_index"):
        if raw_record.get(key) is not None:
            return str(raw_record[key])
    return ""


def resolve_template_path(template: str | None) -> str | None:
    if not template:
        return None
    if template.lower() == "auto":
        return str(find_submission_template("."))
    return template


def load_task_templates(path: str, task: str) -> dict[str, dict[str, Any]]:
    data = read_json_or_jsonl(path)
    if isinstance(data, dict) and isinstance(data.get(task), list):
        records = data[task]
    elif isinstance(data, list):
        records = data
    else:
        return {}

    templates: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            continue
        key = None
        for id_key in ID_KEYS:
            if record.get(id_key) is not None:
                key = str(record[id_key])
                break
        templates[key or str(index)] = record
    return templates


def template_keys(template_record: dict[str, Any] | None, field: str) -> list[str]:
    if not isinstance(template_record, dict):
        return []
    value = template_record.get(field)
    if not isinstance(value, dict):
        return []
    return [str(key) for key in value.keys()]


def copy_identifiers(
    source: dict[str, Any],
    raw_record: dict[str, Any],
    template_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if isinstance(template_record, dict):
        for key in ID_KEYS:
            if key in template_record:
                result[key] = template_record[key]
        if result:
            return result

    for key in ID_KEYS:
        if key in source:
            result[key] = source[key]
    if not result:
        result["id"] = raw_record.get("id", raw_record.get("source_index", 0))
    return result


if __name__ == "__main__":
    main()

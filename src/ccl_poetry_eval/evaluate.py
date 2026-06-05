from __future__ import annotations

import argparse
from typing import Any

from .io_utils import load_json_records

ID_KEYS = ("idx", "id", "qid", "question_id", "sample_id", "poem_id")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Lightweight local evaluation helper.")
    parser.add_argument("--task", required=True, choices=["task1", "task2", "task3", "task4"])
    parser.add_argument("--gold", required=True)
    parser.add_argument("--pred", required=True)
    parser.add_argument("--answer-field", default="answer")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    gold_records = load_json_records(args.gold)
    pred_records = load_json_records(args.pred)
    pairs = align_records(gold_records, pred_records)
    print(f"matched={len(pairs)} gold={len(gold_records)} pred={len(pred_records)}")

    if args.task == "task2":
        flag_acc = accuracy(
            [normalize_flag(gold.get("flag")) for gold, _ in pairs],
            [normalize_flag(pred.get("flag")) for _, pred in pairs],
        )
        print(f"flag_accuracy={flag_acc:.4f}")

    gold_answers = [normalize_answer(gold.get(args.answer_field)) for gold, _ in pairs]
    pred_answers = [normalize_answer(pred.get(args.answer_field)) for _, pred in pairs]
    exact = accuracy(gold_answers, pred_answers)
    print(f"exact_match={exact:.4f}")

    bleu = corpus_bleu(pred_answers, gold_answers)
    if bleu is not None:
        print(f"bleu={bleu:.4f}")


def align_records(
    gold_records: list[dict[str, Any]],
    pred_records: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    pred_by_id = {record_id(record, index): record for index, record in enumerate(pred_records)}
    pairs = []
    for index, gold in enumerate(gold_records):
        key = record_id(gold, index)
        pred = pred_by_id.get(key)
        if pred is not None:
            pairs.append((gold, pred))
    return pairs


def record_id(record: dict[str, Any], index: int) -> str:
    for key in ID_KEYS:
        value = record.get(key)
        if value is not None:
            return str(value)
    return str(index)


def accuracy(gold: list[Any], pred: list[Any]) -> float:
    if not gold:
        return 0.0
    return sum(1 for expected, actual in zip(gold, pred) if expected == actual) / len(gold)


def normalize_answer(value: Any) -> str:
    if isinstance(value, list):
        return "|".join(normalize_answer(item) for item in value)
    return "" if value is None else str(value).strip()


def normalize_flag(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return 1 if int(value) else 0
    except (TypeError, ValueError):
        text = normalize_answer(value)
        return 1 if text in {"是", "有", "包含", "true", "True"} else 0


def corpus_bleu(pred_answers: list[str], gold_answers: list[str]) -> float | None:
    try:
        import sacrebleu
    except ImportError:
        return None
    if not pred_answers:
        return 0.0
    return float(sacrebleu.corpus_bleu(pred_answers, [gold_answers]).score)


if __name__ == "__main__":
    main()

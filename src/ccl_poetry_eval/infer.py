from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):  # type: ignore[no-redef]
        return iterable

from .io_utils import ensure_parent, load_json_records
from .model_clients import build_client
from .prompting import load_prompt_template, render_prompt

ID_KEYS = ("idx", "id", "qid", "question_id", "sample_id", "poem_id")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run batch inference for one task.")
    parser.add_argument("--task", required=True, choices=["task1", "task2", "task3", "task4"])
    parser.add_argument("--input", required=True, help="Input JSON/JSONL file.")
    parser.add_argument("--output", required=True, help="Raw JSONL output file.")
    parser.add_argument("--prompt", help="Prompt template path. Defaults to prompts/{task}.txt.")
    parser.add_argument("--backend", default="dummy", choices=["dummy", "hf", "local_api"])
    parser.add_argument("--model", default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--base-url", help="OpenAI-compatible local API base URL.")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--resume", action="store_true", help="Skip records already in output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_json_records(args.input)
    template = load_prompt_template(args.task, args.prompt)
    client = build_client(
        backend=args.backend,
        model=args.model,
        task=args.task,
        temperature=args.temperature,
        max_new_tokens=args.max_new_tokens,
        base_url=args.base_url,
    )

    output_path = ensure_parent(args.output)
    done_keys = _load_done_keys(output_path) if args.resume else set()
    mode = "a" if args.resume and output_path.exists() else "w"

    with output_path.open(mode, encoding="utf-8") as handle:
        for index, sample in enumerate(tqdm(records, desc=args.task)):
            sample_key = _sample_key(sample, index)
            if sample_key in done_keys:
                continue
            prompt = render_prompt(template, sample, args.task)
            raw_output = client.generate(prompt)
            result: dict[str, Any] = {
                "task": args.task,
                "source_index": index,
                "id": sample_key,
                "input": sample,
                "raw_output": raw_output,
                "model": args.model,
            }
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            handle.flush()


def _sample_key(sample: dict[str, Any], index: int) -> str:
    for key in ID_KEYS:
        value = sample.get(key)
        if value is not None:
            return str(value)
    return str(index)


def _load_done_keys(path: Path) -> set[str]:
    if not path.exists():
        return set()
    keys: set[str] = set()
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            keys.add(str(record.get("id", record.get("source_index", ""))))
    return keys


if __name__ == "__main__":
    main()

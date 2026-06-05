from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_prompt_template(task: str, prompt_path: str | Path | None = None) -> str:
    path = Path(prompt_path) if prompt_path else Path("prompts") / f"{task}.txt"
    if not path.exists():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def render_prompt(template: str, sample: dict[str, Any], task: str) -> str:
    sample_json = json.dumps(sample, ensure_ascii=False, indent=2)
    return template.replace("{task}", task).replace("{sample_json}", sample_json)

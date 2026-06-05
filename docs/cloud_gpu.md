# Cloud GPU runbook

Target model: `Qwen/Qwen2.5-7B-Instruct`.

## Recommended GPU

Use one 24 GB GPU if possible:

- RTX 4090 24 GB
- RTX 3090 24 GB
- A10 24 GB
- L20 or stronger

The dataset is small, so one GPU is enough for baseline inference. Avoid CPU-only servers for the real run.

## Upload files

Upload the whole project directory, including:

```text
CCPA2026-test_data/
CCPA2026-train_data/
prompts/
src/
scripts/
pyproject.toml
提交示例.json
```

Do not upload only `src/`; the runner needs the official data and submission template.

## Setup

On Ubuntu GPU server:

```bash
cd ccl2026-poetry-eval
bash scripts/setup_autodl.sh
```

If you prefer an isolated virtual environment, use:

```bash
bash scripts/setup_cloud_ubuntu.sh
source .venv/bin/activate
```

## Run Qwen2.5-7B-Instruct

```bash
bash scripts/run_hf_qwen25_7b.sh
```

Final output:

```text
outputs/submissions/submission_qwen2.5-7b-instruct.json
```

The script uses `--resume`, so interrupted runs can continue from the existing JSONL files.

## Download result

Download this file back to your local machine:

```text
outputs/submissions/submission_qwen2.5-7b-instruct.json
```

Then submit it on the competition platform after a final local schema check.

#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

for TASK in task1 task2 task3 task4; do
  python -m ccl_poetry_eval.infer \
    --task "${TASK}" \
    --input "CCPA2026-test_data/${TASK}.json" \
    --output "outputs/raw/${TASK}_dummy.jsonl" \
    --prompt "prompts/${TASK}.txt" \
    --backend dummy \
    --model dummy

  python -m ccl_poetry_eval.postprocess \
    --task "${TASK}" \
    --input "outputs/raw/${TASK}_dummy.jsonl" \
    --output "outputs/submissions/${TASK}_dummy.json" \
    --template auto
done

python -m ccl_poetry_eval.submit \
  --task1 "outputs/submissions/task1_dummy.json" \
  --task2 "outputs/submissions/task2_dummy.json" \
  --task3 "outputs/submissions/task3_dummy.json" \
  --task4 "outputs/submissions/task4_dummy.json" \
  --output "outputs/submissions/submission_dummy.json"

python -m ccl_poetry_eval.validate_submission \
  --submission "outputs/submissions/submission_dummy.json" \
  --template auto

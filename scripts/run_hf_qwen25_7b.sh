#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
RUN_NAME="${RUN_NAME:-qwen2.5-7b-instruct}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-768}"

source scripts/submission_name.sh
SUBMISSION_FILE="${SUBMISSION_FILE:-$(submission_output_path "${RUN_NAME}")}"

for TASK in task1 task2 task3 task4; do
  python -m ccl_poetry_eval.infer \
    --task "${TASK}" \
    --input "CCPA2026-test_data/${TASK}.json" \
    --output "outputs/raw/${TASK}_${RUN_NAME}.jsonl" \
    --prompt "prompts/${TASK}.txt" \
    --backend hf \
    --model "${MODEL}" \
    --temperature 0 \
    --max-new-tokens "${MAX_NEW_TOKENS}" \
    --resume

  python -m ccl_poetry_eval.postprocess \
    --task "${TASK}" \
    --input "outputs/raw/${TASK}_${RUN_NAME}.jsonl" \
    --output "outputs/submissions/${TASK}_${RUN_NAME}.json" \
    --template auto
done

python -m ccl_poetry_eval.submit \
  --task1 "outputs/submissions/task1_${RUN_NAME}.json" \
  --task2 "outputs/submissions/task2_${RUN_NAME}.json" \
  --task3 "outputs/submissions/task3_${RUN_NAME}.json" \
  --task4 "outputs/submissions/task4_${RUN_NAME}.json" \
  --output "${SUBMISSION_FILE}"

python -m ccl_poetry_eval.validate_submission \
  --submission "${SUBMISSION_FILE}" \
  --template auto

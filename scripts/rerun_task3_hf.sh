#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
BASE_RUN_NAME="${BASE_RUN_NAME:-qwen2.5-7b-instruct}"
TASK3_RUN_NAME="${TASK3_RUN_NAME:-qwen2.5-7b-instruct-task3-v2}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-256}"

source scripts/submission_name.sh
SUBMISSION_FILE="${SUBMISSION_FILE:-$(submission_output_path "${BASE_RUN_NAME}")}"

python -m ccl_poetry_eval.infer \
  --task task3 \
  --input "CCPA2026-test_data/task3.json" \
  --output "outputs/raw/task3_${TASK3_RUN_NAME}.jsonl" \
  --prompt "prompts/task3.txt" \
  --backend hf \
  --model "${MODEL}" \
  --temperature 0 \
  --max-new-tokens "${MAX_NEW_TOKENS}" \
  --resume

python -m ccl_poetry_eval.postprocess \
  --task task3 \
  --input "outputs/raw/task3_${TASK3_RUN_NAME}.jsonl" \
  --output "outputs/submissions/task3_${TASK3_RUN_NAME}.json" \
  --template auto

python -m ccl_poetry_eval.submit \
  --task1 "outputs/submissions/task1_${BASE_RUN_NAME}.json" \
  --task2 "outputs/submissions/task2_${BASE_RUN_NAME}.json" \
  --task3 "outputs/submissions/task3_${TASK3_RUN_NAME}.json" \
  --task4 "outputs/submissions/task4_${BASE_RUN_NAME}.json" \
  --output "${SUBMISSION_FILE}"

python -m ccl_poetry_eval.validate_submission \
  --submission "${SUBMISSION_FILE}" \
  --template auto

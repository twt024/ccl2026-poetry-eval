#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
BASE_RUN_NAME="${BASE_RUN_NAME:-qwen2.5-7b-instruct}"
TASK4_RUN_NAME="${TASK4_RUN_NAME:-qwen2.5-7b-instruct-task4-v4}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-256}"

TASK1_FILE="${TASK1_FILE:-outputs/submissions/task1_${BASE_RUN_NAME}.json}"
TASK3_FILE="${TASK3_FILE:-outputs/submissions/task3_${BASE_RUN_NAME}.json}"

python -m ccl_poetry_eval.infer \
  --task task4 \
  --input "CCPA2026-test_data/task4.json" \
  --output "outputs/raw/task4_${TASK4_RUN_NAME}.jsonl" \
  --prompt "prompts/task4_v4.txt" \
  --backend hf \
  --model "${MODEL}" \
  --temperature 0 \
  --max-new-tokens "${MAX_NEW_TOKENS}" \
  --resume

python -m ccl_poetry_eval.postprocess \
  --task task4 \
  --input "outputs/raw/task4_${TASK4_RUN_NAME}.jsonl" \
  --output "outputs/submissions/task4_${TASK4_RUN_NAME}.json" \
  --template auto

python -m ccl_poetry_eval.submit \
  --task1 "${TASK1_FILE}" \
  --task2 "outputs/submissions/task2_${BASE_RUN_NAME}.json" \
  --task3 "${TASK3_FILE}" \
  --task4 "outputs/submissions/task4_${TASK4_RUN_NAME}.json" \
  --output "outputs/submissions/submission_${BASE_RUN_NAME}_task4v4.json"

python -m ccl_poetry_eval.validate_submission \
  --submission "outputs/submissions/submission_${BASE_RUN_NAME}_task4v4.json" \
  --template auto

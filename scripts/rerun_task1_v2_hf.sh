#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
BASE_RUN_NAME="${BASE_RUN_NAME:-qwen2.5-7b-instruct}"
TASK1_RUN_NAME="${TASK1_RUN_NAME:-qwen2.5-7b-instruct-task1-v2prompt}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-768}"

TASK3_FILE="${TASK3_FILE:-outputs/submissions/task3_${BASE_RUN_NAME}.json}"
TASK4_FILE="${TASK4_FILE:-outputs/submissions/task4_${BASE_RUN_NAME}.json}"
source scripts/submission_name.sh
SUBMISSION_FILE="${SUBMISSION_FILE:-$(submission_output_path "${BASE_RUN_NAME}")}"

python -m ccl_poetry_eval.infer \
  --task task1 \
  --input "CCPA2026-test_data/task1.json" \
  --output "outputs/raw/task1_${TASK1_RUN_NAME}.jsonl" \
  --prompt "prompts/task1_v2.txt" \
  --backend hf \
  --model "${MODEL}" \
  --temperature 0 \
  --max-new-tokens "${MAX_NEW_TOKENS}" \
  --resume

python -m ccl_poetry_eval.postprocess \
  --task task1 \
  --input "outputs/raw/task1_${TASK1_RUN_NAME}.jsonl" \
  --output "outputs/submissions/task1_${TASK1_RUN_NAME}.json" \
  --template auto

python -m ccl_poetry_eval.submit \
  --task1 "outputs/submissions/task1_${TASK1_RUN_NAME}.json" \
  --task2 "outputs/submissions/task2_${BASE_RUN_NAME}.json" \
  --task3 "${TASK3_FILE}" \
  --task4 "${TASK4_FILE}" \
  --output "${SUBMISSION_FILE}"

python -m ccl_poetry_eval.validate_submission \
  --submission "${SUBMISSION_FILE}" \
  --template auto

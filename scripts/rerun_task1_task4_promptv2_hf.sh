#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
BASE_RUN_NAME="${BASE_RUN_NAME:-qwen2.5-7b-instruct}"
PROMPT_RUN_NAME="${PROMPT_RUN_NAME:-qwen2.5-7b-instruct-promptv2}"
TASK1_MAX_NEW_TOKENS="${TASK1_MAX_NEW_TOKENS:-768}"
TASK4_MAX_NEW_TOKENS="${TASK4_MAX_NEW_TOKENS:-256}"

TASK2_FILE="${TASK2_FILE:-outputs/submissions/task2_${BASE_RUN_NAME}.json}"
TASK3_FILE="${TASK3_FILE:-outputs/submissions/task3_${BASE_RUN_NAME}.json}"
source scripts/submission_name.sh
SUBMISSION_FILE="${SUBMISSION_FILE:-$(submission_output_path "${BASE_RUN_NAME}")}"

python -m ccl_poetry_eval.infer \
  --task task1 \
  --input "CCPA2026-test_data/task1.json" \
  --output "outputs/raw/task1_${PROMPT_RUN_NAME}.jsonl" \
  --prompt "prompts/task1_v2.txt" \
  --backend hf \
  --model "${MODEL}" \
  --temperature 0 \
  --max-new-tokens "${TASK1_MAX_NEW_TOKENS}" \
  --resume

python -m ccl_poetry_eval.postprocess \
  --task task1 \
  --input "outputs/raw/task1_${PROMPT_RUN_NAME}.jsonl" \
  --output "outputs/submissions/task1_${PROMPT_RUN_NAME}.json" \
  --template auto

python -m ccl_poetry_eval.infer \
  --task task4 \
  --input "CCPA2026-test_data/task4.json" \
  --output "outputs/raw/task4_${PROMPT_RUN_NAME}.jsonl" \
  --prompt "prompts/task4_v4.txt" \
  --backend hf \
  --model "${MODEL}" \
  --temperature 0 \
  --max-new-tokens "${TASK4_MAX_NEW_TOKENS}" \
  --resume

python -m ccl_poetry_eval.postprocess \
  --task task4 \
  --input "outputs/raw/task4_${PROMPT_RUN_NAME}.jsonl" \
  --output "outputs/submissions/task4_${PROMPT_RUN_NAME}.json" \
  --template auto

python -m ccl_poetry_eval.submit \
  --task1 "outputs/submissions/task1_${PROMPT_RUN_NAME}.json" \
  --task2 "${TASK2_FILE}" \
  --task3 "${TASK3_FILE}" \
  --task4 "outputs/submissions/task4_${PROMPT_RUN_NAME}.json" \
  --output "${SUBMISSION_FILE}"

python -m ccl_poetry_eval.validate_submission \
  --submission "${SUBMISSION_FILE}" \
  --template auto

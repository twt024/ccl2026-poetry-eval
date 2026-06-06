#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

MODEL="${MODEL:-Qwen/Qwen2.5-7B-Instruct}"
BASE_RUN_NAME="${BASE_RUN_NAME:-qwen2.5-7b-instruct}"
MULTI_RUN_NAME="${MULTI_RUN_NAME:-qwen2.5-7b-instruct-task3-mp}"
MAX_NEW_TOKENS="${MAX_NEW_TOKENS:-256}"

TASK1_FILE="${TASK1_FILE:-outputs/submissions/task1_${BASE_RUN_NAME}.json}"
TASK2_FILE="${TASK2_FILE:-outputs/submissions/task2_${BASE_RUN_NAME}.json}"
TASK4_FILE="${TASK4_FILE:-outputs/submissions/task4_${BASE_RUN_NAME}.json}"

PROMPTS=(
  "task3:prompts/task3.txt"
  "task3-direct:prompts/task3_direct.txt"
  "task3-cloze:prompts/task3_cloze.txt"
)

TASK3_FILES=()

for ITEM in "${PROMPTS[@]}"; do
  NAME="${ITEM%%:*}"
  PROMPT="${ITEM#*:}"
  RUN_NAME="${MULTI_RUN_NAME}-${NAME}"
  RAW_FILE="outputs/raw/${RUN_NAME}.jsonl"
  TASK_FILE="outputs/submissions/${RUN_NAME}.json"

  python -m ccl_poetry_eval.infer \
    --task task3 \
    --input "CCPA2026-test_data/task3.json" \
    --output "${RAW_FILE}" \
    --prompt "${PROMPT}" \
    --backend hf \
    --model "${MODEL}" \
    --temperature 0 \
    --max-new-tokens "${MAX_NEW_TOKENS}" \
    --resume

  python -m ccl_poetry_eval.postprocess \
    --task task3 \
    --input "${RAW_FILE}" \
    --output "${TASK_FILE}" \
    --template auto

  TASK3_FILES+=("${TASK_FILE}")
done

python -m ccl_poetry_eval.merge_task3 \
  --inputs "${TASK3_FILES[@]}" \
  --output "outputs/submissions/task3_${MULTI_RUN_NAME}.json" \
  --report "outputs/logs/task3_${MULTI_RUN_NAME}_merge_report.json" \
  --template auto

python -m ccl_poetry_eval.submit \
  --task1 "${TASK1_FILE}" \
  --task2 "${TASK2_FILE}" \
  --task3 "outputs/submissions/task3_${MULTI_RUN_NAME}.json" \
  --task4 "${TASK4_FILE}" \
  --output "outputs/submissions/submission_${BASE_RUN_NAME}_task3mp.json"

python -m ccl_poetry_eval.validate_submission \
  --submission "outputs/submissions/submission_${BASE_RUN_NAME}_task3mp.json" \
  --template auto

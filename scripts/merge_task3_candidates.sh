#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH="${PYTHONPATH:-}:src"

BASE_RUN_NAME="${BASE_RUN_NAME:-qwen2.5-7b-instruct}"
MERGE_RUN_NAME="${MERGE_RUN_NAME:-task3-merged}"

if [[ -z "${TASK3_FILES:-}" ]]; then
  echo "Set TASK3_FILES to a space-separated list of task3 JSON files." >&2
  exit 1
fi

# shellcheck disable=SC2206
FILES=(${TASK3_FILES})

python -m ccl_poetry_eval.merge_task3 \
  --inputs "${FILES[@]}" \
  --output "outputs/submissions/task3_${MERGE_RUN_NAME}.json" \
  --report "outputs/logs/task3_${MERGE_RUN_NAME}_merge_report.json" \
  --template auto

python -m ccl_poetry_eval.submit \
  --task1 "${TASK1_FILE:-outputs/submissions/task1_${BASE_RUN_NAME}.json}" \
  --task2 "${TASK2_FILE:-outputs/submissions/task2_${BASE_RUN_NAME}.json}" \
  --task3 "outputs/submissions/task3_${MERGE_RUN_NAME}.json" \
  --task4 "${TASK4_FILE:-outputs/submissions/task4_${BASE_RUN_NAME}.json}" \
  --output "outputs/submissions/submission_${BASE_RUN_NAME}_${MERGE_RUN_NAME}.json"

python -m ccl_poetry_eval.validate_submission \
  --submission "outputs/submissions/submission_${BASE_RUN_NAME}_${MERGE_RUN_NAME}.json" \
  --template auto

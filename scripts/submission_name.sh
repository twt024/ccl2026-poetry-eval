#!/usr/bin/env bash

submission_output_path() {
  local base_name="${1:-qwen2.5-7b-instruct}"
  local start_no="${SUBMISSION_START_NO:-4}"
  local fixed_no="${SUBMISSION_NO:-}"
  local dir="outputs/submissions"

  mkdir -p "${dir}"

  if [[ -n "${fixed_no}" ]]; then
    printf "%s/submission_%s（%s）.json\n" "${dir}" "${base_name}" "${fixed_no}"
    return
  fi

  local current_no="${start_no}"
  local candidate
  while true; do
    candidate="${dir}/submission_${base_name}（${current_no}）.json"
    if [[ ! -e "${candidate}" ]]; then
      printf "%s\n" "${candidate}"
      return
    fi
    current_no=$((current_no + 1))
  done
}

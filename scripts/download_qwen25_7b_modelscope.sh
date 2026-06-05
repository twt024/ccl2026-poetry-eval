#!/usr/bin/env bash
set -euo pipefail

MODEL_ID="${MODEL_ID:-Qwen/Qwen2.5-7B-Instruct}"
TARGET_DIR="${TARGET_DIR:-/root/autodl-tmp/models/Qwen2.5-7B-Instruct}"

python -m pip install -U modelscope

mkdir -p "$(dirname "${TARGET_DIR}")"

python - <<PY
from modelscope import snapshot_download

model_id = "${MODEL_ID}"
target_dir = "${TARGET_DIR}"
path = snapshot_download(model_id, local_dir=target_dir)
print(path)
PY

du -sh "${TARGET_DIR}"

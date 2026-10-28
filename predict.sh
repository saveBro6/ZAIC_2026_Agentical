#!/bin/bash
set -e

export HF_HUB_OFFLINE=1
export PYTHONPATH="/app:${PYTHONPATH}"

mkdir -p /result/logs

cd /app
python -u -m zaic_2026.main \
    --data-dir /data \
    --result-dir /result \
    --model-path /app/models/Qwen2.5-7B-Instruct


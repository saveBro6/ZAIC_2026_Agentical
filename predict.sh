#!/bin/bash
set -e

export HF_HUB_OFFLINE=1

mkdir -p /result/logs

cd /app
python -u zaic_2026/main.py \
    --data-dir /data \
    --result-dir /result \
    --model-path /app/models/Qwen2.5-7B-Instruct

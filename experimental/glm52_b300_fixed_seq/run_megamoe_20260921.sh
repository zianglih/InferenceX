#!/usr/bin/env bash
# Invoked by campaign_20260921.py after its sealed-environment checks.
set -eo pipefail
EXPERIMENT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$EXPERIMENT_DIR/../../benchmarks/benchmark_lib.sh" --validation-only
check_env_vars CAMPAIGN_TASK_ROOT CAMPAIGN_MODEL_PATH CAMPAIGN_RECIPE_ROOT
cd "$CAMPAIGN_RECIPE_ROOT"
source "$EXPERIMENT_DIR/config.env"
source "$EXPERIMENT_DIR/config-megamoe.env"
export SGLANG_SOURCE_ROOT="$CAMPAIGN_TASK_ROOT/sources/sglang"
export FLASHINFER_SOURCE_ROOT="$CAMPAIGN_TASK_ROOT/sources/flashinfer"
export MEGAMOE_CACHE_ROOT="$CAMPAIGN_TASK_ROOT/caches/megamoe"
export MODEL_PATH="$CAMPAIGN_MODEL_PATH"
export OUTPUT_ROOT="$CAMPAIGN_TASK_ROOT/results"
export RUN_ID=c2-w4a16-megamoe-autotune-20260921
export HF_HOME="$CAMPAIGN_TASK_ROOT/hf-home"
export PYTHONUNBUFFERED=1 MAX_JOBS=16 FLASHINFER_NVCC_THREADS=2
bash "$EXPERIMENT_DIR/w4a16_megamoe_mtp.sh"

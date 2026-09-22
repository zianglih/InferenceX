#!/usr/bin/env bash
# Continue only the fourteen unaccepted coordinates; recovery1 stays immutable.
set -eo pipefail
: "${CAMPAIGN_HELPER_ROOT:?Missing reviewed campaign helper root}"
: "${R7_EXECUTION_LOCK:?Missing execution lock}"
# Execution is bound to the exact publication, accepted runtime, and owned worker.
python3 "$CAMPAIGN_HELPER_ROOT/cli.py" check-execution --lock "$R7_EXECUTION_LOCK" --lock-sha "${R7_EXECUTION_LOCK_SHA256:?Missing activation SHA}"
EXPERIMENT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$EXPERIMENT_DIR/config.env"
source "$EXPERIMENT_DIR/config-megamoe.env"
# Only the new arm uses the published integration successor.
export SGLANG_COMMIT=26c41009549f9ad407e107b33d5144f6e085418b
source "$EXPERIMENT_DIR/common-recovery7.sh"
check_env_vars CAMPAIGN_TASK_ROOT CAMPAIGN_MODEL_PATH CAMPAIGN_RECIPE_ROOT CAMPAIGN_RUN_ID
[[ "$CAMPAIGN_RUN_ID" == c2-w4a16-megamoe-autotune-20260921-recovery7 ]] || exit 1
[[ "$REPO_ROOT" == "$CAMPAIGN_RECIPE_ROOT" ]] || exit 1
export REPO_ROOT EXPERIMENT_DIR CAMPAIGN_TASK_ROOT CAMPAIGN_MODEL_PATH CAMPAIGN_RECIPE_ROOT CAMPAIGN_RUN_ID
export CAMPAIGN_HELPER_ROOT R7_EXECUTION_LOCK R7_EXECUTION_LOCK_SHA256 R7_CAMPAIGN_WORKER_PID
export R7_CASE_ADAPTER="$CAMPAIGN_HELPER_ROOT/case_entry.py"

export SGLANG_SOURCE_ROOT="$CAMPAIGN_TASK_ROOT/sources/sglang"
export FLASHINFER_SOURCE_ROOT="$CAMPAIGN_TASK_ROOT/sources/flashinfer"
export MEGAMOE_CACHE_ROOT="$CAMPAIGN_TASK_ROOT/caches/megamoe"
export MODEL_PATH="$CAMPAIGN_MODEL_PATH" OUTPUT_ROOT="$CAMPAIGN_TASK_ROOT/results"
export RUN_ID="$CAMPAIGN_RUN_ID" HF_HOME="$CAMPAIGN_TASK_ROOT/hf-home"
export PYTHONUNBUFFERED=1 MAX_JOBS=16 FLASHINFER_NVCC_THREADS=2
cd "$CAMPAIGN_RECIPE_ROOT"
export SCENARIOS='8k1k:8192:1024'
export SWEEP_CASES='4:8 4:16 4:32 4:64 4:128 8:4'
run_glm52_sweep w4a16_megamoe
export SCENARIOS='1k1k:1024:1024'
export SWEEP_CASES='4:256 4:4 4:8 4:16 4:32 4:64 4:128 8:4'
run_glm52_sweep w4a16_megamoe

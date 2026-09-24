#!/usr/bin/env bash
# Preserve the current InferenceX random workload and metric implementation.
set -eo pipefail
RECIPE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$RECIPE_DIR/../.." && pwd)
source "$REPO_ROOT/benchmarks/benchmark_lib.sh" --validation-only
check_env_vars CASE_DIR MODEL_PATH SERVED_MODEL PORT CONC SERVER_PID \
    EVAL_ONLY PROFILE PYTHONPATH PYTHONPYCACHEPREFIX
[[ "$EVAL_ONLY" == false && "$PROFILE" == 0 ]] || exit 1
source "$REPO_ROOT/benchmarks/benchmark_lib.sh"
# Keep the shared liveness watch's raw identity inside this case, not /tmp.
INFERENCEX_SERVER_STATE="$CASE_DIR/server_watch.json"
python3 -m infx.bench_serving.server_watch capture --pid "$SERVER_PID" > "$INFERENCEX_SERVER_STATE"
INFERENCEX_SERVER_PID="$SERVER_PID"
# Save the same seeded request plan without issuing HTTP requests.
python3 "$RECIPE_DIR/run.py" --request-lengths --model-path "$MODEL_PATH" \
    --num-prompts "$((10 * CONC))" --destination "$CASE_DIR/requested-lengths.json"
run_benchmark_serving \
    --model "$SERVED_MODEL" --tokenizer "$MODEL_PATH" \
    --port "$PORT" --backend vllm --server-pid "$SERVER_PID" \
    --input-len 1024 --output-len 8192 --random-range-ratio 0.8 \
    --num-prompts "$((10 * CONC))" --max-concurrency "$CONC" \
    --result-filename result --result-dir "$CASE_DIR" \
    --bench-serving-dir "$REPO_ROOT" --use-chat-template

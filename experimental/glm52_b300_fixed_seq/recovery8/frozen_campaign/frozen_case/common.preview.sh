#!/usr/bin/env bash

REPO_ROOT=$(cd "$EXPERIMENT_DIR/../.." && pwd)
source "$REPO_ROOT/benchmarks/benchmark_lib.sh"

run_glm52_sweep() {
    local backend="$1" scenario_case sweep_case
    check_env_vars IMAGE SGLANG_COMMIT MODEL HARDWARE SWEEP_CASES GPU_IDS SCENARIOS \
        RANDOM_RANGE_RATIO PROMPTS_PER_CONCURRENCY PORT MEM_FRACTION_STATIC \
        CHUNKED_PREFILL_SIZE MAX_PREFILL_TOKENS SPECULATIVE_NUM_STEPS \
        SPECULATIVE_EAGLE_TOPK SPECULATIVE_NUM_DRAFT_TOKENS CLEANUP_TERM_SECONDS \
        CLEANUP_KILL_SECONDS EVAL_ONLY PROFILE SGLANG_SOURCE_ROOT MODEL_PATH \
        MODEL_REVISION OUTPUT_ROOT RUN_ID PARALLEL_TOPOLOGY PREFILL_CUDA_GRAPH_POLICY

    case "$PARALLEL_TOPOLOGY" in
        tp|dp-ep) ;;
        *) echo "Unsupported PARALLEL_TOPOLOGY: $PARALLEL_TOPOLOGY" >&2; return 1 ;;
    esac
    case "$PREFILL_CUDA_GRAPH_POLICY" in
        latest-default|disabled) ;;
        *) echo "Unsupported PREFILL_CUDA_GRAPH_POLICY: $PREFILL_CUDA_GRAPH_POLICY" >&2; return 1 ;;
    esac
    if [[ ( "$backend" == w4a16_megamoe || "$backend" == w4a16_cutedsl ) && ( "$PARALLEL_TOPOLOGY" != dp-ep || "$PREFILL_CUDA_GRAPH_POLICY" != disabled ) ]]; then
        echo 'W4A16 arms require PARALLEL_TOPOLOGY=dp-ep and PREFILL_CUDA_GRAPH_POLICY=disabled.' >&2
        return 1
    fi

    if [[ "$EVAL_ONLY" != false || "$PROFILE" != 0 ]]; then
        echo 'This experiment requires EVAL_ONLY=false and PROFILE=0.' >&2
        return 1
    fi
    if [[ ! "$RUN_ID" =~ ^[a-zA-Z0-9._-]+$ || "$RUN_ID" == . || "$RUN_ID" == .. ]]; then
        echo 'RUN_ID must be a simple directory name.' >&2
        return 1
    fi
    if [[ "$OUTPUT_ROOT" != /* || "$OUTPUT_ROOT" == /workspace || "$OUTPUT_ROOT" == /workspace/* ]]; then
        echo 'OUTPUT_ROOT must be an absolute path outside /workspace.' >&2
        return 1
    fi
    if [[ ! -d "$MODEL_PATH" || ! -f "$MODEL_PATH/config.json" ]]; then
        echo 'MODEL_PATH must be a downloaded, revision-pinned model directory.' >&2
        return 1
    fi
    if [[ ! "$MODEL_REVISION" =~ ^[0-9a-f]{40}$ ]]; then
        echo 'MODEL_REVISION must be a full Hugging Face commit SHA.' >&2
        return 1
    fi
    if [[ "$(git -C "$SGLANG_SOURCE_ROOT" rev-parse HEAD)" != "$SGLANG_COMMIT" ]]; then
        echo 'SGLang source HEAD does not match SGLANG_COMMIT.' >&2
        return 1
    fi
    git -C "$SGLANG_SOURCE_ROOT" diff --exit-code HEAD -- python
    export PYTHONPATH="$SGLANG_SOURCE_ROOT/python:$REPO_ROOT"
    if [[ "$backend" == w4a16_megamoe || "$backend" == w4a16_cutedsl ]]; then
        check_env_vars FLASHINFER_SOURCE_ROOT FLASHINFER_COMMIT FLASHINFER_CUDA_ARCH_LIST
        export PYTHONPATH="$SGLANG_SOURCE_ROOT/python:$FLASHINFER_SOURCE_ROOT:$REPO_ROOT"
    fi
    if [[ "$backend" == w4a16_megamoe ]]; then
        check_env_vars MEGAMOE_CACHE_ROOT SGLANG_FLASHINFER_AUTOTUNE_CACHE
        if [[ "$MEGAMOE_CACHE_ROOT" != /* || "$MEGAMOE_CACHE_ROOT" == /workspace || "$MEGAMOE_CACHE_ROOT" == /workspace/* ]]; then
            echo 'MEGAMOE_CACHE_ROOT must be an absolute path outside /workspace.' >&2
            return 1
        fi
        # The new adapter stores Mega tactics in SGLang's namespaced autotune cache.
        export SGLANG_CACHE_DIR="$MEGAMOE_CACHE_ROOT/sglang"
        export FLASHINFER_WORKSPACE_BASE="$MEGAMOE_CACHE_ROOT"
        export CUTE_DSL_CACHE_DIR="$MEGAMOE_CACHE_ROOT/cute-dsl"
        export CUDA_CACHE_PATH="$MEGAMOE_CACHE_ROOT/cuda"
        export TORCH_EXTENSIONS_DIR="$MEGAMOE_CACHE_ROOT/torch-extensions"
        export TORCHINDUCTOR_CACHE_DIR="$MEGAMOE_CACHE_ROOT/torchinductor"
        export TRITON_CACHE_DIR="$MEGAMOE_CACHE_ROOT/triton"
        export XDG_CACHE_HOME="$MEGAMOE_CACHE_ROOT/xdg"
    elif [[ "$backend" == w4a16_cutedsl ]]; then
        check_env_vars CUTEDSL_CACHE_ROOT FLASHINFER_EXPECTED_VERSION CUTE_DSL_EXPECTED_VERSION
        if [[ "$CUTEDSL_CACHE_ROOT" != /* || "$CUTEDSL_CACHE_ROOT" == /workspace || "$CUTEDSL_CACHE_ROOT" == /workspace/* ]]; then
            echo 'CUTEDSL_CACHE_ROOT must be an absolute path outside /workspace.' >&2
            return 1
        fi
        export SGLANG_CACHE_DIR="$CUTEDSL_CACHE_ROOT/sglang"
        export FLASHINFER_WORKSPACE_BASE="$CUTEDSL_CACHE_ROOT"
        unset FLASHINFER_MOE_EP_KNOB_CACHE
    fi
    export PYTHONNOUSERSITE=1
    export SGLANG_ENABLE_JIT_DEEPGEMM=1
    # Spec V2 is always active at the pinned HEAD; its old environment flag is removed.
    unset SGLANG_ENABLE_SPEC_V2
    unset SGLANG_SIMULATE_ACC_LEN SGLANG_SIMULATE_ACC_METHOD SGLANG_SIMULATE_ACC_TOKEN_MODE
    if [[ "$backend" == w4a16_cutedsl ]]; then
        python3 "$EXPERIMENT_DIR/artifacts.py" verify-cutedsl-source
    else
        python3 "$EXPERIMENT_DIR/artifacts.py" verify-source
    fi
    command -v setsid >/dev/null

    for scenario_case in $SCENARIOS; do
        if [[ ! "$scenario_case" =~ ^[a-zA-Z0-9][a-zA-Z0-9._-]*:[1-9][0-9]*:[1-9][0-9]*$ ]]; then
            echo "Invalid name:input:output scenario: $scenario_case" >&2
            return 1
        fi
        (
            export SCENARIO="${scenario_case%%:*}" OSL="${scenario_case##*:}"
            local lengths="${scenario_case#*:}"
            export ISL="${lengths%%:*}"
            for sweep_case in $SWEEP_CASES; do
                if [[ ! "$sweep_case" =~ ^[1-9][0-9]*:[1-9][0-9]*$ ]]; then
                    echo "Invalid TP:concurrency case: $sweep_case" >&2
                    return 1
                fi
                (
                    export BACKEND="$backend" TP="${sweep_case%%:*}" CONC="${sweep_case##*:}"
                    run_glm52_case
                )
            done
        )
    done
}

run_glm52_case() {
    check_env_vars SCENARIO ISL OSL TP CONC BACKEND
    local -a gpu_ids server_args benchmark_args runtime_env
    IFS=, read -r -a gpu_ids <<< "$GPU_IDS"
    if [[ "$TP" -gt "${#gpu_ids[@]}" ]]; then
        echo "TP=$TP exceeds configured GPU_IDS=$GPU_IDS." >&2
        return 1
    fi
    export CUDA_VISIBLE_DEVICES
    CUDA_VISIBLE_DEVICES=$(IFS=,; echo "${gpu_ids[*]:0:$TP}")
    export CASE_DIR="$OUTPUT_ROOT/$RUN_ID/$SCENARIO/${BACKEND//_/-}/tp${TP}_conc${CONC}"
    if [[ -e "$CASE_DIR" ]]; then
        echo "Refusing to overwrite existing artifacts: $CASE_DIR" >&2
        return 1
    fi
    mkdir -p "$CASE_DIR"
    export DP=1 EP=1 SERVER_MAX_RUNNING_REQUESTS="$CONC"
    if [[ "$PARALLEL_TOPOLOGY" == dp-ep ]]; then
        export DP="$TP" EP="$TP"
        # DP attention divides this server-wide limit among DP workers.
        # Preserve client concurrency while giving every worker one slot.
        if [[ "$SERVER_MAX_RUNNING_REQUESTS" -lt "$DP" ]]; then
            export SERVER_MAX_RUNNING_REQUESTS="$DP"
        fi
    fi
    export SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=0
    export SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION=0
    export SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE=bf16
    export SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE=0
    # EXIT runs after this function returns; the PID must outlive its local scope.
    GLM52_SERVER_PID=''
    local benchmark_rc=0
    trap 'finish_glm52_case "$?" "$GLM52_SERVER_PID"' EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM

    select_available_server_port
    server_args=(
        python3 -m sglang.launch_server
        --model-path "$MODEL_PATH" --served-model-name "$MODEL" --host 0.0.0.0 --port "$PORT"
        --trust-remote-code --dtype bfloat16 --quantization modelopt_fp4
        --tensor-parallel-size "$TP"
        --tool-call-parser glm47 --reasoning-parser glm45
        --kv-cache-dtype fp8_e4m3 --attention-backend dsa
        --dsa-decode-backend trtllm --dsa-prefill-backend trtllm
        --cuda-graph-max-bs-decode "$CONC"
        --mem-fraction-static "$MEM_FRACTION_STATIC"
        --chunked-prefill-size "$CHUNKED_PREFILL_SIZE" --max-prefill-tokens "$MAX_PREFILL_TOKENS"
        --flashinfer-allreduce-fusion-backend auto --disable-radix-cache --stream-interval 30
        --speculative-algorithm EAGLE
        --speculative-num-steps "$SPECULATIVE_NUM_STEPS"
        --speculative-eagle-topk "$SPECULATIVE_EAGLE_TOPK"
        --speculative-num-draft-tokens "$SPECULATIVE_NUM_DRAFT_TOKENS"
        --model-loader-extra-config '{"enable_multithread_load": true}'
    )
    case "$BACKEND" in
        w4a4_trtllm)
            server_args+=(--moe-runner-backend flashinfer_trtllm --moe-a2a-backend none)
            ;;
        w4a16_megamoe)
            export SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1
            mkdir -p "$MEGAMOE_CACHE_ROOT/tp$TP"
            export FLASHINFER_MOE_EP_KNOB_CACHE="$MEGAMOE_CACHE_ROOT/tp$TP/knobs.json"
            server_args+=(--moe-runner-backend flashinfer_megamoe
                --moe-a2a-backend flashinfer_megamoe)
            ;;
        w4a16_cutedsl)
            export SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16=1
            export SGLANG_FLASHINFER_MOE_FUSED_FINALIZE=0
            server_args+=(--moe-runner-backend flashinfer_cutedsl --moe-a2a-backend none)
            ;;
        *) echo "Unsupported backend: $BACKEND" >&2; return 1 ;;
    esac
    server_args+=(--data-parallel-size "$DP" --expert-parallel-size "$EP"
        --max-running-requests "$SERVER_MAX_RUNNING_REQUESTS")
    if [[ "$PARALLEL_TOPOLOGY" == dp-ep ]]; then
        server_args+=(--enable-dp-attention --speculative-moe-runner-backend flashinfer_trtllm
            --speculative-moe-a2a-backend none)
    fi
    if [[ "$PREFILL_CUDA_GRAPH_POLICY" == disabled ]]; then
        server_args+=(--cuda-graph-backend-prefill disabled)
    fi
    benchmark_args=(
        --model "$MODEL" --tokenizer "$MODEL_PATH" --port "$PORT" --backend vllm
        --input-len "$ISL" --output-len "$OSL" --random-range-ratio "$RANDOM_RANGE_RATIO"
        --num-prompts "$((CONC * PROMPTS_PER_CONCURRENCY))" --max-concurrency "$CONC"
        --result-filename result --result-dir "$CASE_DIR" --bench-serving-dir "$REPO_ROOT"
        --use-chat-template
    )
    python3 "$EXPERIMENT_DIR/artifacts.py" start
    nvidia-smi > "$CASE_DIR/nvidia-smi.txt"
    python3 -m pip list --format=json > "$CASE_DIR/packages.json"
    runtime_env=(
        PYTHONPATH="$PYTHONPATH" PYTHONNOUSERSITE=1 CUDA_VISIBLE_DEVICES="$CUDA_VISIBLE_DEVICES" \
        SGLANG_ENABLE_JIT_DEEPGEMM="$SGLANG_ENABLE_JIT_DEEPGEMM" \
        SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16="$SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16" \
        SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION="$SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION" \
        SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE="$SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE" \
        SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE="$SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE"
    )
    if [[ "$BACKEND" == w4a16_megamoe || "$BACKEND" == w4a16_cutedsl ]]; then
        runtime_env+=(FLASHINFER_SOURCE_ROOT="$FLASHINFER_SOURCE_ROOT"
            FLASHINFER_COMMIT="$FLASHINFER_COMMIT"
            FLASHINFER_CUDA_ARCH_LIST="$FLASHINFER_CUDA_ARCH_LIST")
    fi
    if [[ "$BACKEND" == w4a16_megamoe ]]; then
        runtime_env+=(FLASHINFER_MOE_EP_KNOB_CACHE="$FLASHINFER_MOE_EP_KNOB_CACHE"
            SGLANG_CACHE_DIR="$SGLANG_CACHE_DIR"
            SGLANG_FLASHINFER_AUTOTUNE_CACHE="$SGLANG_FLASHINFER_AUTOTUNE_CACHE"
            FLASHINFER_WORKSPACE_BASE="$FLASHINFER_WORKSPACE_BASE"
            CUTE_DSL_CACHE_DIR="$CUTE_DSL_CACHE_DIR"
            CUDA_CACHE_PATH="$CUDA_CACHE_PATH"
            TORCH_EXTENSIONS_DIR="$TORCH_EXTENSIONS_DIR"
            TORCHINDUCTOR_CACHE_DIR="$TORCHINDUCTOR_CACHE_DIR"
            TRITON_CACHE_DIR="$TRITON_CACHE_DIR"
            XDG_CACHE_HOME="$XDG_CACHE_HOME")
    elif [[ "$BACKEND" == w4a16_cutedsl ]]; then
        runtime_env+=(SGLANG_FLASHINFER_MOE_FUSED_FINALIZE="$SGLANG_FLASHINFER_MOE_FUSED_FINALIZE"
            SGLANG_CACHE_DIR="$SGLANG_CACHE_DIR"
            FLASHINFER_WORKSPACE_BASE="$FLASHINFER_WORKSPACE_BASE")
    fi
    start_gpu_monitor --output "$CASE_DIR/gpu_metrics.csv"
    python3 "$R8_CASE_ADAPTER" --case-from-environment --activation "$R8_EXECUTION_LOCK"
}

finish_glm52_case() {
    local work_status="$1" server_pid="$2" cleanup_status=0
    trap - EXIT INT TERM
    stop_gpu_monitor || cleanup_status=$?
    if [[ -n "$server_pid" ]]; then
        stop_background_process_groups "$work_status" "$CLEANUP_TERM_SECONDS" "$CLEANUP_KILL_SECONDS" "$server_pid" || cleanup_status=$?
        wait "$server_pid" 2>/dev/null || true
    fi
    if [[ "$work_status" -eq 0 && "$cleanup_status" -ne 0 ]]; then
        work_status=$cleanup_status
    fi
    python3 "$EXPERIMENT_DIR/artifacts.py" finish "$work_status"
    exit "$?"
}

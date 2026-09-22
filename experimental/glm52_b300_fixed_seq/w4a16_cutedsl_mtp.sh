#!/usr/bin/env bash
set -eo pipefail

EXPERIMENT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$EXPERIMENT_DIR/common.sh"
check_env_vars RUN_CUTEDSL
if [[ "$RUN_CUTEDSL" != true ]]; then
    echo 'Source config-cutedsl.env after preparing the pinned CuTe DSL stack.' >&2
    exit 1
fi
run_glm52_sweep w4a16_cutedsl

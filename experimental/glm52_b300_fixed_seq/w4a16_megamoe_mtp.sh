#!/usr/bin/env bash
set -eo pipefail

EXPERIMENT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$EXPERIMENT_DIR/common.sh"
check_env_vars RUN_MEGAMOE
if [[ "$RUN_MEGAMOE" != true ]]; then
    echo 'MegaMoE is deferred. Set RUN_MEGAMOE=true only when the optimized stack is ready.' >&2
    exit 1
fi
run_glm52_sweep w4a16_megamoe

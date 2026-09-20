#!/usr/bin/env bash
set -eo pipefail

EXPERIMENT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$EXPERIMENT_DIR/common.sh"
check_env_vars RUN_MEGAMOE
if [[ "$RUN_MEGAMOE" != true ]]; then
    echo 'Source config-megamoe.env after preparing the pinned optimized stack.' >&2
    exit 1
fi
run_glm52_sweep w4a16_megamoe

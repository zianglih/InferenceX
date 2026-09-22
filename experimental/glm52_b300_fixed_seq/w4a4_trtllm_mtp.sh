#!/usr/bin/env bash
set -eo pipefail

EXPERIMENT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$EXPERIMENT_DIR/common.sh"
run_glm52_sweep w4a4_trtllm

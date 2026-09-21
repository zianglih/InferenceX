"""Source-bound recipe artifacts for later review/publication; no repo mutation."""
import difflib
from pathlib import Path
import sys
import campaign

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'frozen_case'))
import recipe_delta as case_delta


def wrapper():
    campaign.check_inputs()
    old = (HERE / 'recipe/run_megamoe_recovery3.sh').read_text()
    old = old.replace('set -eo pipefail\n', '''set -eo pipefail
: "${CAMPAIGN_HELPER_ROOT:?Missing reviewed campaign helper root}"
: "${R7_EXECUTION_LOCK:?Missing execution lock}"
# This candidate rejects before sourcing recipe or touching model/cache/results.
python3 "$CAMPAIGN_HELPER_ROOT/campaign.py" --check-execution "$R7_EXECUTION_LOCK"
''', 1)
    anchor = 'check_env_vars CAMPAIGN_TASK_ROOT CAMPAIGN_MODEL_PATH CAMPAIGN_RECIPE_ROOT CAMPAIGN_RUN_ID\n'
    assert old.count(anchor) == 1
    old = old.replace(anchor, anchor + '''[[ "$CAMPAIGN_RUN_ID" == c2-w4a16-megamoe-autotune-20260921-recovery7 ]] || exit 1
[[ "$REPO_ROOT" == "$CAMPAIGN_RECIPE_ROOT" ]] || exit 1
export REPO_ROOT EXPERIMENT_DIR CAMPAIGN_TASK_ROOT CAMPAIGN_MODEL_PATH CAMPAIGN_RECIPE_ROOT CAMPAIGN_RUN_ID
export CAMPAIGN_HELPER_ROOT R7_EXECUTION_LOCK
export R7_CASE_ADAPTER="$CAMPAIGN_HELPER_ROOT/case_entry.py"
python3 "$CAMPAIGN_HELPER_ROOT/campaign.py" --prepare-native-parents "$CAMPAIGN_TASK_ROOT" --activation "$R7_EXECUTION_LOCK"
''')
    return old


def common():
    campaign.check_inputs()
    return case_delta.render((HERE / 'recipe/common.sh').read_bytes())


if __name__ == '__main__':
    # Only prints the patch. A caller must deliberately save a local preview.
    old = (HERE / 'recipe/run_megamoe_recovery3.sh').read_text()
    print(''.join(difflib.unified_diff(old.splitlines(True), wrapper().splitlines(True),
          fromfile='run_megamoe_recovery3.sh (frozen)', tofile='run_megamoe_recovery7.sh (disabled)')))

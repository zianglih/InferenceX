"""Render a disabled successor common.sh; never mutate the recipe checkout."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def render(raw):
    expected = json.loads((HERE / 'inputs.json').read_text())['files']['inferencex/experimental/glm52_b300_fixed_seq/common.sh']
    if hashlib.sha256(raw).hexdigest() != expected['sha256']:
        raise ValueError('Original common.sh changed')
    text = raw.decode()
    begin = text.index('    write_command "$CASE_DIR/server_command.sh"')
    end = text.index('\n}\n\nfinish_glm52_case', begin)
    # All case metadata/settings/arrays and monitor/final status stay in their
    # original owner. The adapter owns the server so GLM52_SERVER_PID remains ''.
    replacement = '''    start_gpu_monitor --output "$CASE_DIR/gpu_metrics.csv"
    python3 "$R7_CASE_ADAPTER" --case-from-environment --activation "$R7_EXECUTION_LOCK"
'''
    return text[:begin] + replacement.rstrip() + text[end:]

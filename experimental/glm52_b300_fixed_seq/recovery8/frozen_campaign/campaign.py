#!/usr/bin/env python3
"""Concrete recovery8 environment/contract wiring. No executable CLI activation."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys
import uuid

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'frozen_case'))
import case_adapter as case_adapter

producer = case_adapter.producer
require = producer.require
RUN_ID = producer.RUN_ID
AUDIT_REQUIREMENTS = ('raw14_base_audit', 'native_extension_audit', 'actual_runtime_and_sources',
    'full_source_and_native_payloads', 'first_c8_independent_calibration', 'two_reused_points_unchanged',
    'terminal_worker_and_cleanup', 'final_archive_verification')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bindings():
    return json.loads((HERE / 'inputs.json').read_text())['files']


def check_inputs():
    for name, record in bindings().items():
        if 'copy' in record:
            require(case_adapter.descriptor(HERE / record['copy']) ==
                    {k: record[k] for k in ('bytes', 'sha256')}, 'Frozen wiring input drift: ' + name)
    require(sha(HERE / 'reuse.json') == producer.REUSE_SHA, 'Two original points changed')
    case_adapter.frozen_guard()


def literal_exports(path):
    """Read the pinned literal config, not a general shell/environment evaluator."""
    result = {}
    for line in Path(path).read_text().splitlines():
        tokens = shlex.split(line, comments=True)
        if not tokens:
            continue
        require(tokens[0] == 'export' and len(tokens) == 2 and '=' in tokens[1], 'Nonliteral config statement')
        key, value = tokens[1].split('=', 1)
        require('$' not in value and '`' not in value, 'Config expansion forbidden')
        result[key] = value
    return result


def campaign_environment(base, *, task_root, recipe_root, model_path, helper_root, activation_path):
    """The full exported original recipe environment; pure and parameterized."""
    for value in (task_root, recipe_root, model_path, helper_root, activation_path):
        p = Path(value)
        require(p.is_absolute() and '..' not in p.parts, 'Unsafe resource path')
    env = dict(base)
    env.update(literal_exports(HERE / 'recipe/config.env'))
    env.update(literal_exports(HERE / 'recipe/config-megamoe.env'))
    env['SGLANG_COMMIT']=producer.SG
    env.update(CAMPAIGN_TASK_ROOT=task_root, CAMPAIGN_MODEL_PATH=model_path,
        CAMPAIGN_RECIPE_ROOT=recipe_root, CAMPAIGN_RUN_ID=RUN_ID,
        REPO_ROOT=recipe_root, EXPERIMENT_DIR=recipe_root + '/experimental/glm52_b300_fixed_seq',
        CAMPAIGN_HELPER_ROOT=helper_root, R8_CASE_ADAPTER=helper_root + '/case_entry.py',
        R8_EXECUTION_LOCK=activation_path, SGLANG_SOURCE_ROOT=task_root + '/sources/sglang',
        FLASHINFER_SOURCE_ROOT=task_root + '/sources/flashinfer', MEGAMOE_CACHE_ROOT=task_root + '/caches/megamoe',
        MODEL_PATH=model_path, OUTPUT_ROOT=task_root + '/results', RUN_ID=RUN_ID,
        HF_HOME=task_root + '/hf-home', PYTHONUNBUFFERED='1', MAX_JOBS='16', FLASHINFER_NVCC_THREADS='2')
    # benchmark_lib.sh sets these when sourced, before the sweep.
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONPYCACHEPREFIX'] = env.get('PYTHONPYCACHEPREFIX') or '/tmp/inferencex-pycache'
    return env


def case_environment(env, case, *, port):
    """Mirror only the pinned common.sh exports, checked against the actual shell."""
    require(case in producer.matrix(), 'Unknown remaining coordinate')
    env = dict(env)
    cache = env['MEGAMOE_CACHE_ROOT']
    env.update(SCENARIO=case['scenario'], ISL=str(case['input_len']), OSL='1024',
        SCENARIOS=case['scenario'] + ':' + str(case['input_len']) + ':1024',
        SWEEP_CASES=' '.join(str(x['tp']) + ':' + str(x['concurrency']) for x in producer.matrix() if x['scenario'] == case['scenario']),
        BACKEND='w4a16_megamoe', TP=str(case['tp']), CONC=str(case['concurrency']),
        DP=str(case['tp']), EP=str(case['tp']), SERVER_MAX_RUNNING_REQUESTS=str(case['server_max_running_requests']),
        PORT=str(port), CUDA_VISIBLE_DEVICES=','.join(str(i) for i in range(case['tp'])),
        CASE_DIR=env['OUTPUT_ROOT'] + '/' + RUN_ID + '/' + case['case'],
        PYTHONPATH=env['SGLANG_SOURCE_ROOT'] + '/python:' + env['FLASHINFER_SOURCE_ROOT'] + ':' + env['REPO_ROOT'],
        PYTHONNOUSERSITE='1', SGLANG_ENABLE_JIT_DEEPGEMM='1',
        SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16='1', SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION='0',
        SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE='bf16', SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE='0',
        FLASHINFER_MOE_EP_KNOB_CACHE=cache + '/tp' + str(case['tp']) + '/knobs.json',
        SGLANG_CACHE_DIR=cache + '/sglang', FLASHINFER_WORKSPACE_BASE=cache,
        CUTE_DSL_CACHE_DIR=cache + '/cute-dsl', CUDA_CACHE_PATH=cache + '/cuda',
        TORCH_EXTENSIONS_DIR=cache + '/torch-extensions', TORCHINDUCTOR_CACHE_DIR=cache + '/torchinductor',
        TRITON_CACHE_DIR=cache + '/triton', XDG_CACHE_HOME=cache + '/xdg')
    for key in ('SGLANG_ENABLE_SPEC_V2', 'SGLANG_SIMULATE_ACC_LEN', 'SGLANG_SIMULATE_ACC_METHOD', 'SGLANG_SIMULATE_ACC_TOKEN_MODE'):
        env.pop(key, None)
    case_adapter.case_from_environment(env)
    return env


def contract_for_case(env, native_binding, *, nonce):
    """Create the exact per-case natural-import contract from reviewed descriptors.

    Does not infer any descriptor/runtime acceptance from live maps or logs.
    Actual binding generation/verification is still an activation prerequisite.
    """
    case = case_adapter.case_from_environment(env)
    require(str(uuid.UUID(nonce)) == nonce, 'Nonce must be canonical UUID')
    expected = {'selected', 'selected_prefix', 'native_members', 'provider_source',
                'runtime_seal_sha256', 'stock_manifest_sha256', 'source_pins', 'source_origins', 'defaults', 'hostname'}
    require(set(native_binding) == expected, 'Native input schema differs')
    for key in ('runtime_seal_sha256', 'stock_manifest_sha256'):
        value = native_binding[key]
        require(isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'Unbound native provenance')
    contract = {**native_binding, 'run_id': RUN_ID, 'case': case['case'], 'tp': case['tp'],
                'nonce': nonce, 'hook_sha256': sha(HERE / 'frozen_case/frozen/natural_proof.py')}
    case_adapter.native.validate_lock(contract)
    contract['native_contract_sha256'] = producer.digest(contract)
    return contract


def run_bound_case(env, selected, native_binding, *, nonce, io_factory=case_adapter.PosixIO):
    """Concrete bridge used by local fake tests; CLI never calls this unactivated."""
    check_inputs()
    contract = contract_for_case(env, native_binding, nonce=nonce)
    spec = case_adapter.make_spec(env, selected, contract)
    return case_adapter.run_case(io_factory(spec))


def prepare_native_parents(task_root):
    """Exclusive campaign-level parent preparation; no case leaf or cache copying.

    This function is not callable via current CLI. Future activation verifies
    resource/runtime/source/idle beforehand and calls it once.
    """
    task = Path(task_root)
    require(task.is_absolute() and task.is_dir() and not any(p.is_symlink() for p in (task, *task.parents)), 'Unsafe task root')
    native = task / 'native-runtime'
    require(not native.exists() and not native.is_symlink(), 'Native campaign evidence already exists')
    native.mkdir()
    run = native / RUN_ID
    run.mkdir()
    for scenario in ('8k1k', '1k1k'):
        (run / scenario / 'w4a16-megamoe').mkdir(parents=True)
    case_adapter.write(native / 'campaign-plan.json', plan())
    return run


def audit_prerequisites(raw14, native, proofs):
    require(set(raw14) == case_adapter.audit_native.RAW14, 'Raw14 namespace changed')
    require(set(proofs) == set(AUDIT_REQUIREMENTS) and all(v is not None for v in proofs.values()), 'Audit prerequisites incomplete')
    require(native.get('startup_sealed') is True and native.get('after_sealed') is True,
            'Native pre/post seals missing')
    # This returns obligations, not success. Final consumers must read/validate
    # the actual bound reports and bytes, not truth-test caller-provided flags.
    return {'status': 'AUDIT_INPUTS_PRESENT_NOT_VALIDATED', 'required_validations': list(AUDIT_REQUIREMENTS)}


def plan():
    return {'status': 'NOT_EXECUTION_READY', 'run_id': RUN_ID, 'remaining': producer.matrix(),
            'new_measured_requests': 7640, 'new_warmup_requests': 1528,
            'warmup_per_concurrency': 2, 'measured_per_concurrency': 10,
            'reuse': json.loads((HERE / 'reuse.json').read_text()),
            'native_namespace': '<task_root>/native-runtime/<run_id>/<case>',
            'raw_namespace': '<task_root>/results/<run_id>/<case>',
            'final_join_after_original_status': True,
            'required_archive_scopes': ['results/<run_id>', 'environment', 'native-runtime/<run_id>',
                                        'source archives', 'original wheel native payload provenance', 'immutable old-two references'],
            'archive_policy': 'Explicit manifests; native links forbidden; original wheel payload descriptors bound separately.',
            'audit_prerequisites': list(AUDIT_REQUIREMENTS),
            'activation': json.loads((HERE / 'activation.json').read_text()), 'dispatch_available': False}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check-execution')
    ap.add_argument('--prepare-native-parents')
    ap.add_argument('--case-from-environment', action='store_true')
    ap.add_argument('--activation')
    args = ap.parse_args()
    check_inputs()
    if args.check_execution or args.prepare_native_parents or args.case_from_environment or args.activation:
        raise SystemExit('NOT_EXECUTION_READY: actual resource/runtime/patch/fullbinary/publication gates are null')
    print(json.dumps(plan(), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()

"""Local recovery8 producer skeleton. No CLI dispatcher or resource binding."""
import hashlib
import json
from pathlib import Path
import re

RUN_ID = 'c2-w4a16-megamoe-autotune-20260921-recovery8'
OLD_RUN_ID = 'c2-w4a16-megamoe-autotune-20260921-recovery1'
SG = '26c41009549f9ad407e107b33d5144f6e085418b'
FI = 'ad0a5e5e78e57070ec7c582efe733cb55cd8839f'
REUSE_SHA = '2f3ccb31296bf146e115dcc9af4a6a0a432f5235734eff8d5fcc1d64c06d012b'
REQUIRED_PROOFS = ('stock_c8','stock_payload','environment','source_layout','published_recipe','execution_review')

def require(ok, why):
    if not ok:
        raise ValueError(why)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def matrix():
    result = []
    for scenario, length, coords in [('8k1k',8192,[(4,8),(4,16),(4,32),(4,64),(4,128),(8,4)]),
                                     ('1k1k',1024,[(4,256),(4,4),(4,8),(4,16),(4,32),(4,64),(4,128),(8,4)])]:
        for tp, concurrency in coords:
            result.append({'case': f'{scenario}/w4a16-megamoe/tp{tp}_conc{concurrency}',
                           'scenario': scenario, 'tp': tp, 'dp': tp, 'ep': tp,
                           'concurrency': concurrency, 'server_max_running_requests': max(tp,concurrency),
                           'input_len': length, 'output_len': 1024, 'requests': 10*concurrency})
    return result

def validate_config(c):
    require(c['run_id'] == RUN_ID and c['sglang_commit'] == SG and c['flashinfer_commit'] == FI, 'Identity drift')
    require(c['remaining'] == matrix() and sum(x['requests'] for x in matrix()) == 7640, '14-point matrix drift')
    require(c['reuse'] == {'run_id': OLD_RUN_ID, 'manifest_sha256': REUSE_SHA,
                         'cases': ['8k1k/w4a16-megamoe/tp4_conc256','8k1k/w4a16-megamoe/tp4_conc4'],
                         'requests': 2600, 'raw_file_count': 28, 'native_provenance': 'original-wheel; not patched'}, 'Reuse drift')
    require(c['execution_status'] == 'NOT_EXECUTION_READY', 'This skeleton cannot activate execution')
    require(all(c['activation'].get(k) is None for k in REQUIRED_PROOFS), 'Actual activation belongs to a separately reviewed successor')
    require(set(c['resources'])=={'node','namespace','host','task_root','source_roots','model_path','recipe_commit','runtime_seal'}, 'Resource schema drift')
    require(all(v is None for v in c['resources'].values()), 'No node/source/runtime resource binding in this candidate')

def server_argv(case, *, model_path, port):
    require(case in matrix() and isinstance(port,int) and 1024 <= port <= 65535, 'Invalid case/port')
    require(Path(model_path).is_absolute(), 'Absolute model path required')
    tp, conc = str(case['tp']), str(case['concurrency'])
    return ['python3','-m','sglang.launch_server',
        '--model-path', model_path, '--served-model-name','nvidia/GLM-5.2-NVFP4',
        '--host','0.0.0.0','--port',str(port),'--trust-remote-code','--dtype','bfloat16',
        '--quantization','modelopt_fp4','--tensor-parallel-size',tp,
        '--tool-call-parser','glm47','--reasoning-parser','glm45','--kv-cache-dtype','fp8_e4m3',
        '--attention-backend','dsa','--dsa-decode-backend','trtllm','--dsa-prefill-backend','trtllm',
        '--cuda-graph-max-bs-decode',conc,'--mem-fraction-static','0.80',
        '--chunked-prefill-size','32768','--max-prefill-tokens','32768',
        '--flashinfer-allreduce-fusion-backend','auto','--disable-radix-cache','--stream-interval','30',
        '--speculative-algorithm','EAGLE','--speculative-num-steps','3',
        '--speculative-eagle-topk','1','--speculative-num-draft-tokens','4',
        '--model-loader-extra-config','{"enable_multithread_load": true}',
        '--moe-runner-backend','flashinfer_megamoe','--moe-a2a-backend','flashinfer_megamoe',
        '--data-parallel-size',tp,'--expert-parallel-size',tp,
        '--max-running-requests',str(case['server_max_running_requests']),
        '--enable-dp-attention','--speculative-moe-runner-backend','flashinfer_trtllm',
        '--speculative-moe-a2a-backend','none','--cuda-graph-backend-prefill','disabled']

def child_environment(base, selected, hook_dir, proof_lock, proof_lock_sha):
    """INFO only at launch; SG sets the three defaults in the serving child."""
    import stock
    require(not any(k.startswith('NVSHMEM_') for k in base), 'Inherited NVSHMEM overrides refused')
    env=dict(base, NVSHMEM_DEBUG='INFO')
    return stock.child_environment(env,hook_dir,proof_lock,proof_lock_sha)

def setsid_command(argv, environment):
    """The exact same argv is recorded and executed; caller cannot omit env."""
    require(argv and all(isinstance(x,str) and '\0' not in x for x in argv),'Invalid argv')
    require(all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',k) and isinstance(v,str) and '\0' not in v for k,v in environment.items()),'Invalid env')
    return ['setsid','env',*[k+'='+v for k,v in sorted(environment.items())],*argv]

def benchmark_argv(case, *, model_path, port, case_dir, recipe_root):
    require(case in matrix(),'Unknown workload')
    return ['--model','nvidia/GLM-5.2-NVFP4','--tokenizer',model_path,'--port',str(port),'--backend','vllm',
            '--input-len',str(case['input_len']),'--output-len','1024','--random-range-ratio','0.8',
            '--num-prompts',str(case['requests']),'--max-concurrency',str(case['concurrency']),
            '--result-filename','result','--result-dir',case_dir,'--bench-serving-dir',recipe_root,'--use-chat-template']

def launch_protocol(config, launch_spec, io):
    """Future adapter contract: the recorded env is the exact env passed to spawn.

    This candidate always rejects before IO. A successor must replace this gate
    only after reviewed real resource/proof bindings and an owned-process adapter.
    """
    validate_config(config)
    raise RuntimeError('NOT_EXECUTION_READY: no actual resource/native/fix/calibration bindings')

def exercise_launch_contract(spec, io):
    """Injectable protocol for local fake-IO validation; no default process adapter.

    Future real adapter owns birth validation and partial-spawn cleanup before a
    handle is returned. This function owns every returned handle until handoff.
    """
    command=setsid_command(spec['argv'],spec['env'])
    expected = digest({'command':command,'base_env':spec['base_env']})
    require(spec['command_environment_sha256'] == expected, 'Recorded/executed command mismatch')
    io.fresh_guard(spec)
    io.record_launch_intent(spec)
    child = None
    try:
        # Setsid creates the serving session; passive proof env is only on this
        # child command, never exported to the campaign/benchmark client.
        child = io.spawn(command,env=spec['base_env'])
        io.record_child_birth(child)
        io.wait_health(child)
        proofs = io.read_all_rank_proofs(child)
        require(proofs['case'] == spec['case'] and proofs['run_id'] == RUN_ID, 'Wrong native proof identity')
        require(proofs['ranks'] == list(range(spec['tp'])) and proofs['errors'] == [], 'Incomplete native startup proof')
        io.seal_native_proof_before_benchmark(proofs)
        return io.handoff_to_existing_case_runner(child)
    except BaseException:
        if child is not None:
            io.cleanup_returned_child(child)
        raise

if __name__ == '__main__':
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--check-execution')
    args=ap.parse_args()
    if args.check_execution:
        raise SystemExit('NOT_EXECUTION_READY: this local candidate never authorizes execution')
    c = json.loads((Path(__file__).parent/'candidate.json').read_text())
    validate_config(c)
    print(json.dumps({'status':c['execution_status'], 'cases':len(matrix()), 'new_requests':7640,
                      'old_requests':2600, 'dispatch_available':False}, indent=2))

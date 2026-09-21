#!/usr/bin/env python3
"""Concrete per-case IO/lifecycle candidate. CLI remains plan-only until rebound."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
FROZEN = HERE / 'frozen'
sys.path.insert(0, str(FROZEN))
import producer
import natural_proof as native
import audit_native
import stock
from owned import Registry

require = producer.require
MAX_JSON = 1024 * 1024
RUNTIME_KEYS = ('PYTHONPATH', 'PYTHONNOUSERSITE', 'CUDA_VISIBLE_DEVICES', 'SGLANG_ENABLE_JIT_DEEPGEMM',
    'SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16', 'SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION',
    'SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE', 'SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE',
    'FLASHINFER_SOURCE_ROOT', 'FLASHINFER_COMMIT', 'FLASHINFER_CUDA_ARCH_LIST',
    'FLASHINFER_MOE_EP_KNOB_CACHE', 'SGLANG_CACHE_DIR', 'SGLANG_FLASHINFER_AUTOTUNE_CACHE',
    'FLASHINFER_WORKSPACE_BASE', 'CUTE_DSL_CACHE_DIR', 'CUDA_CACHE_PATH', 'TORCH_EXTENSIONS_DIR',
    'TORCHINDUCTOR_CACHE_DIR', 'TRITON_CACHE_DIR', 'XDG_CACHE_HOME')
NATIVE_KEYS = ('LD_LIBRARY_PATH', 'NVSHMEM_DEBUG',
    'PYTHONDONTWRITEBYTECODE', 'MEGAMOE_R7_NATIVE_PROOF_LOCK', 'MEGAMOE_R7_NATIVE_PROOF_SHA256')


def descriptor(path):
    data = Path(path).read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def read(path, limit=MAX_JSON):
    p = Path(path)
    require(p.is_file() and not p.is_symlink() and p.stat().st_size <= limit, 'Unsafe/oversized receipt')
    return json.loads(p.read_bytes())


def write(path, value):
    native.atomic_bytes(Path(path), (json.dumps(value, sort_keys=True, indent=2) + '\n').encode(), MAX_JSON)


def frozen_guard():
    inputs = read(HERE / 'inputs.json')
    for record in inputs['files'].values():
        if 'copy' in record:
            require(descriptor(HERE / record['copy']) == {k: record[k] for k in ('bytes', 'sha256')}, 'Frozen module bytes drift')
    for module in (producer, native, audit_native, stock):
        require(Path(module.__file__).resolve().parent == FROZEN, 'Module import origin differs')


def case_from_environment(env):
    key = f'{env["SCENARIO"]}/w4a16-megamoe/tp{env["TP"]}_conc{env["CONC"]}'
    case = next((x for x in producer.matrix() if x['case'] == key), None)
    require(case is not None, 'Not one of the exact fourteen remaining coordinates')
    exact = {'RUN_ID': producer.RUN_ID, 'BACKEND': 'w4a16_megamoe', 'SGLANG_COMMIT': producer.SG,
             'FLASHINFER_COMMIT': producer.FI, 'MEM_FRACTION_STATIC': '0.80', 'RANDOM_RANGE_RATIO': '0.8',
             'PROMPTS_PER_CONCURRENCY': '10', 'EVAL_ONLY': 'false', 'PROFILE': '0',
             'ISL': str(case['input_len']), 'OSL': '1024', 'DP': str(case['tp']), 'EP': str(case['tp']),
             'SERVER_MAX_RUNNING_REQUESTS': str(case['server_max_running_requests']),
             'CHUNKED_PREFILL_SIZE': '32768', 'MAX_PREFILL_TOKENS': '32768',
             'SPECULATIVE_NUM_STEPS': '3', 'SPECULATIVE_EAGLE_TOPK': '1', 'SPECULATIVE_NUM_DRAFT_TOKENS': '4',
             'PARALLEL_TOPOLOGY': 'dp-ep', 'PREFILL_CUDA_GRAPH_POLICY': 'disabled'}
    require(all(env.get(k) == v for k, v in exact.items()), 'Original recipe settings changed')
    require(env['CASE_DIR'] == str(Path(env['OUTPUT_ROOT']) / producer.RUN_ID / key), 'Raw case path changed')
    return case


def make_spec(env, selected, native_contract):
    """Needs a future reviewed runtime binding, never inferred from incoming logs."""
    case = case_from_environment(env)
    root = Path(env['CAMPAIGN_TASK_ROOT'])
    require(root.is_absolute() and '..' not in root.parts, 'Unsafe campaign path')
    require(Path(env['OUTPUT_ROOT']) == root / 'results', 'Results root differs')
    require(not any(p.is_symlink() for p in (root, *root.parents)), 'Campaign path linked')
    evidence = root / 'native-runtime' / producer.RUN_ID / case['case']
    port = int(env['PORT'])
    argv = producer.server_argv(case, model_path=env['MODEL_PATH'], port=port)
    bench = producer.benchmark_argv(case, model_path=env['MODEL_PATH'], port=port,
                                   case_dir=env['CASE_DIR'], recipe_root=env['REPO_ROOT'])
    require(native_contract['case'] == case['case'] and native_contract['tp'] == case['tp'], 'Native case identity')
    require(native_contract['selected_prefix'] == selected['prefix'], 'Selected native prefix differs')
    native.validate_lock(native_contract)
    for key, source_key, descriptor_key in [('host', 'host', 'host_descriptor'), ('uid', 'plugin', 'plugin_descriptor')]:
        item = native_contract['selected'][key]
        require(str(Path(selected[source_key]).resolve(strict=True)) == item['resolved_path'], 'Selected image target differs')
        require({k: item[k] for k in ('bytes', 'sha256')} == {k: selected[descriptor_key][k] for k in ('bytes', 'sha256')}, 'Selected image descriptor differs')
    require(native_contract['hook_sha256'] == descriptor(FROZEN / 'natural_proof.py')['sha256'], 'Hook identity differs')
    return {'case': case, 'base_env': dict(env), 'argv': argv, 'benchmark_args': bench,
            'case_dir': env['CASE_DIR'], 'native_root': str(evidence), 'selected': selected,
            'contract': dict(native_contract), 'port': port,
            'benchmark_lib': str(Path(env['REPO_ROOT']) / 'benchmarks/benchmark_lib.sh'),
            'artifacts_py': str(Path(env['EXPERIMENT_DIR']) / 'artifacts.py')}


def phase_records(root, phase, lock, owners, *, owner_bind=None):
    require(not list(root.glob('error-*.json')), 'Native observation error present')
    records, ranks = [], set()
    files = list(root.iterdir())
    require(len(files) <= 128, 'Native evidence count exceeded')
    for path in sorted(root.glob(phase + '-rank-*-pid-*.json')):
        record = read(path, 64 * 1024)
        require(record['maps_file'] == path.with_suffix('.maps').name, 'Maps filename differs')
        raw_path = root / record['maps_file']
        require(raw_path.is_file() and not raw_path.is_symlink() and raw_path.stat().st_size <= native.MAX_MAPS, 'Unsafe maps file')
        raw = raw_path.read_bytes()
        rank = record['rank']
        require(type(rank) is int and 0 <= rank < lock['tp'] and rank not in ranks, 'Duplicate/wrong rank')
        if owner_bind is not None:
            owners[rank] = owner_bind({'pid': record['pid'], 'starttime': record['starttime']})
        audit_native.snapshot(record, raw, lock, owners, phase)
        ranks.add(rank)
        records.append((record, raw))
    require(ranks == set(range(lock['tp'])) and len({x['pid'] for x in owners.values()}) == lock['tp'], 'All rank evidence required before client')
    allowed = set()
    for prefix in (('startup',) if phase == 'startup' else ('startup', 'after')):
        for rank, owner in owners.items():
            base = f'{prefix}-rank-{rank}-pid-{owner["pid"]}'
            allowed.update((base + '.json', base + '.maps'))
    require({p.name for p in files} == allowed, 'Extra, partial or orphan native evidence')
    return records


class PosixIO:
    """Actual local process adapter, never reached by this candidate's CLI."""
    def __init__(self, spec):
        self.spec, self.root = spec, Path(spec['native_root'])
        self.registry = Registry(self.persist_owner)
        self.counter = 0
        self.persisted = {}
        self.server = None
        self.streams = []

    def persist_owner(self, child):
        value = {'label': child.label, 'pid': child.proc.pid, 'birth': child.birth, 'known': child.known}
        fingerprint = producer.digest(value)
        if self.persisted.get(child.proc.pid) == fingerprint:
            return
        self.counter += 1
        require(self.counter <= 4096, 'Owner ledger count bound')
        write(self.root / f'owner-{self.counter:06d}.json',
              {**value, 'at': time.time()})
        self.persisted[child.proc.pid] = fingerprint

    def prepare(self):
        frozen_guard()
        inputs = read(HERE / 'inputs.json')['files']
        for name, relative in [('benchmark_lib', 'inferencex/benchmarks/benchmark_lib.sh'),
                               ('artifacts_py', 'inferencex/experimental/glm52_b300_fixed_seq/artifacts.py')]:
            require(descriptor(self.spec[name]) == inputs[relative], 'Original recipe helper changed')
        require(self.root.parent.is_dir() and not self.root.exists(), 'Case native parent must be prepared; case exclusive')
        require(not any(p.is_symlink() for p in (self.root, *self.root.parents)), 'Native path linked')
        self.root.mkdir()
        proof = self.root / 'proof'; proof.mkdir()
        contract = self.spec['contract']
        contract.update(proof_root=str(proof), execution_status='REVIEWED_SUCCESSOR_REQUIRED')
        write(self.root / 'native-contract.json', contract)
        env = producer.child_environment(self.spec['base_env'], self.spec['selected'], str(FROZEN),
                                        str(self.root / 'native-contract.json'),
                                        descriptor(self.root / 'native-contract.json')['sha256'])
        # Preserve inherited environment without serializing unrelated variables
        # (potential credentials). Explicit env args cover original runtime keys
        # plus the reviewed native-only changes; the same base is passed to Popen.
        explicit = {key: env[key] for key in (*RUNTIME_KEYS, *NATIVE_KEYS)}
        self.spec['command'] = producer.setsid_command(self.spec['argv'], explicit)
        write(self.root / 'launch-intent.json', {'argv': self.spec['command'],
              'base_environment_sha256': producer.digest(self.spec['base_env']),
              'at': time.time(), 'case': self.spec['case']})
        # Original raw filenames retained. Client environment gets no native overlay.
        case_dir = Path(self.spec['case_dir'])
        with (case_dir / 'server_command.sh').open('x') as stream:
            stream.write(shlex.join(self.spec['command']) + '\n')
        client = ['env', 'PYTHONPATH=' + self.spec['base_env']['PYTHONPATH'], 'EVAL_ONLY=false', 'PROFILE=0',
                  'bash', '-c', 'source "$1"; shift; run_benchmark_serving "$@"', '_', self.spec['benchmark_lib'],
                  *self.spec['benchmark_args']]
        with (case_dir / 'benchmark_command.sh').open('x') as stream:
            stream.write(shlex.join(client) + '\n')

    def open_output(self, path):
        stream = Path(path).open('xb')
        self.streams.append(stream)
        return stream

    def start_server(self):
        self.server = self.registry.spawn(self.spec['command'], env=self.spec['base_env'],
                     output=self.open_output(Path(self.spec['case_dir']) / 'server.log'), label='server')
        return self.server

    def command(self, argv, label, output, *, env=None):
        actual_env = env or self.spec['base_env']
        write(self.root / (label + '-command.json'), {'argv': argv,
              'base_environment_sha256': producer.digest(self.spec['base_env']),
              'environment_delta': {k: v for k, v in actual_env.items()
                                    if self.spec['base_env'].get(k) != v}, 'at': time.time()})
        child = self.registry.spawn(argv, env=env or self.spec['base_env'],
                   output=self.open_output(output), label=label, new_session=True)
        while child.proc.poll() is None:
            self.registry.refresh()
            time.sleep(0.2)
        return child.proc.returncode

    def wait_health(self):
        # Preserve original helper's server_watch capture and pass the identical
        # captured state to the later client shell; don't lose shell-local state.
        code = 'source "$1"; wait_for_server_ready --port "$2" --server-log "$3" --server-pid "$4" || exit $?; cp -- "$INFERENCEX_SERVER_STATE" "$5" || exit $?; printf "%s\\n" "$INFERENCEX_SERVER_STATE"'
        require(self.command(['bash', '-c', code, '_', self.spec['benchmark_lib'], str(self.spec['port']),
                str(Path(self.spec['case_dir']) / 'server.log'), str(self.server.proc.pid),
                str(self.root / 'server-watch.json')], 'readiness', self.root / 'readiness.log') == 0, 'Health failed')

    def server_info(self, phase):
        require(self.command(['curl', '--fail', '--silent', '--show-error',
                f'http://127.0.0.1:{self.spec["port"]}/get_server_info'], 'server-info-' + phase,
                Path(self.spec['case_dir']) / f'server_info.{phase}.json') == 0, 'Server info failed')

    def startup(self):
        owners = {}
        records = phase_records(self.root / 'proof', 'startup', self.spec['contract'], owners,
                                owner_bind=self.server.bind_rank)
        for record, _ in records:
            # Re-read same live owner after all snapshots, before any client.
            self.server.bind_rank(owners[record['rank']])
        log_path=Path(self.spec['case_dir'])/'server.log'
        require(log_path.stat().st_size <= 128*1024**2, 'Server log bound')
        raw=log_path.read_bytes()
        proof=stock.proxy_info(raw.decode(errors='replace'), owners, self.spec['contract']['hostname'])
        write(self.root/'proxy-disabled.json', {**proof,'schema_version':1,'at':time.time(),'server_log_prefix':{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}})
        write(self.root / 'startup-seal.json', {'at': time.time(), 'owners': owners,
             'files': {p.name: descriptor(p) for p in (self.root / 'proof').iterdir()},
             'native_contract': descriptor(self.root / 'native-contract.json'), 'errors': []})
        return owners, records

    def snapshot_autotune(self):
        require(self.command(['python3', self.spec['artifacts_py'], 'snapshot-autotune'],
                'snapshot-autotune', self.root / 'snapshot-autotune.log') == 0, 'Autotune snapshot failed')

    def benchmark(self):
        env = dict(self.spec['base_env'])
        env.update(INFERENCEX_SERVER_STATE=str(self.root / 'server-watch.json'),
                   INFERENCEX_SERVER_PID=str(self.server.proc.pid))
        return self.command(['bash', '-c', 'source "$1"; shift; run_benchmark_serving "$@"',
                '_', self.spec['benchmark_lib'], *self.spec['benchmark_args']], 'benchmark',
                Path(self.spec['case_dir']) / 'benchmark.log', env=env)

    def after(self, owners, startup, window):
        for rank, owner in owners.items():
            self.server.bind_rank(owner)
            native.snapshot_owned_process(self.spec['contract'], self.root / 'proof', rank, owner)
        after = phase_records(self.root / 'proof', 'after', self.spec['contract'], owners)
        before = {record['rank']: record for record, _ in startup}
        for record, _ in after:
            rank = record['rank']
            require(before[rank]['at'] <= window['start'] <= window['end'] <= record['at'], 'Native window order')
            for selected in self.spec['contract']['selected'].values():
                path = selected['resolved_path']
                require(before[rank]['native']['images'][path] == record['native']['images'][path], 'Native image changed')
        write(self.root / 'after-seal.json', {'at': time.time(), 'window': window,
             'files': {p.name: descriptor(p) for p in (self.root / 'proof').iterdir()}, 'errors': []})

    def cleanup(self):
        result = self.registry.cleanup()
        for stream in self.streams:
            stream.close()
        return result

    def terminal(self, value):
        write(self.root / 'exit.json', value)


def run_case(io):
    """Real ordering shared by fake fixtures and the explicit PosixIO backend."""
    terminal = {'status': 'FAILED', 'error': None, 'benchmark_exit': None, 'native_after': False}
    result = 1
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Owned case interrupted by signal ' + str(signum))
    saved = {sig: signal.getsignal(sig) for sig in (signal.SIGINT, signal.SIGTERM)}
    for sig in saved:
        signal.signal(sig, interrupted)
    try:
        io.prepare()
        io.start_server()
        io.wait_health()
        io.server_info('before')
        owners, startup = io.startup()  # mandatory all-rank seal before client
        io.snapshot_autotune()
        window = {'start': time.time()}
        terminal['benchmark_exit'] = io.benchmark()
        window['end'] = time.time()
        # Also attempt post evidence after a nonzero client exit; never claim pass.
        after_info_error = None
        try:
            io.server_info('after')
        except Exception as error:
            after_info_error = error
        io.after(owners, startup, window)
        terminal['native_after'] = True
        if after_info_error is not None:
            raise after_info_error
        result = terminal['benchmark_exit']
        terminal['status'] = 'CASE_PHASES_COMPLETED' if result == 0 else 'BENCHMARK_FAILED'
    except BaseException as error:
        terminal['error'] = repr(error)
        print(terminal['error'], file=sys.stderr)
    finally:
        # Teardown cannot be interrupted a second time, leaving owned children.
        for sig in saved:
            signal.signal(sig, signal.SIG_IGN)
        try:
            terminal['cleanup'] = io.cleanup()
            if any(x['cleanup_pending'] for x in terminal['cleanup']):
                result = 1
        except BaseException as error:
            terminal['cleanup_error'] = repr(error)
            result = 1
        terminal['exit_code'] = result
        terminal['at'] = time.time()
        # Receipt failure is a failure, never successful cleanup evidence.
        try:
            io.terminal(terminal)
        except BaseException as error:
            print('Terminal receipt failed: ' + repr(error), file=sys.stderr)
            result = 1
        for sig, handler in saved.items():
            signal.signal(sig, handler)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case-from-environment', action='store_true')
    parser.add_argument('--activation')
    args = parser.parse_args()
    frozen_guard()
    if args.case_from_environment or args.activation:
        raise SystemExit('NOT_EXECUTION_READY: resource/runtime/patched C8/publication bindings remain null')
    print(json.dumps({'status': 'LOCAL_CASE_ADAPTER_CANDIDATE', 'dispatch_available': False,
                      'activation': read(HERE / 'activation.json'), 'remaining_cases': len(producer.matrix())}))


if __name__ == '__main__':
    main()

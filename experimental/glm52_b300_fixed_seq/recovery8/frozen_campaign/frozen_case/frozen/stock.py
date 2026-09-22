"""Pure stock-wheel source/default/map contracts; never imports a provider."""
import hashlib
import json
from pathlib import Path
import re

SG = '26c41009549f9ad407e107b33d5144f6e085418b'
OLD_SG = '6d8a58f177a1488e10e8567a3fa4b4fccd0a26e2'
FI = 'ad0a5e5e78e57070ec7c582efe733cb55cd8839f'
TASK = '/data/home/ziangli/inferencex-glm52-megamoe-autotune-20260921-recovery8'
RUN = 'c2-w4a16-megamoe-autotune-20260921-recovery8'
PREFIX = '/opt/sglang/lib/python3.12/site-packages/nvidia/nvshmem'
HOST = PREFIX + '/lib/libnvshmem_host.so.3'
UID = PREFIX + '/lib/nvshmem_bootstrap_uid.so.3'
HOST_SHA = 'c43004bb93053aa70603a204fe0c9052bdd29f38822d3048599183f8d5930d8f'
UID_SHA = '69b2b46a146adec27389c3bbdb46efd3d0853dc32eead1f6e08d6d906ad70c82'
DEFAULTS = {'NVSHMEM_REMOTE_TRANSPORT':'none', 'NVSHMEM_IB_ENABLE_IBGDA':'0', 'NVSHMEM_DISABLE_LOCAL_ONLY_PROXY':'1'}
EFFECTIVE = {**DEFAULTS,'NVSHMEM_DEBUG':'INFO'}
VARIANT = 'original-wheel-sglang-no-proxy-defaults'
ORIGINS = {
    'sglang': {'path':TASK+'/sources/sglang/python/sglang/__init__.py','sha256':'0c6bd1b5bc75da013d49d26f7799ca36d682779293405dce1adc193b97a0e6bd'},
    'flashinfer': {'path':TASK+'/sources/flashinfer/flashinfer/__init__.py','sha256':'c16462859defd38449f80aa35790f4d3ee71af86a157069838af661a48755857'},
}

def need(v,m):
    if not v: raise ValueError(m)

def digest(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def initial_environment(base):
    need(isinstance(base,dict) and all(isinstance(k,str) and isinstance(v,str) for k,v in base.items()), 'Initial environment schema')
    need({k:v for k,v in base.items() if k.startswith('NVSHMEM_')} == {'NVSHMEM_DEBUG':'INFO'}, 'Initial defaults must be absent; only NVSHMEM_DEBUG=INFO supplied')
    need(not any(base.get(k) for k in ('LD_PRELOAD','LD_AUDIT','TORCH_USE_RTLD_GLOBAL')), 'Initial native loader injection')
    need('SGLANG_FLASHINFER_AUTOTUNE_EXTEND' not in base, 'No forced EXTEND override')
    for k in ('PYTHONPATH','LD_LIBRARY_PATH'):
        parts=base.get(k,'').split(':') if base.get(k) else []
        need(all(x and Path(x).is_absolute() and '..' not in Path(x).parts for x in parts),'Unsafe search path')
        need(not any('host-search' in Path(x).parts or 'inferencex-glm52-nvshmem-init-pair' in x for x in parts),'Selected-build overlay in stock run')
    return base

def child_environment(base,hook_dir,proof_lock,proof_sha):
    initial_environment(base)
    for name in (hook_dir,proof_lock):need(Path(name).is_absolute() and '..' not in Path(name).parts,'Unsafe proof path')
    need(re.fullmatch('[0-9a-f]{64}',proof_sha),'Unbound proof SHA')
    env=dict(base)
    env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',
        PYTHONPATH=hook_dir+(':'+base['PYTHONPATH'] if base.get('PYTHONPATH') else ''),
        MEGAMOE_R8_NATIVE_PROOF_LOCK=proof_lock,MEGAMOE_R8_NATIVE_PROOF_SHA256=proof_sha)
    return env

def contract(c):
    need(c['selected_prefix']==PREFIX,'Wrong stock native prefix')
    need(set(c['selected'])=={'host','uid'},'Stock host/UID required')
    for role,path,size,sha in (('host',HOST,41241312,HOST_SHA),('uid',UID,73704,UID_SHA)):
        need(c['selected'][role]=={'resolved_path':path,'bytes':size,'sha256':sha},'Stock native identity differs: '+role)
    need(c['source_pins']=={'sglang':SG,'flashinfer':FI,'bootstrap_sglang':OLD_SG},'Mixed source provenance differs')
    need(c['source_origins']==ORIGINS and c['defaults']==EFFECTIVE,'Source origins/defaults differ')
    raw=Path(__file__).with_name('stock-native.json').read_bytes()
    bound=json.loads(raw)
    need(c['stock_manifest_sha256']==hashlib.sha256(raw).hexdigest(),'Stock provider descriptor manifest differs')
    expected_members={PREFIX+'/'+n:d for n,d in bound['members'].items() if PREFIX+'/'+n not in (HOST,UID)}
    need(c['native_members']==expected_members,'Stock member descriptor set differs')
    need(isinstance(c['native_members'],dict) and len(c['native_members'])<=64,'Native member bound')
    for path,d in c['native_members'].items():
        q=Path(path);need(q.is_relative_to(PREFIX+'/lib') and '..' not in q.parts and q.suffix=='.3','Native member outside stock library')
        need(set(d)=={'bytes','sha256'} and type(d['bytes']) is int and 0<d['bytes']<=128*1024**2 and re.fullmatch('[0-9a-f]{64}',d['sha256']),'Native member descriptor')
    # The full actual provider manifest must independently bind these descriptors.
    need(HOST not in c['native_members'] and UID not in c['native_members'],'Duplicate selected native identities')

def startup_evidence(record,rank):
    e=record['stock_evidence']
    need(set(e)=={'entry_environment','return_environment','source_origins','device'},'Startup stock evidence schema/unknown error')
    need(e['entry_environment']==e['return_environment']==EFFECTIVE,'Natural init entry/return defaults not established by SG')
    need(e['source_origins']==ORIGINS,'Actual runtime source origin drift')
    need(type(e['device']) is int and e['device']==rank,'Rank/device default proof differs')

def proxy_info(log,owners,hostname):
    need(isinstance(hostname,str) and re.fullmatch('[A-Za-z0-9_.-]+',hostname),'Bound actual hostname required')
    matches=[]
    # Concurrent printf may glue unfinished text to the exact known hostname.
    # Foreign prefixes still delimit spans; their warning cannot be borrowed.
    host=re.escape(hostname)
    prefix=re.compile(r'(?P<host>'+host+r'|(?:(?!'+host+r')[A-Za-z0-9_.-])+):(?P<pid>[0-9]+):(?P<tid>[0-9]+) \[(?P<device>-?[0-9]+)\] NVSHMEM (?P<level>[A-Z]+) ')
    for line_no,line in enumerate(log.splitlines(),1):
        need(len(line)<=1024**2,'Physical native log-line bound')
        prefixes=list(prefix.finditer(line));found=0
        for index,m in enumerate(prefixes):
            stop=prefixes[index+1].start() if index+1<len(prefixes) else len(line)
            span=line[m.start():stop]
            if 'Proxy is disabled.' not in span:continue
            found+=1
            need(m['level']=='INFO' and span[m.end()-m.start():].startswith('Proxy is disabled.'),'Unattributed native proxy INFO span')
            d={k:m[k] if k=='host' else int(m[k]) for k in ('host','pid','tid','device')}
            need(d['host']==hostname and d['device'] in owners and owners[d['device']]['pid']==d['pid'],'Proxy INFO not actual owned rank/device')
            need('Device side wait_until timeouts and global exit will not function.' in span,'Native limitation text absent from same prefix span')
            matches.append({'line':line_no,'text':span,**d})
        need(found==line.count('Proxy is disabled.'),'Unattributed or duplicate native proxy phrase')
    need(len(matches)<=2*len(owners) and {x['device'] for x in matches}==set(owners),'Proxy NONE coverage incomplete/excessive')
    return {'lines':matches,'covered_ranks':sorted(owners),'device_wait_timeout_and_global_exit_functionality':'disabled by this native configuration','native_private_state_read':False}

def plan():
    return {'status':'LOCAL_STOCK_CONSUMER_PREPARATION_NOT_EXECUTION_BOUND','run_id':RUN,
        'sglang':SG,'historical_sglang':OLD_SG,'flashinfer':FI,'native_variant':VARIANT,
        'resources':None,'execution':None,'actual_stock_c8':None,'producer_hook_sha256':None,
        'gpu_acceptance':False}

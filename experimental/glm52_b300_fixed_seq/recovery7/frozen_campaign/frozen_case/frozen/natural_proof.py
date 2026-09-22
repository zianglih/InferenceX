"""Natural-import proof prototype. No Torch/CUDA/native import or native calls."""
import functools
import hashlib
import importlib.abc
import inspect
import json
import os
from pathlib import Path
import stat
import sys
import time
import stock

TARGET = 'nvshmem.core.init_fini'
MAX_MAPS = 4*1024*1024
MAX_ELF = 128*1024*1024

def require(ok, message):
    if not ok: raise ValueError(message)

def sha(b): return hashlib.sha256(b).hexdigest()

def validate_lock(lock):
    stock.contract(lock)
    require(set(lock['selected'])=={'host','uid'},'Exactly host and UID required')
    prefix=Path(lock['selected_prefix'])
    require(prefix.is_absolute() and '..' not in prefix.parts,'Unsafe native prefix')
    all_members={**lock['native_members'],**{x['resolved_path']:x for x in lock['selected'].values()}}
    require(0<len(all_members)<=64,'Native file count bound')
    for path,item in all_members.items():
        q=Path(path)
        require(q.is_absolute() and '..' not in q.parts and q.is_relative_to(prefix/'lib'),'Native member escapes selected lib')
        require(type(item['bytes'])is int and 0<item['bytes']<=MAX_ELF and len(item['sha256'])==64 and all(x in '0123456789abcdef' for x in item['sha256']),'Native descriptor invalid')

def atomic_bytes(path,b,limit):
    require(len(b)<=limit, 'Proof record oversized')
    tmp = path.with_name(path.name+f'.tmp-{os.getpid()}')
    with tmp.open('xb') as f: f.write(b); f.flush(); os.fsync(f.fileno())
    os.link(tmp,path)
    tmp.unlink()

def atomic(path,value):
    atomic_bytes(path,(json.dumps(value,sort_keys=True)+'\n').encode(),64*1024)

def identity(pid=None):
    pid=os.getpid() if pid is None else pid
    require(type(pid)is int and pid>1,'Invalid PID')
    s = Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
    return {'pid':pid, 'starttime':int(s[19])}

def selected_maps(raw, selected, native_members=None):
    """Pure parse: require exactly the selected host and UID, with no deleted image."""
    require(len(raw)<=MAX_MAPS, 'Maps bound')
    paths = {x['resolved_path'] for x in selected.values()}
    allowed=paths|set(native_members or {})
    rows = {}
    for line in raw.decode().splitlines():
        fields=line.split(None,5)
        if len(fields)!=6: continue
        path=fields[5]
        basename=Path(path.removesuffix(' (deleted)')).name
        relevant = basename.startswith(('libnvshmem_host.so','nvshmem_bootstrap_','nvshmem_transport_'))
        if not relevant: continue
        require(path in allowed, 'Unexpected/deleted host, bootstrap or transport mapped path')
        start,end=(int(x,16) for x in fields[0].split('-'))
        require(start<end and int(fields[4])>0, 'Invalid mapped image')
        rows.setdefault(path,[]).append({'range':[start,end],'perms':fields[1], 'offset':int(fields[2],16),
                                  'dev':fields[3], 'inode':int(fields[4]), 'path':path})
    require(paths<=rows.keys(),'Selected host/UID not naturally mapped')
    require({p for p in rows if Path(p).name.startswith('libnvshmem_host.so')}=={selected['host']['resolved_path']},'More than selected host mapped')
    require({p for p in rows if Path(p).name.startswith('nvshmem_bootstrap_uid.so')}=={selected['uid']['resolved_path']},'More than selected UID mapped')
    for path,r in rows.items():
        require(r and any('x' in x['perms'] for x in r), 'Missing executable native image: '+path)
        require(len({(x['dev'],x['inode']) for x in r})==1, 'Native image inode differs')
    return rows

def capture(lock,pid=None):
    validate_lock(lock)
    pid=os.getpid() if pid is None else pid
    with open('/proc/'+str(pid)+'/maps','rb') as f: raw=f.read(MAX_MAPS+1)
    rows=selected_maps(raw,lock['selected'],lock.get('native_members'))
    members={**lock.get('native_members',{}),**{x['resolved_path']:x for x in lock['selected'].values()}}
    result={'maps_sha256':sha(raw), 'maps_bytes':len(raw), 'images':{},'_raw_maps':raw}
    for name,segments in rows.items():
        path=Path(name);item=members[name]
        require(path.is_absolute() and path.is_file() and not any(p.is_symlink() for p in (path,*path.parents)), 'Resolved image path not regular')
        with path.open('rb') as f:
            before=os.fstat(f.fileno()); require(stat.S_ISREG(before.st_mode) and before.st_size<=MAX_ELF, 'Native image bound')
            h=hashlib.sha256()
            for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
            after=os.fstat(f.fileno())
        require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns), 'Native image changed')
        row=segments[0]
        require(row['inode']==after.st_ino and tuple(int(x,16) for x in row['dev'].split(':'))==(os.major(after.st_dev),os.minor(after.st_dev)), 'Mapped/native file identity mismatch')
        require(h.hexdigest()==item['sha256'] and after.st_size==item['bytes'], 'Native image payload mismatch')
        result['images'][name]={'path':str(path),'sha256':h.hexdigest(),'bytes':after.st_size,'segments':segments}
    return result

def write_snapshot(output,record,native):
    native=dict(native);raw=native.pop('_raw_maps')
    require(sha(raw)==native['maps_sha256'] and len(raw)==native['maps_bytes'],'Snapshot payload differs')
    name=f'{record["phase"]}-rank-{record["rank"]}-pid-{record["pid"]}'
    atomic_bytes(output/(name+'.maps'),raw,MAX_MAPS)
    record.update(native=native,maps_file=name+'.maps',status='NATIVE_MAP_PROOF')
    atomic(output/(name+'.json'),record)

def observation_error(output,error):
    try:atomic(output/f'error-pid-{os.getpid()}-{time.time_ns()}.json',
               {'status':'OBSERVATION_ERROR','pid':os.getpid(),'error':repr(error)[:2000]})
    except BaseException:pass

def snapshot_owned_process(lock,output,rank,owner):
    """Read only one externally birth-bound server rank after its benchmark.

    No liveness/process discovery here: a future reviewed case adapter supplies
    its retained ownership ledger, and both reads must match that birth.
    """
    require(type(rank)is int and 0<=rank<lock['tp'],'Invalid owned rank')
    require(identity(owner['pid'])==owner,'PID/birth changed before native snapshot')
    native=capture(lock,owner['pid'])
    require(identity(owner['pid'])==owner,'PID/birth changed during native snapshot')
    record={'schema_version':1,'run_id':lock['run_id'],'case':lock['case'],'nonce':lock['nonce'],
            'rank':rank,'nranks':lock['tp'],'at':time.time(),'phase':'after','added_native_calls':False,
            'native_contract_sha256':lock['native_contract_sha256'],'hook_sha256':sha(Path(__file__).read_bytes()),**owner}
    write_snapshot(output,record,native)

def stock_observation(lock):
    # No imports, CUDA initialization, native getters or loader operations.
    origins={}
    for name, expected in lock['source_origins'].items():
        module=sys.modules.get(name)
        require(module is not None and getattr(module,'__file__',None)==expected['path'], 'Natural source origin missing')
        path=Path(module.__file__)
        require(not path.is_symlink() and sha(path.read_bytes())==expected['sha256'], 'Natural source payload changed')
        origins[name]=dict(expected)
    torch=sys.modules.get('torch')
    require(torch is not None and torch.cuda.is_initialized(), 'Natural Torch CUDA state absent')
    return {'environment':{k:os.environ.get(k) for k in stock.EFFECTIVE}, 'source_origins':origins, 'device':torch.cuda.current_device()}

def wrap(module, lock, output, capture_fn=capture, identity_fn=identity):
    original=module.init
    require(not getattr(original,'_r7_native_proof',False), 'Duplicate natural hook')
    signature=inspect.signature(original)
    emitted=set()
    @functools.wraps(original)
    def observed(*args,**kwargs):
        # Original API errors propagate unchanged; observation runs only after success.
        entry=None
        try:entry=stock_observation(lock)
        except BaseException as error:observation_error(output,error)
        result=original(*args,**kwargs)
        try:
            arguments=signature.bind_partial(*args,**kwargs).arguments
            rank,nranks=arguments.get('rank'),arguments.get('nranks')
            require(type(rank)is int and type(nranks)is int and nranks==lock['tp'] and 0<=rank<nranks, 'Rank geometry differs')
            require(arguments.get('initializer_method')=='uid','Natural init is not UID')
            key=(rank,nranks)
            if key in emitted:return result
            record={'schema_version':1,'run_id':lock['run_id'],'case':lock['case'],
                'nonce':lock['nonce'],'rank':rank,'nranks':nranks,'at':time.time(),'phase':'startup',
                'natural_init_returned':True,'added_native_calls':False,'initializer_method':'uid',
                'native_contract_sha256':lock['native_contract_sha256'],'hook_sha256':sha(Path(__file__).read_bytes())}
            returned=stock_observation(lock)
            require(entry is not None, 'Natural entry observation missing')
            record['stock_evidence']={'entry_environment':entry['environment'],'return_environment':returned['environment'], 'source_origins':returned['source_origins'],'device':returned['device']}
            require(entry['source_origins']==returned['source_origins'] and entry['device']==returned['device'], 'Natural source/device changed')
            stock.startup_evidence(record,rank)
            record.update(identity_fn())
            write_snapshot(output,record,capture_fn(lock))
            emitted.add(key)
        except BaseException as error:
            # Observability failure cannot replace a successful native return.
            # Missing or error records fail the external pre-benchmark gate.
            observation_error(output,error)
        return result
    observed._r7_native_proof=True
    module.init=observed

class Loader:
    def __init__(self, original, lock, output): self.original,self.lock,self.output=original,lock,output
    def create_module(self,spec):
        return self.original.create_module(spec) if hasattr(self.original,'create_module') else None
    def exec_module(self,module):
        self.original.exec_module(module)
        try:
            source=Path(module.__file__)
            require(str(source)==self.lock['provider_source']['path'] and sha(source.read_bytes())==self.lock['provider_source']['sha256'],'Natural provider source drift')
            wrap(module,self.lock,self.output)
        except BaseException as error:observation_error(self.output,error)
    def __getattr__(self,name): return getattr(self.original,name)

class Finder(importlib.abc.MetaPathFinder):
    def __init__(self,lock,output): self.lock,self.output=lock,output
    def find_spec(self,fullname,path=None,target=None):
        if fullname!=TARGET: return None
        for finder in tuple(sys.meta_path):
            if finder is self or not hasattr(finder,'find_spec'): continue
            spec=finder.find_spec(fullname,path,target)
            if spec is not None:
                require(spec.loader is not None,'Natural module has no loader')
                spec.loader=Loader(spec.loader,self.lock,self.output)
                return spec
        return None

def install():
    name=os.environ.get('MEGAMOE_R7_NATIVE_PROOF_LOCK')
    if not name: return
    p=Path(name)
    require(p.is_absolute() and not any(x.is_symlink() for x in (p,*p.parents)), 'Unsafe hook lock')
    b=p.read_bytes();require(len(b)<=64*1024 and sha(b)==os.environ.get('MEGAMOE_R7_NATIVE_PROOF_SHA256'), 'Hook lock hash differs')
    lock=json.loads(b)
    require(lock.get('execution_status')=='REVIEWED_SUCCESSOR_REQUIRED', 'Prototype never installs against candidate/null bindings')
    require(lock.get('run_id')=='c2-w4a16-megamoe-autotune-20260921-recovery7', 'Wrong run identity')
    validate_lock(lock)
    output=Path(lock['proof_root'])
    require(output.is_absolute() and output.is_dir() and not any(x.is_symlink() for x in (output,*output.parents)), 'Proof root must preexist and be unlinked')
    require(TARGET not in sys.modules, 'Hook arrived after natural NVSHMEM import')
    sys.meta_path.insert(0,Finder(lock,output))

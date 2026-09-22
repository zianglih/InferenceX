"""Independent final CuTe first-case review; no auditor implementation is imported."""
import base64
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib,json,math,re,shlex,tarfile
from pathlib import Path

P=Path(__file__).resolve().parents[2]
CASE='8k1k/w4a16-cutedsl/tp4_conc256'
RUN='c2-w4a16-cutedsl-mem80-20260920'
D=P/'artifacts/measured'/RUN/CASE
E=P/'artifacts/cutedsl-20260920'
T=P/'artifacts/measured/c2-w4a16-cutedsl-mem80-20260920-completed-20260920T142743Z.tar.gz.verification.json'
J=P/'artifacts/cutedsl-first-case-independent-review.json'
MD=P/'artifacts/cutedsl-first-case-independent-review.md'
RAW=('benchmark.log','benchmark_command.sh','gpu_metrics.csv','gpu_metrics_identity.csv','metadata.json','nvidia-smi.txt','packages.json','result.json','server.log','server_command.sh','server_info.after.json','server_info.before.json','status.json')
RECEIPTS=('runtime-before.json','runtime-after.json','packages-before.txt','packages-after.txt','pip-check-before.txt','pip-check-after.txt','source-imports.json','setup-completed.json')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
iso=lambda x:datetime.fromtimestamp(x,timezone.utc).isoformat()
issues=[]
def need(ok,msg):
    if not ok:issues.append(msg)
def check(obj,expected,label):
    for k,v in expected.items():
        need(k in obj and type(obj[k]) is type(v) and obj[k]==v,f'{label}.{k}: expected {v!r}, got {obj.get(k)!r}')
def flags(path):
    tokens=shlex.split(path.read_text());out={}
    for n,t in enumerate(tokens):
        if t.startswith('--'):
            k,sep,v=t.partition('=')
            if not sep:v=tokens[n+1] if n+1<len(tokens) and not tokens[n+1].startswith('--') else True
            need(k not in out,f'duplicate command flag: {k}')
            out[k]=v
    return tokens,out
m,s,r=(read(D/x) for x in ('metadata.json','status.json','result.json'))
transfer=read(T)
need(transfer['cases']==[CASE] and transfer['run_id']==RUN and transfer['verified_files']==13,'Transfer case manifest mismatch')
raw_hash={n:sha(D/n) for n in RAW}
need(set(p.name for p in D.iterdir())==set(RAW),'Final raw file inventory differs from 13 expected files')
for n,h in raw_hash.items():
    need(transfer['files'].get(CASE+'/'+n)=={'bytes':(D/n).stat().st_size,'sha256':h},'Raw transfer hash/size mismatch: '+n)
packed=Path(transfer['transfer']);need(sha(packed)==transfer['transfer_sha256'],'Raw transfer archive SHA mismatch')
with tarfile.open(packed,'r:gz') as tar:
    tar_files={mem.name:mem for mem in tar.getmembers() if mem.isfile()}
    need(set(tar_files)=={RUN+'/'+CASE+'/'+n for n in RAW}|{'collector-manifest.json'},'Transfer tar file inventory mismatch')
    manifest=json.load(tar.extractfile(tar_files['collector-manifest.json']))
    need(manifest=={k:transfer[k] for k in ('run_id','cases','files')},'Embedded transfer manifest mismatch')
    for n,h in raw_hash.items():
        mem=tar_files.get(RUN+'/'+CASE+'/'+n)
        need(mem is not None,'Missing case file in transfer tar: '+n)
        if mem:need(hashlib.sha256(tar.extractfile(mem).read()).hexdigest()==h,'Transfer tar member SHA differs: '+n)
receipt_hash={n:sha(E/n) for n in RECEIPTS}
prior=read(P/'artifacts/cutedsl-20260920-runtime-only-audit.json')
need(prior['issue_count']==0,'Previously reviewed real setup environment has issues')
for n,h in receipt_hash.items():need(prior['transfer']['inventory'][n]['sha256']==h,'Sealed setup receipt changed since independent environment review: '+n)
source=read(E/'source-imports.json');seal=read(E/'setup-completed.json')
pins={'inferencex_commit':'3433a0c1169a6b162edf91c7ea193196c08a6386','sglang_commit':'50eeb742961908afa68f4f523a1a19c5de6eb0b3','flashinfer_commit':'f9dd3c10541e087b716772245a9d033499745048','mem_fraction_static':0.8,'model_revision':'53e0691e21895a3863a606dfd12910c69eba94ab','image':'lmsysorg/sglang:nightly-dev-cu13-20260918-20518d85'}
check(m,{**pins,'run_id':RUN,'status':'completed','backend':'w4a16_cutedsl','tp':4,'dp':4,'ep':4,'gpu_count':4,'concurrency':256,'server_max_running_requests':256,'scenario':'8k1k','isl':8192,'osl':1024,'num_prompts':2560,'num_warmups':512,'random_range_ratio':0.8,'parallel_topology':'dp-ep','prefill_cuda_graph_policy':'disabled','quality_evaluation':'not_run'},'metadata')
expectedheads={'sglang':pins['sglang_commit'],'flashinfer':pins['flashinfer_commit'],'inferencex':pins['inferencex_commit']}
need(source['source_heads']==seal['source_heads']==expectedheads,'Source pins disagree across real receipts')
need(source['source_tree_clean']==dict.fromkeys(expectedheads,True),'Recorded source clean flags mismatch')
check(s,{'status':'completed','exit_code':0,'expected':2560,'completed':2560,'failed':0},'status')
for label,obj in [('status',s),('result',r)]:
    check(obj['benchmark_outcome'],{'status':'passed','requested':2560,'completed':2560,'failed':0},label+'.benchmark_outcome')
    need(not any(obj.get('errors',[])),label+' contains request errors')
check(r,{'num_prompts':2560,'completed':2560,'max_concurrency':256,'model_id':'nvidia/GLM-5.2-NVFP4'},'result')
sums={}
for role in ('input','output'):
    vals=r[role+'_lens'];need(len(vals)==2560 and all(type(v)is int and v>0 for v in vals),'Invalid raw token array: '+role)
    sums[role]=sum(vals);need(sums[role]==r['total_'+role+'_tokens'],'Token sum mismatch: '+role)
start,end,duration=[r[k] for k in ('benchmark_start_time_unix','benchmark_end_time_unix','duration')]
# Wall-clock timestamps and the benchmark duration clock are sampled separately.
need(all(type(v)in(int,float) and math.isfinite(v) for v in (start,end,duration)) and duration>0 and abs(end-start-duration)<0.001,'Invalid measured duration/timestamps')
need(datetime.fromisoformat(seal['completed_at'])<datetime.fromisoformat(m['started_at']), 'Setup completed after case initialization')
need(datetime.fromisoformat(m['started_at']).timestamp()<start<end<datetime.fromisoformat(m['finished_at']).timestamp(),'Case interval does not contain measurement')
metrics={'output_throughput':sums['output']/duration,'total_token_throughput':sum(sums.values())/duration,'request_throughput':2560/duration}
for k,v in metrics.items():need(math.isclose(r[k],v,rel_tol=1e-12,abs_tol=1e-8),'Independent throughput disagrees: '+k)
median=r['median_tpot_ms'];need(type(median)in(int,float) and math.isfinite(median) and median>0,'Invalid reported median TPOT')
client=(D/'benchmark.log').read_bytes().decode().split('\n')
printed=[(i,re.search(r'Median TPOT \(ms\):\s+([0-9.]+)',l)) for i,l in enumerate(client,1) if 'Median TPOT (ms):' in l]
need(len(printed)==1 and abs(float(printed[0][1][1])-median)<=0.005000001,'Reported median does not match rounded log')
metrics.update(output_tokens_per_second_per_gpu=metrics['output_throughput']/4,reported_median_tpot_ms=median,interactivity_tokens_per_second_per_user=1000/median)

expected={'tp_size':4,'dp_size':4,'ep_size':4,'mem_fraction_static':0.8,'enable_dp_attention':True,'max_running_requests':256,'chunked_prefill_size':8192,'max_prefill_tokens':32768,
'dtype':'bfloat16','quantization':'modelopt_fp4','kv_cache_dtype':'fp8_e4m3','page_size':64,'attention_backend':'dsa','dsa_prefill_backend':'trtllm','dsa_decode_backend':'trtllm','dsa_topk_backend':'sgl-kernel',
'moe_runner_backend':'flashinfer_cutedsl','moe_a2a_backend':'none','speculative_moe_runner_backend':'flashinfer_trtllm','speculative_moe_a2a_backend':'none','speculative_draft_model_quantization':'modelopt_fp4','_speculative_draft_quantization_explicitly_set':False,
'speculative_algorithm':'EAGLE','speculative_num_steps':3,'speculative_eagle_topk':1,'speculative_num_draft_tokens':4,'speculative_accept_threshold_single':1.0,'speculative_accept_threshold_acc':1.0,'speculative_dsa_topk_backend':'sgl-kernel',
'cuda_graph_backend_prefill':'disabled','cuda_graph_max_bs_decode':256,'disable_cuda_graph':False,'disable_decode_cuda_graph':False,'disable_radix_cache':True,'disable_shared_experts_fusion':True,'enable_two_batch_overlap':False,'attn_cp_size':1,'enable_dp_attention_local_control_broadcast':False,'flashinfer_allreduce_fusion_backend':'auto','stream_interval':30,'model_path':m['model_path'],'served_model_name':m['model']}
buckets=list(range(1,9))+list(range(10,33,2))+list(range(40,65,4))+list(range(72,257,8))
state_checks={};infos={};al={}
for when in ('before','after'):
    info=read(D/f'server_info.{when}.json');infos[when]=info
    states=info.get('internal_states',[]);need(len(states)==4,when+' missing DP states')
    state_checks[when]=[];al[when]=[]
    for label,obj in [('top',info)]+[(f'dp[{i}]',x) for i,x in enumerate(states)]:
        check(obj,expected,when+'.'+label)
        check(obj['cuda_graph_config']['decode'],{'backend':'full','max_bs':256,'bs':buckets},when+'.'+label+'.decode_graph')
        check(obj['cuda_graph_config']['prefill'],{'backend':'disabled'},when+'.'+label+'.prefill_graph')
        if label!='top':
            check(obj,{'world_size':4,'effective_max_running_requests_per_dp':64},when+'.'+label)
            al[when].append(obj.get('avg_spec_accept_length'))
        state_checks[when].append({'object':label,'checked_settings':{k:obj.get(k) for k in expected},'effective_max_running_requests_per_dp':obj.get('effective_max_running_requests_per_dp'),'configured_graphs':obj['cuda_graph_config']})
tokens,serverflags=flags(D/'server_command.sh');commandenv=dict(t.split('=',1) for t in tokens[:tokens.index('python3')] if '=' in t)
base='/data/home/ziangli/inferencex-glm52-b300';firoot=base+'/sources/flashinfer-f9dd3c10';cache=base+'/caches/cutedsl-f9dd3c10-cute4.7.1-cu13'
env={'SGLANG_FLASHINFER_CUTEDSL_NVFP4_W4A16':'1','SGLANG_FLASHINFER_MOE_FUSED_FINALIZE':'0','SGLANG_FLASHINFER_NVFP4_PER_TOKEN_ACTIVATION':'0','SGLANG_FLASHINFER_MEGAMOE_COMBINE_DTYPE':'bf16','SGLANG_FLASHINFER_MEGAMOE_IN_KERNEL_FC2_REDUCE':'0','SGLANG_ENABLE_JIT_DEEPGEMM':'1','PYTHONNOUSERSITE':'1','CUDA_VISIBLE_DEVICES':'0,1,2,3','FLASHINFER_COMMIT':pins['flashinfer_commit'],'FLASHINFER_SOURCE_ROOT':firoot,'FLASHINFER_CUDA_ARCH_LIST':'10.3a','SGLANG_CACHE_DIR':cache+'/sglang','FLASHINFER_WORKSPACE_BASE':cache,'PYTHONPATH':base+'/sources/sglang/python:'+firoot+':'+base+'/sources/inferencex-cutedsl-20260920'}
for label,obj in [('metadata.environment',m['environment']),('server_command.env',commandenv)]:
    check(obj,env,label)
    for k in ('FLASHINFER_MOE_EP_KNOB_CACHE','SGLANG_ENABLE_SPEC_V2','SGLANG_SIMULATE_ACC_LEN','SGLANG_SIMULATE_ACC_METHOD','SGLANG_SIMULATE_ACC_TOKEN_MODE','FLASHINFER_DISABLE_VERSION_CHECK','FLASHINFER_CUBIN_CHECKSUM_DISABLED','FLASHINFER_NO_DOWNLOAD','FLASHINFER_DISABLE_JIT'):
        need(k not in obj,f'Unexpected environment override: {label}.{k}')
check(serverflags,{'--tensor-parallel-size':'4','--data-parallel-size':'4','--expert-parallel-size':'4','--max-running-requests':'256','--enable-dp-attention':True,'--chunked-prefill-size':'32768','--max-prefill-tokens':'32768','--cuda-graph-max-bs-decode':'256','--cuda-graph-backend-prefill':'disabled','--moe-runner-backend':'flashinfer_cutedsl','--moe-a2a-backend':'none','--speculative-moe-runner-backend':'flashinfer_trtllm','--speculative-moe-a2a-backend':'none','--quantization':'modelopt_fp4','--dtype':'bfloat16','--kv-cache-dtype':'fp8_e4m3','--attention-backend':'dsa','--dsa-prefill-backend':'trtllm','--dsa-decode-backend':'trtllm','--speculative-algorithm':'EAGLE','--speculative-num-steps':'3','--speculative-eagle-topk':'1','--speculative-num-draft-tokens':'4','--disable-radix-cache':True,'--stream-interval':'30'},'server_command')
need(float(serverflags['--mem-fraction-static'])==0.8,'Command memory mismatch');need('--speculative-draft-model-quantization' not in serverflags,'Explicit draft quantization override')
_,clientflags=flags(D/'benchmark_command.sh')
check(clientflags,{'--model':m['model'],'--tokenizer':m['model_path'],'--backend':'vllm','--input-len':'8192','--output-len':'1024','--random-range-ratio':'0.8','--num-prompts':'2560','--max-concurrency':'256','--use-chat-template':True},'benchmark_command')
need('--num-warmups 512' in '\n'.join(client) and '--request-rate inf' in '\n'.join(client) and '--ignore-eos' in '\n'.join(client),'Expanded client command differs from requested workload')
packages={re.sub(r'[-_.]+','-',p['name']).lower():p['version'] for p in read(D/'packages.json')}
post=read(E/'runtime-after.json')
for name,version in post['versions'].items():need(packages.get(name)==version,'Package differs from sealed runtime: '+name)
for line in (E/'packages-after.txt').read_text().splitlines():
    if line and not line.startswith(('#','-e ')) and '==' in line:
        name,version=line.split('==',1);need(packages.get(re.sub(r'[-_.]+','-',name).lower())==version,'Freeze version mismatch: '+name)
check(m,{'flashinfer_source_root':firoot,'flashinfer_import_path':source['imports']['flashinfer'],'flashinfer_import_version':'0.7.0'},'metadata')
need(m['cute_dsl_compiler']['version']=='4.7.1' and set(m['cute_dsl_compiler']['library_versions'].values())=={'4.7.1'},'CuTe compiler provenance mismatch')
need(m['cute_dsl_compiler']['import_paths']['cutlass']==source['imports']['cutlass'],'CuTe import differs from sealed setup')
need('NVIDIA B300' in (D/'nvidia-smi.txt').read_text(),'Missing B300 identity')

# Independent phase classifier using physical LF lines, preserving progress CRs.
counts=defaultdict(Counter);graph={'prefill':defaultdict(Counter),'decode':defaultdict(Counter)};evidence=[];captures=[];timestamp=None;resolution=0
patterns={'severity_tagged_warning':r'\bWARNING\b|(?:User|Future|Deprecation|Runtime)Warning:|\[W\d','allocator_oom_warning':r'memory allocation failed with OOM','oom_exception':r'OutOfMemoryError|CUDA out of memory','error_label':r'ERROR:','traceback':r'Traceback \(most recent call last\):','late_load_advisory':r'Pre-load it','sigterm':r'SIGTERM received','sigquit':r'SIGQUIT received|Triggering SIGQUIT','child_exit_minus15':r'exit code -15','fatal_runtime':r'CUDA error:|illegal memory access|device-side assert|NCCL error|RuntimeError:', 'autotune_cache_disagreement':r'per-rank caches disagree','cutedsl_w4a16_autotune':r'Tuning CuteDslMoEWrapper::run::W4A16','trtllm_bf16_autotune':r'Tuning flashinfer::trtllm_bf16_moe'}
for n,line in enumerate((D/'server.log').read_bytes().decode(errors='replace').split('\n'),1):
    match=re.search(r'\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)(?:\.(\d+))?',line)
    if match:
        timestamp=datetime.strptime(match[1],'%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp()
        resolution=1.0
        if match[2]:timestamp+=float('0.'+match[2]);resolution=10**(-len(match[2]))
    if timestamp is None:phase='untimed'
    elif timestamp+resolution<=start:phase='before'
    elif timestamp>end:phase='after'
    elif timestamp>=start and timestamp+resolution<=end:phase='measured'
    else:phase='boundary'
    tags=[k for k,pattern in patterns.items() if re.search(pattern,line)]
    for tag in tags:counts[tag][phase]+=1
    if tags:
        evidence.append({'line':n,'time_utc':iso(timestamp) if timestamp is not None else None,'phase':phase,'tags':tags,'text':line[:900]})
    g=re.search(r'(Prefill|Decode) batch,.*cuda graph: (True|False)',line)
    if g:graph[g[1].lower()][phase][g[2]]+=1
    sizes=list(map(int,re.findall(r'Capturing batches \(bs=(\d+)',line)))
    if sizes:captures.append({'line':n,'phase':phase,'sizes':sorted(set(sizes)),'max':max(sizes)})
actualsizes=sorted({v for item in captures for v in item['sizes']})
need(actualsizes==[v for v in buckets if v<=64],'Actual capture log sizes do not match DP64 pool')
need(all(x['phase']=='before' for x in captures),'Capture occurred outside initialization/warmup phase')
need(not any(v.get('True',0) for v in graph['prefill'].values()),'Unexpected prefill graph replay')
need(graph['decode'].get('measured',{}).get('True',0)>0,'No measured decode replay evidence')
for tag in ('allocator_oom_warning','oom_exception','error_label','traceback','fatal_runtime'):
    need(not sum(counts[tag].values()),'Unexpected log diagnostic requiring review: '+tag)
need(sum(counts['cutedsl_w4a16_autotune'].values())>0,'Missing CuTe W4A16 autotune evidence')
need(sum(counts['trtllm_bf16_autotune'].values())>0,'Missing TRT BF16 autotune evidence')
normalized_keys=('tp_size','dp_size','ep_size','enable_dp_attention','max_running_requests','chunked_prefill_size','mem_fraction_static','moe_runner_backend','moe_a2a_backend','speculative_moe_runner_backend','speculative_moe_a2a_backend','speculative_draft_model_quantization','_speculative_draft_quantization_explicitly_set','cuda_graph_backend_prefill')
normalized={k:infos['after'][k] for k in normalized_keys};normalized.update(configured_decode_max_bs=256,actual_capture_max=max(actualsizes))
report={'schema_version':1,'review_status':'passed' if not issues else 'failed','issue_count':len(issues),'issues':issues,
 'created_at':datetime.now(timezone.utc).isoformat(),'case':CASE,'run_id':RUN,'raw_file_sha256':raw_hash,'runtime_receipt_sha256':receipt_hash,'pins':pins,'normalized_settings':normalized,
 'independent_review_report':{'path':MD.name,'sha256':sha(MD) if MD.exists() else None},'measured_counts':{'requested':2560,'completed':r['completed'],'failed':s['failed'],'exit_code':s['exit_code']},
 'measurement':{'start_utc':iso(start),'end_utc':iso(end),'duration_seconds':duration,'timestamp_difference_seconds':end-start,'input_tokens':sums['input'],'output_tokens':sums['output'],**metrics,
 'median_tpot_validation':'Finite positive reported aggregate agrees with benchmark.log rounded107.48; raw per-request latency/TTFT samples unavailable, so no independent median reconstruction'},
 'independent_state_checks':state_checks,'environment_settings':env,'actual_capture_evidence':captures,
 'graph_log_counts_by_phase':{k:{p:dict(c) for p,c in phases.items()} for k,phases in graph.items()},
 'diagnostic_counts_by_phase':{k:dict(v) for k,v in counts.items()},'diagnostic_evidence':evidence,
 'cumulative_acceptance_length':{'before':al['before'],'after':al['after'],'scope':'Lifetime cumulative per returned DP state, includes warmup; no measured-only or weighted aggregate inferred'},
 'transfer_identity':{'verification_path':str(T),'verification_sha256':sha(T),'archive_sha256':sha(packed)},
 'setup_review_identity':{'path':'cutedsl-20260920-independent-environment-review.md','sha256':sha(P/'artifacts/cutedsl-20260920-independent-environment-review.md'),'setup_completed_at':seal['completed_at']},
 'review_scope':'First real completed TP4/C256 case only; no TP8 calibration or full-matrix performance conclusion',
 'limitations':['Warmup requested512 and completion log are present, but individual warmup responses are not retained; do not claim independently proven512/512 warmup successes.',
 'No model-quality evaluation, repeated-run confidence interval or latency-SLO qualification was performed.',
 'Autotune operation names corroborate CuTe W4A16 and TRT native-BF16 dispatch; not an exhaustive per-layer kernel profiler trace.',
 'The .6.18 FLASHINFER_VERSION image label differs from selected source .7.0/f9dd3. Setup pip-check remains nonclean with known dependency metadata conflicts.',
 'Phase counts are physical-log observations; untimed lines inherit prior timestamps and whole-second boundaries are explicit. Teardown diagnostics are separate from measured outcomes.',
 'Auditor pending flags remain unchanged until parent binds this completed review; TP8/C4 requires separate calibration.']}
J.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'issues':issues,'measurement':report['measurement'],'log_counts':report['diagnostic_counts_by_phase'],'graphs':report['graph_log_counts_by_phase'],'capture_sizes':actualsizes,'capture_line_numbers':[x['line'] for x in captures],'AL_after':al['after'],'evidence':[{k:x[k] for k in ('line','time_utc','phase','tags','text')} for x in evidence if any(t in x['tags'] for t in ('sigterm','sigquit','child_exit_minus15','autotune_cache_disagreement'))]},indent=2))

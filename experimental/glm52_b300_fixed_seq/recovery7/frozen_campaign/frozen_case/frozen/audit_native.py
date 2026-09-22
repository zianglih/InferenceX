"""Pure additional native-evidence gate; legacy arithmetic/14-raw audit remains required.

No discovery, remote access, package import, dispatch or final acceptance CLI.
The future reviewed adapter must invoke the existing base auditor and establish
process-owner births independently before supplying these records.
"""
import hashlib
import stock
from producer import RUN_ID, OLD_RUN_ID, matrix, require
from natural_proof import selected_maps, validate_lock

RAW14={'autotune_cache.before.json','benchmark.log','benchmark_command.sh','gpu_metrics.csv',
       'gpu_metrics_identity.csv','metadata.json','nvidia-smi.txt','packages.json','result.json',
       'server.log','server_command.sh','server_info.after.json','server_info.before.json','status.json'}

def snapshot(record,raw,lock,owners,phase):
    validate_lock(lock)
    require(record['status']=='NATIVE_MAP_PROOF' and record['phase']==phase,'Native observation failed/wrong phase')
    require(record['run_id']==RUN_ID and record['case']==lock['case'] and record['nonce']==lock['nonce'], 'Native case binding differs')
    rank=record['rank'];require(type(rank)is int and 0<=rank<lock['tp'] and record['nranks']==lock['tp'],'Native rank geometry')
    require({'pid':record['pid'],'starttime':record['starttime']}==owners[rank],'Native PID/birth ownership differs')
    require(record['native_contract_sha256']==lock['native_contract_sha256'] and record['added_native_calls'] is False,'Native contract/call scope differs')
    require(record['hook_sha256']==lock['hook_sha256'],'Unreviewed native evidence helper')
    if phase=='startup':
        stock.startup_evidence(record,rank)
        require(record['natural_init_returned'] is True and record['initializer_method']=='uid','Missing natural UID init return')
    native=record['native'];require(hashlib.sha256(raw).hexdigest()==native['maps_sha256'] and len(raw)==native['maps_bytes'],'Raw map SHA differs')
    rows=selected_maps(raw,lock['selected'],lock['native_members'])
    require(set(rows)==set(native['images']),'Mapped native file inventory differs')
    declared={**lock['native_members'],**{x['resolved_path']:x for x in lock['selected'].values()}}
    for path,segments in rows.items():
        item=native['images'][path]
        require(item['path']==path and item['segments']==segments,'Map summary differs')
        require(item['bytes']==declared[path]['bytes'] and item['sha256']==declared[path]['sha256'],'Mapped native payload differs')
    return rank

def audit_extension(case,base_report,raw14_hashes,native_lock,startup,after,owners,window,errors):
    """Input snapshots are [(record, raw_maps_bytes), ...], from sealed sibling evidence."""
    require(case in matrix() and native_lock['case']==case['case'] and native_lock['tp']==case['tp'],'Unknown case')
    require(base_report['case']==case['case'] and base_report['issues']==[],'Existing case audit not clean')
    require(base_report['completed']==case['requests'] and base_report['failed']==0 and base_report['exit_code']==0,'Original completion gate failed')
    require(set(raw14_hashes)==RAW14 and raw14_hashes==base_report['raw_file_sha256'],'Exactly original raw14 required')
    require(errors==[] and set(owners)==set(range(case['tp'])),'Native observation/ownership incomplete')
    require(len({v['pid'] for v in owners.values()})==case['tp'],'Rank ownership PID duplicated')
    require(window['start']<=window['end'],'Measured interval invalid')
    checked={}
    for phase,records in [('startup',startup),('after',after)]:
        ranks=[];checked[phase]={}
        for record,raw in records:
            rank=snapshot(record,raw,native_lock,owners,phase)
            require(rank not in ranks,'Duplicate native rank')
            require(record['at']<=window['start'] if phase=='startup' else record['at']>=window['end'],'Native proof on wrong side of benchmark')
            ranks.append(rank);checked[phase][rank]=record
        require(sorted(ranks)==list(range(case['tp'])),'Missing per-case native rank')
    for rank in owners:
        for selected in native_lock['selected'].values():
            path=selected['resolved_path']
            before=checked['startup'][rank]['native']['images'][path]
            end=checked['after'][rank]['native']['images'][path]
            require(before==end,'Selected native image/maps changed during case')
    return {'status':'NATIVE_EXTENSION_VALIDATED_ONLY','run_id':RUN_ID,'case':case['case'],
            'rank_count':case['tp'],'native_variant':'original-wheel-sglang-no-proxy-defaults',
            'raw14_unchanged':True,'startup_outside_measured_window':True,
            'first_case_independent_calibration_still_required':True,
            'source_runtime_and_archive_acceptance_still_required':True}

def provenance_rows(new_case_reports,old_case_reports):
    """Truthful mixed provenance; not a numerical/completion acceptance shortcut."""
    require({x['case'] for x in new_case_reports}=={x['case'] for x in matrix()} and len(new_case_reports)==14,'Remaining matrix incomplete')
    require({x['case'] for x in old_case_reports}=={'8k1k/w4a16-megamoe/tp4_conc256','8k1k/w4a16-megamoe/tp4_conc4'} and len(old_case_reports)==2,'Reuse coordinates differ')
    return [{'run_id':OLD_RUN_ID,'case':x['case'],'native_variant':'original-wheel; not patched'} for x in old_case_reports]+[
        {'run_id':RUN_ID,'case':x['case'],'native_variant':'original-wheel-sglang-no-proxy-defaults'} for x in new_case_reports]

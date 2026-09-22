#!/usr/bin/env python3
"""Reproduce the exported four-frontier figures from their preserved raw files."""
from pathlib import Path
import argparse, hashlib, json, os, sys


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def desc(path):
    need(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)), 'Regular unlinked file required')
    a=path.stat()
    with path.open('rb') as f:
        digest=hashlib.file_digest(f,'sha256').hexdigest();z=os.fstat(f.fileno())
    need(all(getattr(a,k)==getattr(z,k)==getattr(path.stat(),k) for k in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')), 'File changed')
    return {'bytes':a.st_size,'sha256':digest}


def validate(input_path):
    here=Path(__file__).resolve().parent
    input_path=input_path.absolute();root=input_path.parent.parent
    need(input_path==root/'figures/pareto.json' and here==root/'plot-source', 'Expected exported figure/source locations')
    value=read(input_path);source=value['plot_source']
    need(set(source)=={'manifest','bytes','sha256'} and source['manifest']=='../plot-source/source-manifest.json', 'Exact exported source-manifest path required')
    need(desc(here/'source-manifest.json')=={k:source[k] for k in ('bytes','sha256')}, 'Figure-bound source-manifest SHA differs')
    manifest=read(here/'source-manifest.json')
    need(set(manifest['files'])=={'replot.py','plot_group.py','plot_pareto.py','summarize.py'}, 'Four exact source files required')
    for name,d in manifest['files'].items():need(desc(here/name)==d, 'Exported source SHA differs')
    sys.path.insert(0,str(here))
    import plot_pareto as plot
    import plot_group as grouped
    points=value['points']
    need(value['main_observations']==48 and value['original_reference_observations']==16 and len(points)==64, 'Incomplete final observation set')
    files={};raw_bindings=value['raw_bindings']
    for p in points:
        paths={}
        for field in ('metadata_file','result_file'):
            rel=p[field];parts=Path(rel).parts
            need(len(parts)>3 and parts[:2] in (('..','runs'),('..','regression-reference')) and '..' not in parts[1:], 'Raw source path escapes export')
            path=root.joinpath(*parts[1:]);d=desc(path)
            need(d==raw_bindings[rel], 'Exported raw payload SHA differs');files[rel]=d;paths[field]=path
        row=plot.read_case(paths['metadata_file']);need(row['included'], 'Original strict point reader rejected exported raw')
        row['case_id']=p['case_id'];actual=plot.point_from_case(row)
        need(all(actual[k]==v for k,v in p.items() if k in actual and k not in paths), 'Recomputed exported metrics/source identity differ')
        need(paths['result_file']==paths['metadata_file'].with_name('result.json') and p['inferencex_commit']==row['metadata']['inferencex_commit'], 'Result/recipe source differs')
    need(files==raw_bindings and len(files)==128, 'Missing or extra raw metadata/result payload')
    main=[p for p in points if p['plot_series']!='original_mega'];original=[p for p in points if p['plot_series']=='original_mega']
    need(grouped.four_series(main,original)==points, 'Four-series source order differs')
    identity=value['original_id_source'];parts=Path(identity['path']).parts
    need(parts[:2]==('..','regression-reference') and '..' not in parts[1:], 'Original-ID source outside reference scope')
    identity_path=root.joinpath(*parts[1:])
    need(desc(identity_path)=={k:identity[k] for k in ('bytes','sha256')}, 'Original-ID source SHA differs')
    historical=[p for p in read(identity_path)['points'] if p['backend']=='w4a16_megamoe']
    key=lambda p:(p['scenario'],p['tp'],p['concurrency'])
    need(len(historical)==16 and {key(p):p['case_id'] for p in historical}=={key(p):p['case_id'] for p in original}, 'Historical display IDs rewritten')
    return value,files,plot,grouped


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();output=a.output.absolute();input_path=a.input.absolute();root=input_path.parent.parent
    need(not output.exists() and output.parent.is_dir() and not any(p.is_symlink() for p in (output,*output.parents)), 'Exclusive unlinked output required')
    need(output!=root and output not in root.parents and root not in output.parents, 'Output must not overlap preserved export')
    before=desc(input_path);value,files,plot,grouped=validate(input_path);output.mkdir()
    try:
        charts=[grouped.draw([p for p in value['points'] if p['scenario']==scenario],output,scenario,mode) for mode in plot.MODES for scenario in plot.SCENARIOS]
        need(charts==value['charts'], 'Reproduced frontier identities differ')
        again,after,_,_=validate(input_path);need(before==desc(input_path) and again==value and after==files, 'Export changed during rendering')
        receipt={'status':'EXPORTED_RAW_METRICS_AND_FOUR_FRONTIERS_REPRODUCED','issues':[],'input':before,'raw_files':files,'charts':charts,'new_measurements':False,'pixel_byte_identity_claim':False}
        (output/'replot-verification.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    except BaseException as e:
        (output/'FAILED.json').write_text(json.dumps({'status':'FAILED_PREFIX_PRESERVED','error':repr(e)},indent=2)+'\n');raise


if __name__=='__main__':main()

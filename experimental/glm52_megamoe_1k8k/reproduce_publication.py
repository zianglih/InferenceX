#!/usr/bin/env python3
"""Rebuild the published GLM-5.2 R2 table coordinates and four frontiers.

Reads only repository-contained selected raw payloads. It does not reproduce the
full case/terminal acceptance audit, which also needs the preserved full logs.
No remote commands, benchmark launch, source mutation or archive deletion.
"""
import argparse
import csv
from decimal import Decimal, localcontext
import hashlib
import json
import os
from pathlib import Path

MANIFEST_SHA = 'cdc4b6b260a70fe393c1e0c9ff605ff500b76c572e7c679e7840fb2586a54955'
GROUPS = (('w4a4', 4), ('w4a16', 4), ('w4a4', 8), ('w4a16', 8))
CS = (4, 8, 16, 32, 64, 128)


def desc(path):
    assert path.is_file() and not path.is_symlink(), path
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def read(path, decimal=False):
    return json.loads(path.read_text(), parse_float=Decimal) if decimal else json.loads(path.read_text())


def write_json(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')


def write_csv(path, rows):
    with path.open('x', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(dict.fromkeys(k for r in rows for k in r)))
        w.writeheader()
        w.writerows(rows)


def pareto_frontier(rows):
    return sorted([r for r in rows if not any(q['interactivity_tok_s_user'] >= r['interactivity_tok_s_user'] and q['output_tok_s_gpu'] >= r['output_tok_s_gpu'] and (q['interactivity_tok_s_user'] > r['interactivity_tok_s_user'] or q['output_tok_s_gpu'] > r['output_tok_s_gpu']) for q in rows)], key=lambda r: r['interactivity_tok_s_user'])


def load_selected(root):
    assert desc(root / 'FILES.json')['sha256'] == MANIFEST_SHA
    published = read(root / 'FILES.json')
    for name, wanted in published.items():
        rel = Path(name)
        assert not rel.is_absolute() and '..' not in rel.parts
        assert desc(root / rel) == wanted, name
    config = read(root / 'raw/config.json')
    assert config['run_id'] == 'glm52-megamoe-1k8k-20260924-r2-all24'
    rows, metrics, ordered = [], {}, {}
    for p, tp in GROUPS:
        for c in CS:
            cid = f'{p}-tp{tp}-ep{tp}-dp{tp}-c{c}'
            d = root / 'raw' / cid
            manifest = read(d / 'manifest.json')
            for path in d.iterdir():
                if path.name != 'manifest.json':
                    assert desc(path) == manifest['files'][path.name]
            raw, raw_decimal = read(d / 'result.json'), read(d / 'result.json', True)
            settings, request, exit = read(d / 'settings.json'), read(d / 'requested-lengths.json'), read(d / 'exit.json')
            case = settings['case']
            assert case['precision'] == p and case['tp'] == case['ep'] == case['dp'] == tp and case['concurrency'] == c
            assert settings['config'] == config and (settings['nominal_input'], settings['nominal_output'], settings['ratio']) == (1024, 8192, 0.8)
            assert raw['completed'] == raw['num_prompts'] == 10*c and raw['max_concurrency'] == c and raw['request_rate'] == 'inf'
            assert raw['benchmark_outcome']['status'] == 'passed' and raw['benchmark_outcome']['failed'] == 0
            assert exit['status'] == 'completed' and not exit.get('error') and not exit.get('postflight_error')
            for role in ('server', 'benchmark'):
                cl = exit['cleanup'][role]
                assert not cl.get('errors') and not cl.get('remaining') and not cl.get('error')
            assert exit['cleanup']['benchmark']['waited_returncode'] == 0
            lengths = (raw['input_lens'], raw['output_lens'])
            assert lengths == (request['input_lens'], request['output_lens'])
            if c in ordered:
                assert lengths == ordered[c]
            ordered[c] = lengths
            assert sum(raw['input_lens']) == raw['total_input_tokens'] and sum(raw['output_lens']) == raw['total_output_tokens']
            assert len(raw['output_lens']) == 10*c and all(6553 <= n <= 8192 for n in raw['output_lens'])
            duration = raw['duration']
            rate = raw['total_output_tokens'] / duration
            assert abs(rate - raw['output_throughput']) / rate < 1e-9
            row = {'case_id': cid, 'precision': p, 'tp': tp, 'ep': tp, 'dp': tp, 'concurrency': c, 'completed': raw['completed'], 'duration_s': duration,
                   'input_tokens': raw['total_input_tokens'], 'output_tokens': raw['total_output_tokens'], 'output_tok_s': rate, 'output_tok_s_gpu': rate/tp,
                   'interactivity_tok_s_user': 1000/raw['median_tpot_ms'], 'result_sha256': manifest['files']['result.json']['sha256'],
                   'case_manifest_sha256': desc(d/'manifest.json')['sha256'], 'sglang_commit': config['sglang_commit'], 'flashinfer_commit': config['flashinfer_commit'], 'image': config['image']}
            row.update({k: v for k, v in raw.items() if k.endswith('_ms')})
            rows.append(row)
            with localcontext() as ctx:
                ctx.prec = 50
                r = Decimal(raw_decimal['total_output_tokens']) / raw_decimal['duration']
                m = {'duration_s': raw_decimal['duration'], 'output_tok_s': r, 'output_tok_s_gpu': r/tp, 'interactivity_tok_s_user': Decimal(1000)/raw_decimal['median_tpot_ms']}
                m.update({k: v for k, v in raw_decimal.items() if k.endswith('_ms')})
                assert len(m) == 28
                metrics[cid] = m
    assert rows == read(root/'raw-metrics.json') and len(rows) == 24 and sum(r['completed'] for r in rows) == 10080
    comparisons = []
    with localcontext() as ctx:
        ctx.prec = 50
        for kind, fixed_values in (('precision', (4,8)), ('topology', ('w4a4','w4a16'))):
            for fixed in fixed_values:
                for c in CS:
                    if kind == 'precision':
                        a,b = f'w4a4-tp{fixed}-ep{fixed}-dp{fixed}-c{c}',f'w4a16-tp{fixed}-ep{fixed}-dp{fixed}-c{c}'
                        label=f'TP=EP=DP{fixed}: W4A16 / W4A4 - 1'
                    else:
                        a,b=f'{fixed}-tp4-ep4-dp4-c{c}',f'{fixed}-tp8-ep8-dp8-c{c}'
                        label=f'{fixed.upper()}: TP8 / TP4 - 1'
                    for metric, va in metrics[a].items():
                        vb=metrics[b][metric]
                        comparisons.append({'pair_id': f'{kind}-{fixed}-c{c}', 'kind': kind, 'label': label, 'concurrency': c, 'baseline_case': a,
                                            'comparison_case': b, 'metric': metric, 'baseline_value': str(va), 'comparison_value': str(vb),
                                            'absolute_change': str(vb-va), 'percent_change': str((vb/va-1)*100)})
    assert comparisons == read(root/'paired-comparisons.json')['rows'] and len(comparisons) == 672
    return rows, comparisons


def plot(rows, out):
    released = True
    os.environ.setdefault("MPLCONFIGDIR", str(out / ".matplotlib"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "svg.fonttype": "none", "svg.hashsalt": "glm52-r2-four-frontiers"})
    fig, ax = plt.subplots(figsize=(16, 10))
    fig.subplots_adjust(left=.09, right=.97, bottom=.20, top=.86)
    colors = {"w4a4": "#009E73", "w4a16": "#E69F00"}
    plot_points = []
    for p, tp in GROUPS:
        color = colors[p]
        marker, line_style = ("o", "-") if tp == 4 else ("^", "--")
        group = [r for r in rows if (r["precision"], r["tp"]) == (p, tp)]
        frontier = pareto_frontier(group)
        ax.plot([r["interactivity_tok_s_user"] for r in frontier], [r["output_tok_s_gpu"] for r in frontier], color=color, linewidth=1.9,
                label=f"MegaMoE {p.upper()} | TP=EP=DP={tp}", linestyle=line_style, marker=marker, markersize=7, markeredgecolor="white", markeredgewidth=.7, zorder=2)
        ax.scatter([r["interactivity_tok_s_user"] for r in group], [r["output_tok_s_gpu"] for r in group], color=color, marker=marker,
                   s=63, edgecolor="white", linewidth=.7, zorder=4)
        for r in group:
            dx, dy = ((-10, 12) if p == "w4a4" else (10, -17))
            ha = "right" if dx < 0 else "left"
            if r["concurrency"] == 128 and tp == 8:
                dx, dy = ((-22, 23) if p == "w4a4" else (20, -25))
                ha = "right" if dx < 0 else "left"
            if tp == 4 and p == "w4a4" and r["concurrency"] == 4:
                dx, dy, ha = -10, 36, "right"
            if tp == 8 and p == "w4a16" and r["concurrency"] == 4:
                dx, dy, ha = 10, 20, "left"
            ax.annotate(f"C{r['concurrency']}", (r["interactivity_tok_s_user"], r["output_tok_s_gpu"]), xytext=(dx, dy), textcoords="offset points",
                        fontsize=10, fontweight="medium", color=color, ha=ha, va="center", bbox={"facecolor": "white", "edgecolor": "none", "alpha": .82, "pad": .5}, arrowprops={"arrowstyle": "-", "color": color, "lw": .6}, zorder=5)
            plot_points.append({"case_id": r["case_id"], "label": f"C{r['concurrency']}", "x": r["interactivity_tok_s_user"], "y": r["output_tok_s_gpu"]})
    ax.set(xlabel="Interactivity = 1,000 / saved median TPOT (tokens/s/user)", ylabel="Whole-interval output throughput (tokens/s/GPU)", xlim=(58, 207), ylim=(0, 2400))
    ax.grid(alpha=.20)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", frameon=True, framealpha=.96, fontsize=11)
    fig.suptitle("GLM-5.2 MegaMoE | W4A4 versus W4A16 | B300", y=.965, fontsize=20, weight="bold")
    fig.text(.5, .915, "Nominal 1,024 input / 8,192 output | ratio 0.8 | 24 fresh points | 10,080 measured requests", ha="center", fontsize=12)
    fig.text(.5, .115, "Each line connects nondominated points within its own precision/topology group; all 24 points are shown.", ha="center", fontsize=10)
    fig.text(.5, .082, "EAGLE: steps 3 / top-k 1 / draft tokens 4 | Draft MoE: BF16 TRTLLM / none | NextN model quantization: modelopt_fp4 (NVFP4)", ha="center", fontsize=10)
    fig.text(.5, .05, "SG 16c1b8638b46 | FI 19e8aebb5416 | shared compiled caches; fresh server and four isolated tactic namespaces", ha="center", fontsize=10)
    if not released:
        fig.text(.5, .015, "DRAFT - publication input release pending; no publication or cleanup approval", ha="center", color="#A32121", fontsize=10, weight="bold")
    else:
        fig.text(.5, .015, "Whole measured interval; not separately timed decode. Single sequential run; no causal or numerical-equivalence claim.", ha="center", color="#555555", fontsize=9)
    fig.savefig(out / "pareto.png", dpi=180)
    fig.savefig(out / "pareto.svg", metadata={"Date": None})
    plt.close(fig)
    write_json(out / "plot-points.json", plot_points)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--published-dir', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    root, out = args.published_dir.resolve(), args.output.resolve()
    rows, comparisons = load_selected(root)
    out.mkdir(parents=True, exist_ok=False)
    write_json(out/'raw-metrics.json', rows)
    write_csv(out/'raw-metrics.csv', rows)
    write_json(out/'paired-comparisons.json', {'status':'ROOT_RELEASE_ACCEPTED','decimal_precision':50,'pairs':24,'metrics_per_pair':28,'rows':comparisons})
    write_csv(out/'paired-comparisons.csv', comparisons)
    plot(rows, out)
    # Verify mathematical outputs byte-for-byte; graphical byte equality depends
    # on matching Matplotlib/font/runtime versions, so report it separately.
    exact = {}
    for name in ('raw-metrics.json','raw-metrics.csv','paired-comparisons.json','paired-comparisons.csv','plot-points.json'):
        assert desc(out/name) == desc(root/name), name
        exact[name] = desc(out/name)
    figures = {name: {'original':desc(root/name),'reproduced':desc(out/name),'identical':desc(root/name)==desc(out/name)} for name in ('pareto.png','pareto.svg')}
    result = {'status':'PASS','points':24,'successful_measured_requests':10080,'failed_measured_requests':0,'pairs':24,'metrics_per_pair':28,'published_manifest_sha256':MANIFEST_SHA,
              'raw_and_derived_outputs_exact':exact,'figures':figures,'scope':'Reconstruction from selected published raw. Does not replace the full preserved case logs/native/tactic or exact terminal acceptance audit.'}
    write_json(out/'REPRODUCED.json',result)
    print(json.dumps({'status':'PASS','points':24,'metrics':672,'output':str(out),'figures_identical':all(r['identical'] for r in figures.values())}))


if __name__ == '__main__':
    main()

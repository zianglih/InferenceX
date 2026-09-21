"""Post-artifacts.finish producer join; source namespaces remain unchanged."""

import os
from pathlib import Path
import re
import shlex
import sys
import math
from datetime import datetime
import core

sys.path.insert(0, str(core.HERE / "frozen_campaign"))
import campaign

adapter = campaign.case_adapter
need = core.need


def native_manifest(root, selected):
    files, links = {}, {}
    core.safe(root)
    allowed_dirs = {'proof'}
    allowed_top = {
        "native-contract.json",
        "proxy-disabled.json",
        "launch-intent.json",
        "server-watch.json",
        "startup-seal.json",
        "after-seal.json",
        "exit.json",
        "readiness.log",
        "readiness-command.json",
        "server-info-before-command.json",
        "server-info-after-command.json",
        "snapshot-autotune.log",
        "snapshot-autotune-command.json",
        "benchmark-command.json",
    }
    for folder, dirs, names in os.walk(root, followlinks=False):
        for d in dirs:
            need(not (Path(folder) / d).is_symlink(), "Linked native directory")
            need(
                str((Path(folder) / d).relative_to(root)) in allowed_dirs,
                "Unexpected native directory",
            )
        for name in names:
            path = Path(folder) / name
            relative = str(path.relative_to(root))
            if path.is_symlink():
                raise ValueError('Native links forbidden in stock run')
            else:
                need(
                    relative in allowed_top
                    or re.fullmatch(r"owner-[0-9]{6}\.json", relative)
                    or re.fullmatch(
                        r"proof/(startup|after)-rank-[0-7]-pid-[0-9]+\.(json|maps)",
                        relative,
                    ),
                    "Unknown/partial native evidence: " + relative,
                )
                files[relative] = core.describe(path)
    need(len(files) <= 4300 and len(links) == 0, "Native inventory count/link bound")
    return {"files": files, "links": links}


def create_join(lock, case_name):
    case = next((c for c in campaign.producer.matrix() if c["case"] == case_name), None)
    need(case is not None, "Unknown final case")
    raw = core.ROOT / "results" / core.RUN / case_name
    native = core.ROOT / "native-runtime" / core.RUN / case_name
    need(raw.is_dir() and native.is_dir(), "Final namespaces missing")
    need(
        {p.name for p in raw.iterdir()} == adapter.audit_native.RAW14,
        "Raw14 set changed",
    )
    rawhash = {p.name: core.describe(p) for p in raw.iterdir()}
    status = core.read(raw / "status.json")
    meta = core.read(raw / "metadata.json")
    result = core.read(raw / "result.json")
    need(
        all(
            type(status[k]) is int
            for k in ("exit_code", "expected", "completed", "failed")
        ),
        "Raw terminal integer fields",
    )
    need(
        status["status"] == "completed"
        and status["exit_code"] == 0
        and status["expected"] == status["completed"] == case["requests"]
        and status["failed"] == 0
        and result["completed"] == result["num_prompts"] == case["requests"],
        "Raw completion failed",
    )
    need(
        meta["run_id"] == core.RUN
        and meta["inferencex_commit"] == lock["publication"]["commit"],
        "Raw run/recipe differs",
    )
    terminal = core.read(native / "exit.json")
    need(
        terminal["status"] == "CASE_PHASES_COMPLETED"
        and terminal["exit_code"] == terminal["benchmark_exit"] == 0
        and terminal["native_after"] is True
        and terminal["error"] is None
        and not terminal.get("cleanup_error"),
        "Native terminal failed",
    )
    cleanup = terminal["cleanup"]
    need(
        cleanup
        and all(
            type(x["returncode"]) is int
            and x["remaining"] == []
            and x["errors"] == []
            and x["cleanup_pending"] is False
            for x in cleanup
        ),
        "Owned cleanup not complete",
    )
    need(
        sum(x["label"] == "server" for x in cleanup) == 1,
        "Missing/duplicate server cleanup",
    )
    need(
        datetime.fromisoformat(status["finished_at"].replace("Z", "+00:00")).timestamp()
        >= terminal["at"],
        "Original finish predates native cleanup",
    )
    contract = core.read(native / "native-contract.json")
    need(
        contract["run_id"] == core.RUN
        and contract["case"] == case_name
        and contract["tp"] == case["tp"],
        "Contract case differs",
    )
    need(
        contract["runtime_seal_sha256"]
        == core.describe(core.ROOT / "environment/setup-completed.json")["sha256"],
        "Contract setup differs",
    )
    need(
        contract["stock_manifest_sha256"]
        == lock["native_binding"]["stock_manifest_sha256"],
        "Contract native build differs",
    )
    payload = {
        k: v
        for k, v in contract.items()
        if k not in ("native_contract_sha256", "proof_root", "execution_status")
    }
    need(
        campaign.producer.digest(payload) == contract["native_contract_sha256"],
        "Native contract digest differs",
    )
    startup = core.read(native / "startup-seal.json")
    after = core.read(native / "after-seal.json")
    need(startup["errors"] == after["errors"] == [], "Native seal errors")
    need(all(str(int(k)) == k for k in startup["owners"]), "Noncanonical rank key")
    owners = {int(k): v for k, v in startup["owners"].items()}
    need(
        set(owners) == set(range(case["tp"]))
        and len({v["pid"] for v in owners.values()}) == case["tp"],
        "Rank owner coverage",
    )
    need(
        all(
            type(v["pid"]) is int and type(v["starttime"]) is int
            for v in owners.values()
        ),
        "Rank owner types",
    )
    server_ledgers = [core.read(p) for p in sorted(native.glob("owner-*.json"))]
    server_ledgers = [x for x in server_ledgers if x["label"] == "server"]
    need(server_ledgers, "No independent server owner ledger")
    known = server_ledgers[-1]["known"]
    for owner in owners.values():
        need(
            str(owner["pid"]) in known
            and known[str(owner["pid"])]["starttime"] == owner["starttime"],
            "Rank not retained in server ledger",
        )
    # The frozen startup reader deliberately expects startup-only directory.
    # Final directories contain both phases; use the same snapshot validator on
    # the seal's exact startup file set instead of changing that frozen reader.
    return _finish(
        lock,
        case,
        raw,
        native,
        rawhash,
        status,
        result,
        terminal,
        contract,
        startup,
        after,
        owners,
    )


def _records(root, phase, lock, owners):
    result = []
    seen = set()
    for path in sorted((root / "proof").glob(phase + "-*.json")):
        record = core.read(path)
        need(
            record["maps_file"] == path.with_suffix(".maps").name,
            "Proof maps filename differs",
        )
        maps = root / "proof" / record["maps_file"]
        desc = core.describe(maps, adapter.native.MAX_MAPS)
        data = maps.read_bytes()
        need(
            adapter.native.hashlib.sha256(data).hexdigest() == desc["sha256"],
            "Maps changed",
        )
        rank = adapter.audit_native.snapshot(record, data, lock, owners, phase)
        need(rank not in seen, "Duplicate rank")
        seen.add(rank)
        result.append((record, data))
    need(seen == set(range(lock["tp"])), "Incomplete phase ranks")
    return result


def _finish(
    lock,
    case,
    raw,
    native,
    rawhash,
    status,
    result,
    terminal,
    contract,
    startup,
    after,
    owners,
):
    proof = {p.name: core.describe(p) for p in (native / "proof").iterdir()}
    start_files = {k: v for k, v in proof.items() if k.startswith("startup-")}
    need(
        startup["files"] == start_files and after["files"] == proof,
        "Native proof seal manifests differ",
    )
    need(
        startup["native_contract"] == core.describe(native / "native-contract.json"),
        "Startup contract SHA differs",
    )
    before = _records(native, "startup", contract, owners)
    end = _records(native, "after", contract, owners)
    need(len(proof) == case["tp"] * 4, "Orphan/error proof payload")
    window = after["window"]
    need(
        all(
            type(x) in (int, float) and math.isfinite(x)
            for x in (
                *window.values(),
                result["benchmark_start_time_unix"],
                result["benchmark_end_time_unix"],
            )
        ),
        "Nonfinite measured clock",
    )
    need(
        startup["at"]
        <= window["start"]
        <= window["end"]
        <= after["at"]
        <= terminal["at"],
        "Seal/terminal chronology",
    )
    need(
        window["start"]
        <= result["benchmark_start_time_unix"]
        <= result["benchmark_end_time_unix"]
        <= window["end"],
        "Measured clock interval outside client window",
    )
    before = {r["rank"]: r for r, _ in before}
    for record, _ in end:
        rank = record["rank"]
        need(
            before[rank]["at"] <= window["start"] <= window["end"] <= record["at"],
            "Snapshot clock order",
        )
        for item in contract["selected"].values():
            p = item["resolved_path"]
            need(
                before[rank]["native"]["images"][p] == record["native"]["images"][p],
                "Native image changed",
            )
    need(
        shlex.split((raw / "server_command.sh").read_text())
        == core.read(native / "launch-intent.json")["argv"],
        "Executed/recorded server command mismatch",
    )
    log=(raw/'server.log').read_bytes()
    proxy=core.read(native/'proxy-disabled.json')
    prefix=proxy['server_log_prefix']
    need(prefix['bytes']<=len(log) and adapter.native.sha(log[:prefix['bytes']])==prefix['sha256'], 'Preclient log prefix differs')
    checked=adapter.stock.proxy_info(log[:prefix['bytes']].decode(errors='replace'), owners, contract['hostname'])
    need(all(proxy[k]==v for k,v in checked.items()) and proxy['at']<=startup['at'], 'Proxy proof not sealed before client')
    adapter.stock.proxy_info(log.decode(errors='replace'),owners,contract['hostname'])
    manifest = native_manifest(native, lock["selected"])
    join = {
        "status": "SEALED_CASE_EVIDENCE_JOIN_NOT_BASE_AUDIT",
        "run_id": core.RUN,
        "case": case["case"],
        "recipe_commit": lock["publication"]["commit"],
        "raw14": rawhash,
        "native": manifest,
        "setup_seal": core.describe(core.ROOT / "environment/setup-completed.json"),
        "native_contract_sha256": contract["native_contract_sha256"],
        "owners": owners,
        "measured_requests": case["requests"],
        "base_audit_pending": True,
        "calibration_pending": True,
        "native_variant": "original-wheel-sglang-no-proxy-defaults",
        "at": core.now(),
    }
    need(
        rawhash == {p.name: core.describe(p) for p in raw.iterdir()}
        and manifest == native_manifest(native, lock["selected"]),
        "Finalized evidence changed",
    )
    target = core.ROOT / "joins" / case["case"]
    target.parent.mkdir(parents=True, exist_ok=True)
    core.write(target.with_suffix(".json"), join)
    return join

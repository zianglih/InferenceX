"""Closed R4 cache/TMP inventory and approved R5 seed install; no import side effects."""

import hashlib
import json
import os
from pathlib import Path
import stat

if not __debug__:
    raise RuntimeError("Optimized cache helper prohibited")

REMOTE = Path("/data/home/ziangli/inferencex-kimik3-three-curves-c32-20260929")
R4_RUN = REMOTE / "kimi-k3-ep8-three-curves-c32-20260929-all12-r4"
R5_RUN = REMOTE / "kimi-k3-ep8-three-curves-c32-20260929-remaining11-r5"
R4_TMP = Path("/tmp/infx-k3-3c-r4")
R5_TMP = Path("/tmp/infx-k3-3c-r5")
SEED = REMOTE / "r5-cache-seed"
PROVIDER_PREFIX = Path(
    "/opt/sglang/lib/python3.12/site-packages/flashinfer_cubin/cubins"
)
MAX_MEMBERS, MAX_DEPTH = 500000, 40
MAX_FILE, MAX_TOTAL, MAX_JSON = 8 << 30, 128 << 30, 128 << 20
SCOPES = ("caches", "hf-home", "tmp")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def descriptor_bytes(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def encode(value):
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def stamp(s):
    return [
        s.st_dev,
        s.st_ino,
        s.st_mode,
        s.st_uid,
        s.st_nlink,
        s.st_size,
        s.st_mtime_ns,
        s.st_ctime_ns,
    ]


def canonical(path, *, absent=False):
    p = Path(path)
    require(
        p.is_absolute() and ".." not in p.parts and str(p) == str(path),
        "Canonical absolute path",
    )
    for x in (p, *p.parents):
        require(not x.is_symlink(), "Linked path component")
    require(p.resolve() == p, "Resolved path differs")
    if absent:
        require(not os.path.lexists(p), "Exclusive destination exists")
    return p


def relative(name):
    p = Path(name)
    require(
        isinstance(name, str)
        and name
        and not p.is_absolute()
        and ".." not in p.parts
        and str(p) == name
        and len(p.parts) <= MAX_DEPTH,
        "Relative member path",
    )
    return p


def file_hash(path, *, destination=None, limit=MAX_FILE):
    p = canonical(path)
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    out = None
    try:
        s = os.fstat(fd)
        require(
            stat.S_ISREG(s.st_mode) and 0 <= s.st_size <= limit, "Bounded regular file"
        )
        if destination is not None:
            d = canonical(destination, absent=True)
            out = os.open(
                d, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
            )
        h, size = hashlib.sha256(), 0
        while True:
            b = os.read(fd, min(1 << 20, s.st_size + 1 - size))
            if not b:
                break
            size += len(b)
            require(size <= s.st_size, "File grew")
            h.update(b)
            if out is not None:
                view = memoryview(b)
                while view:
                    n = os.write(out, view)
                    require(n > 0, "Short destination write")
                    view = view[n:]
        require(
            size == s.st_size and stamp(s) == stamp(os.fstat(fd)) == stamp(p.lstat()),
            "Source changed while reading",
        )
        if out is not None:
            os.fchmod(out, stat.S_IMODE(s.st_mode))
            os.fsync(out)
            ds = os.fstat(out)
            require(
                ds.st_nlink == 1 and (ds.st_dev, ds.st_ino) != (s.st_dev, s.st_ino),
                "Destination hardlink or shared inode",
            )
            os.utime(d, ns=(s.st_atime_ns, s.st_mtime_ns), follow_symlinks=False)
        return {"bytes": size, "sha256": h.hexdigest(), "stat": stamp(s)}
    finally:
        if out is not None:
            os.close(out)
        os.close(fd)


def document(path, expected=None):
    p = canonical(path)
    got = file_hash(p, limit=MAX_JSON)
    if expected is not None:
        require(
            {k: got[k] for k in ("bytes", "sha256")}
            == {k: expected[k] for k in ("bytes", "sha256")},
            "Document descriptor",
        )
    with p.open("rb") as f:
        raw = f.read(MAX_JSON + 1)
    require(len(raw) <= MAX_JSON, "Document grew beyond cap")
    require(
        descriptor_bytes(raw) == {k: got[k] for k in ("bytes", "sha256")}
        and stamp(p.lstat()) == got["stat"],
        "Document changed",
    )

    def pairs(rows):
        out = {}
        for k, v in rows:
            require(k not in out, "Duplicate JSON key")
            out[k] = v
        return out

    return json.loads(
        raw,
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)),
    )


def write_exclusive(path, value):
    raw = encode(value)
    require(len(raw) <= MAX_JSON, "Manifest byte bound")
    p = canonical(path, absent=True)
    with p.open("xb") as f:
        f.write(raw)
        f.flush()
        os.fsync(f.fileno())
    return {"path": str(p), **descriptor_bytes(raw)}


def inventory(roots, *, hashes=True):
    """Never follows a link. The second stat-only pass closes all names/stamps."""
    rows, root_stats, total = {}, {}, 0
    for scope, root in sorted(roots.items()):
        root = canonical(root)
        s = root.lstat()
        require(stat.S_ISDIR(s.st_mode), "Required source root missing/not directory")
        root_stats[scope] = stamp(s)
        stack = [(root, 0)]
        while stack:
            directory, depth = stack.pop()
            require(depth <= MAX_DEPTH, "Directory depth bound")
            before = stamp(directory.lstat())
            with os.scandir(directory) as it:
                children = []
                for entry in it:
                    require(
                        len(rows) + len(children) < MAX_MEMBERS,
                        "Directory member bound",
                    )
                    children.append(entry)
                children.sort(key=lambda e: e.name)
            for entry in children:
                p = Path(entry.path)
                rel = str(p.relative_to(root))
                relative(rel)
                name = scope + "/" + rel
                require(
                    name not in rows and len(rows) < MAX_MEMBERS, "Member closure/bound"
                )
                s = p.lstat()
                row = {"stat": stamp(s), "mode": stat.S_IMODE(s.st_mode)}
                if stat.S_ISLNK(s.st_mode):
                    text = os.readlink(p)
                    require(len(os.fsencode(text)) <= 4096, "Link text bound")
                    row.update(kind="symlink", link_text=text)
                elif stat.S_ISDIR(s.st_mode):
                    row["kind"] = "directory"
                    stack.append((p, depth + 1))
                elif stat.S_ISREG(s.st_mode):
                    require(s.st_size <= MAX_FILE, "File cap")
                    total += s.st_size
                    require(total <= MAX_TOTAL, "Aggregate payload cap")
                    row.update(kind="file", bytes=s.st_size)
                    if hashes:
                        got = file_hash(p)
                        require(
                            got["stat"] == row["stat"], "Listing/read identity changed"
                        )
                        row["sha256"] = got["sha256"]
                else:
                    row["kind"] = "socket" if stat.S_ISSOCK(s.st_mode) else "special"
                rows[name] = row
            require(stamp(directory.lstat()) == before, "Directory changed during walk")
        require(stamp(root.lstat()) == root_stats[scope], "Root changed during walk")
    return {
        "roots": {k: str(v) for k, v in roots.items()},
        "root_stats": root_stats,
        "files": dict(sorted(rows.items())),
        "regular_bytes": total,
    }


def without_hashes(value):
    return {
        **value,
        "files": {
            n: {k: v for k, v in r.items() if k != "sha256"}
            for n, r in value["files"].items()
        },
    }


def closed_inventory(roots):
    result = inventory(roots)
    require(
        without_hashes(result) == inventory(roots, hashes=False),
        "Tree changed after hashing",
    )
    return result


def content_rows(rows):
    return {n: {k: v for k, v in row.items() if k != "stat"} for n, row in rows.items()}


def check_policy(inv, policy):
    require(set(inv["roots"]) == set(SCOPES), "Three exact search scopes required")
    require(set(policy) == {"links", "excluded", "providers"}, "Closed policy fields")
    rows = inv["files"]
    require(
        set(policy["links"]) == {n for n, r in rows.items() if r["kind"] == "symlink"},
        "Every link needs explicit policy",
    )
    for name, approved in policy["excluded"].items():
        require(name in rows and approved["row"] == rows[name], "Exact exclusion row")
        require(
            (
                name == "tmp/.inferencex-owner.json"
                and rows[name]["kind"] == "file"
                and approved["reason"] == "historical-owner-marker"
            )
            or (
                name.startswith("tmp/")
                and rows[name]["kind"] == "socket"
                and approved["reason"] == "inactive-ipc-socket-not-recreated"
            ),
            "Only historical TMP owner/IPC exclusions admitted",
        )
    require(
        "tmp/.inferencex-owner.json" in policy["excluded"],
        "Retain original TMP owner separately",
    )
    require(
        {n for n, r in rows.items() if r["kind"] in ("socket", "special")}
        <= set(policy["excluded"]),
        "Unapproved special member",
    )
    require(len(policy["providers"]) <= 8, "Provider target count")
    require(
        sum(v["regular_bytes"] for v in policy["providers"].values()) <= MAX_TOTAL,
        "Aggregate provider payload cap",
    )
    for name, provider in policy["providers"].items():
        p = canonical(name)
        require(
            p.is_relative_to(PROVIDER_PREFIX) and p != PROVIDER_PREFIX,
            "Provider must be an exact cubin descendant, not package scan",
        )
        require(provider["roots"] == {"provider": str(p)}, "Provider inventory root")
        require(
            all(r["kind"] in ("file", "directory") for r in provider["files"].values()),
            "Provider target tree must be closed without links/specials",
        )
    for name, link in policy["links"].items():
        require(link["source_text"] == rows[name]["link_text"], "Link source text")
        rel = relative(link["target_relative"])
        if link["target_scope"] == "provider":
            require(
                link["provider_root"] in policy["providers"], "Provider link binding"
            )
            target = Path(link["provider_root"]) / rel
            require(
                str(rel) == "."
                or "provider/" + str(rel)
                in policy["providers"][link["provider_root"]]["files"],
                "Provider member omitted",
            )
        else:
            require(link["target_scope"] in SCOPES, "Link target scope")
            key = link["target_scope"] + "/" + str(rel)
            require(
                str(rel) == "."
                or (
                    key in rows
                    and key not in policy["excluded"]
                    and rows[key]["kind"] in ("file", "directory")
                ),
                "Link target omitted/linked",
            )
            target = Path(inv["roots"][link["target_scope"]]) / rel
        original = Path(inv["roots"][name.split("/", 1)[0]]) / name.split("/", 1)[1]
        require(
            original.resolve(strict=True) == canonical(target),
            "Observed link target differs",
        )


def providers_unchanged(policy):
    for root, expected in policy["providers"].items():
        require(
            closed_inventory({"provider": Path(root)}) == expected,
            "Provider tree changed",
        )


def link_text(link, destination, roots):
    if link["target_scope"] == "provider":
        return str(Path(link["provider_root"]) / link["target_relative"])
    return os.path.relpath(
        Path(roots[link["target_scope"]]) / link["target_relative"], destination.parent
    )


def expected_copy_rows(inv, policy, targets, retain_owner=False):
    out = content_rows(inv["files"])
    for name in policy["excluded"]:
        if not (retain_owner and name == "tmp/.inferencex-owner.json"):
            out.pop(name)
    for name, link in policy["links"].items():
        scope, rel = name.split("/", 1)
        out[name]["link_text"] = link_text(link, Path(targets[scope]) / rel, targets)
    return out


def copy_tree(inv, policy, targets, *, existing_tmp_marker=False, retain_owner=False):
    """Copy only accepted rows; preserve partial output on any exception."""
    check_policy(inv, policy)
    sources = {k: Path(v) for k, v in inv["roots"].items()}
    require(closed_inventory(sources) == inv, "Source differs before copy")
    providers_unchanged(policy)
    require(set(targets) == set(SCOPES), "Destination scopes")
    marker = None
    for scope, root in targets.items():
        root = canonical(root)
        require(
            all(
                not root.is_relative_to(s) and not s.is_relative_to(root)
                for s in sources.values()
            ),
            "Source/destination overlap",
        )
        if scope == "tmp" and existing_tmp_marker:
            require(
                {p.name for p in root.iterdir()} == {".inferencex-owner.json"},
                "Fresh TMP marker only",
            )
            marker = file_hash(root / ".inferencex-owner.json", limit=1 << 20)
        else:
            require(
                root.is_dir() and not list(root.iterdir()),
                "Empty exclusive destination required",
            )
    require(not (existing_tmp_marker and retain_owner), "Owner retention mode conflict")
    expected = expected_copy_rows(inv, policy, targets, retain_owner)
    for name, row in sorted(
        inv["files"].items(), key=lambda x: (len(Path(x[0]).parts), x[0])
    ):
        if name in policy["excluded"] and not (
            retain_owner and name == "tmp/.inferencex-owner.json"
        ):
            continue
        scope, rel = name.split("/", 1)
        src, dst = sources[scope] / rel, Path(targets[scope]) / rel
        canonical(dst.parent)
        require(not os.path.lexists(dst), "Destination member already exists")
        if row["kind"] == "directory":
            dst.mkdir(mode=0o700)
        elif row["kind"] == "file":
            got = file_hash(src, destination=dst)
            require(
                got == {k: row[k] for k in ("bytes", "sha256", "stat")},
                "Copied file source mismatch",
            )
        elif row["kind"] == "symlink":
            os.symlink(expected[name]["link_text"], dst)
        else:
            raise ValueError("Noncopyable member")
    for name, row in reversed(list(inv["files"].items())):
        if row["kind"] == "directory":
            scope, rel = name.split("/", 1)
            dst = Path(targets[scope]) / rel
            os.chmod(dst, row["mode"], follow_symlinks=False)
            os.utime(dst, ns=(row["stat"][6], row["stat"][6]), follow_symlinks=False)
    copied = closed_inventory(targets)
    compare = dict(copied["files"])
    if marker is not None:
        require(
            file_hash(Path(targets["tmp"]) / ".inferencex-owner.json", limit=1 << 20)
            == marker,
            "Fresh TMP owner changed",
        )
        compare.pop("tmp/.inferencex-owner.json")
    require(
        content_rows(compare) == expected,
        "Complete destination bytes/member/type mismatch",
    )
    require(closed_inventory(sources) == inv, "Source changed after copy")
    providers_unchanged(policy)
    return copied


def validate_seed(cfg, prior_descriptor, acceptance_descriptor):
    require(
        cfg["runtime"]["run_root"] == str(R5_RUN)
        and cfg["runtime"]["tmp_root"] == str(R5_TMP),
        "Fixed R5 namespaces",
    )
    acceptance = document(acceptance_descriptor["path"], acceptance_descriptor)
    require(
        acceptance["status"] == "ACCEPTED_KIMI_QUIESCENT_CACHE_SEED"
        and acceptance["data_kind"] == "actual"
        and acceptance["prior_case_acceptance"] == prior_descriptor,
        "Actual root seed acceptance/parent required",
    )
    prior = document(prior_descriptor["path"], prior_descriptor)
    require(
        prior["status"] == "ACCEPTED_KIMI_PRIOR_C32_FOR_CONTINUATION"
        and prior["data_kind"] == "actual",
        "Accepted prior C32 required",
    )
    receipt = document(acceptance["receipt"]["path"], acceptance["receipt"])
    require(
        receipt["status"] == "R4_CACHE_SEED_COPIED_PENDING_INDEPENDENT_ROOT_REVIEW"
        and receipt["prior_case_acceptance"] == prior_descriptor,
        "Seed copied receipt/parent",
    )
    inv, policy = receipt["copied_inventory"], receipt["install_policy"]
    require(inv["roots"] == {s: str(SEED / s) for s in SCOPES}, "Fixed seed roots")
    require(
        acceptance["copied_inventory_sha256"] == descriptor_bytes(encode(inv))["sha256"]
        and acceptance["install_policy_sha256"]
        == descriptor_bytes(encode(policy))["sha256"],
        "Accepted exact files/policy",
    )
    require(
        closed_inventory({s: SEED / s for s in SCOPES}) == inv, "Immutable seed changed"
    )
    check_policy(inv, policy)
    providers_unchanged(policy)
    return {
        "inventory": inv,
        "policy": policy,
        "acceptance": acceptance_descriptor,
        "prior_case_acceptance": prior_descriptor,
    }


def install_seed(seed, run_root, tmp_root):
    require(Path(run_root) == R5_RUN and Path(tmp_root) == R5_TMP, "Install namespaces")
    targets = {
        "caches": Path(run_root) / "caches",
        "hf-home": Path(run_root) / "hf-home",
        "tmp": Path(tmp_root),
    }
    copied = copy_tree(
        seed["inventory"], seed["policy"], targets, existing_tmp_marker=True
    )
    installed = write_exclusive(
        Path(run_root) / "cache-installation-inventory.json", copied
    )
    expected = expected_copy_rows(seed["inventory"], seed["policy"], targets)
    receipt = {
        "status": "ACCEPTED_SEED_INSTALLED_WITH_FRESH_TMP_OWNER",
        "seed_acceptance": seed["acceptance"],
        "acceptance_sha256": seed["acceptance"]["sha256"],
        "prior_case_acceptance": seed["prior_case_acceptance"],
        "installed_inventory": installed,
        "copied_files": sum(r["kind"] == "file" for r in expected.values()),
        "copied_bytes": sum(r.get("bytes", 0) for r in expected.values()),
        "excluded": sorted(seed["policy"]["excluded"]),
        "compile_payloads_hashed": True,
        "tactic_payloads_hashed": True,
        "limit": "Exact copied bytes, not a guarantee of path-dependent compiler cache hits.",
    }
    validate_install_receipt(
        receipt, run_root, seed["prior_case_acceptance"], seed["acceptance"]
    )
    return receipt


def validate_install_receipt(
    receipt, run_root, prior_descriptor, acceptance_descriptor
):
    """Pure saved-control validator; performs no file or cache payload read."""
    require(Path(run_root) == R5_RUN, "Fixed installed run")
    require(
        receipt["status"] == "ACCEPTED_SEED_INSTALLED_WITH_FRESH_TMP_OWNER"
        and receipt["seed_acceptance"] == acceptance_descriptor
        and receipt["acceptance_sha256"] == acceptance_descriptor["sha256"]
        and receipt["prior_case_acceptance"] == prior_descriptor,
        "Saved installed receipt parent joins",
    )
    inv = receipt["installed_inventory"]
    require(
        inv["path"] == str(Path(run_root) / "cache-installation-inventory.json")
        and type(inv["bytes"]) is int
        and 0 < inv["bytes"] <= MAX_JSON
        and len(inv["sha256"]) == 64
        and all(x in "0123456789abcdef" for x in inv["sha256"]),
        "Full installed inventory descriptor",
    )
    require(
        type(receipt["copied_files"]) is int
        and 0 <= receipt["copied_files"] <= MAX_MEMBERS
        and type(receipt["copied_bytes"]) is int
        and 0 <= receipt["copied_bytes"] <= MAX_TOTAL
        and receipt["excluded"] == ["tmp/.inferencex-owner.json"]
        and receipt["compile_payloads_hashed"] is True
        and receipt["tactic_payloads_hashed"] is True,
        "Saved installed receipt coverage",
    )
    return True

#!/usr/bin/env python3
"""Exact reviewed three-file SGLang patch guard; no imports or writes at import time."""

import hashlib
import os
from pathlib import Path
import stat
import subprocess

PATCH = {
    "base_commit": "561ad447c74bb757a40677ee9ce038f9ca429d2c",
    "diff": {
        "bytes": 6993,
        "sha256": "d4bdb5246dbeaca7bf23472cbae617b434bcb3b77c248d0e40e46b8405786ef1",
    },
    "files": {
        "python/sglang/srt/arg_groups/moe_hook.py": {
            "bytes": 32213,
            "sha256": "a5b87ffb25e35d43cf793d2944a4ae179b58173620a7450c571152557455d41d",
        },
        "python/sglang/srt/layers/moe/flashinfer_megamoe.py": {
            "bytes": 27778,
            "sha256": "3dc69aea4056fcd08b85f93490dc0dc61ae0674dcfa3a7a4980bb1c32ad1a84b",
        },
        "python/sglang/srt/layers/moe/flashinfer_megamoe_autotune.py": {
            "bytes": 14585,
            "sha256": "97f3724fea8181cc795e5dd571a7ef084d394d043b2bb4fcd0cfcf4b4e2c84c2",
        },
    },
}
DIFF_ARGS = [
    "diff",
    "--no-ext-diff",
    "--no-textconv",
    "--binary",
    "--full-index",
    "--src-prefix=a/",
    "--dst-prefix=b/",
    "HEAD",
    "--",
]


def require(value, message):
    if not value:
        raise ValueError(message)


def query(root, args, env=None):
    p = subprocess.run(
        ["git", "-C", str(root), *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    require(
        p.returncode == 0 and len(p.stdout) <= 4 * 1024 * 1024,
        "Source Git query failed or excessive",
    )
    return p.stdout


def file_digest(path):
    p = Path(path)
    require(p.is_absolute(), "Source path must be absolute")
    for parent in (p, *p.parents):
        require(not parent.is_symlink(), "Linked source path")
    fd = os.open(p, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        a = os.fstat(fd)
        require(
            stat.S_ISREG(a.st_mode) and a.st_size <= 16 * 1024 * 1024,
            "Source file type/size",
        )
        h = hashlib.sha256()
        size = 0
        while True:
            b = os.read(fd, min(1 << 20, a.st_size + 1 - size))
            if not b:
                break
            size += len(b)
            require(size <= a.st_size, "Source grew")
            h.update(b)
        b = os.fstat(fd)
        c = p.lstat()

        def fields(x):
            return (
                x.st_dev,
                x.st_ino,
                x.st_mode,
                x.st_size,
                x.st_mtime_ns,
                x.st_ctime_ns,
            )

        require(
            fields(a) == fields(b) == fields(c) and size == a.st_size,
            "Source changed while reading",
        )
        return {"bytes": size, "sha256": h.hexdigest()}
    finally:
        os.close(fd)


def check_campaign(cfg):
    expected = {
        "sglang": {
            "base_commit": PATCH["base_commit"],
            "patch": {"path": "artifacts/sglang-dp1.patch", **PATCH["diff"]},
            "files": {"sglang/" + k: v for k, v in PATCH["files"].items()},
        }
    }
    require(
        cfg.get("local_changes") == expected
        and cfg["pins"].get("sglang_local_patch") == PATCH["diff"]["sha256"],
        "Exact reviewed source patch required",
    )


def patched_source(root, env=None):
    root = Path(root)
    require(
        root.is_absolute() and root.is_dir() and not root.is_symlink(),
        "Source root differs",
    )
    require(
        query(root, ["rev-parse", "HEAD"], env).decode().strip()
        == PATCH["base_commit"],
        "Patched source HEAD differs",
    )
    require(
        query(root, ["diff", "--cached", "--name-only"], env) == b"",
        "Staged source changes prohibited",
    )
    require(
        query(root, ["ls-files", "--others", "--exclude-standard"], env) == b"",
        "Untracked source changes prohibited",
    )
    require(
        all(
            line.startswith(b"H ")
            for line in query(root, ["ls-files", "-v"], env).splitlines()
        ),
        "Hidden index worktree flags prohibited",
    )
    names = query(root, ["diff", "--name-only", "HEAD"], env).decode().splitlines()
    require(names == sorted(PATCH["files"]), "Changed source path closure differs")
    diff = query(root, DIFF_ARGS, env)
    observed_diff = {"bytes": len(diff), "sha256": hashlib.sha256(diff).hexdigest()}
    require(observed_diff == PATCH["diff"], "Exact source diff differs")
    files = {name: file_digest(root / name) for name in PATCH["files"]}
    require(files == PATCH["files"], "Patched source bytes differ")
    submodules = query(root, ["submodule", "status"], env).decode().strip()
    require(submodules == "", "Unexpected SGLang submodule state")
    return {
        "commit": PATCH["base_commit"],
        "submodules": submodules,
        "untracked": [],
        "generated_files": {},
        "patch": {"diff": observed_diff, "files": files},
        "index_clean": True,
    }

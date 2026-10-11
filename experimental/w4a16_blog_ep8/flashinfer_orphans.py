"""Quarantine unregistered FlashInfer remnants after pip uninstall.

pip retains generated provider/cache files. An otherwise empty package can then
become a namespace package, which FlashInfer mistakes for an installed JIT shim.
"""

import importlib
import importlib.metadata as md
import importlib.util
from pathlib import Path
import re
import shutil
import site
import sysconfig


def quarantine_orphaned_flashinfer(destination: Path) -> list[dict]:
    remaining = [
        d.metadata["Name"]
        for d in md.distributions()
        if re.sub(r"[-_.]+", "-", d.metadata["Name"] or "")
        .lower()
        .startswith("flashinfer-")
    ]
    if remaining:
        raise RuntimeError(f"FlashInfer distributions remain registered: {remaining}")
    roots = {
        Path(value).resolve()
        for value in [
            *site.getsitepackages(),
            sysconfig.get_path("purelib"),
            sysconfig.get_path("platlib"),
        ]
        if value
    }
    candidates = []
    for root in sorted(roots):
        if not root.is_dir():
            continue
        for path in root.iterdir():
            if path.name in (
                "flashinfer",
                "flashinfer_cubin",
                "flashinfer_jit_cache",
            ) or re.fullmatch(r"flashinfer_jit_cache_[a-z0-9_]+", path.name):
                if path.is_symlink() or not path.is_dir():
                    raise RuntimeError(f"Unexpected FlashInfer module path: {path}")
                candidates.append(path)
    destination.mkdir(exist_ok=False)
    moves = []
    for index, path in enumerate(candidates):
        target = destination / f"{index:02d}-{path.name}"
        shutil.move(str(path), str(target))
        moves.append({"from": str(path), "to": str(target)})
    importlib.invalidate_caches()
    for name in ("flashinfer", "flashinfer_cubin", "flashinfer_jit_cache"):
        if importlib.util.find_spec(name) is not None:
            raise RuntimeError(f"Unexpected importable {name} remains after quarantine")
    return moves

#!/usr/bin/env python3
"""Compact verification of the source-built FlashInfer/SGLang installation."""

import hashlib
import importlib.metadata as md
import importlib.util
import json
import os
from pathlib import Path
import re
import sys


def digest(path):
    data = path.read_bytes()
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main():
    request = json.loads(Path(sys.argv[1]).read_text())
    for key, value in request["runtime_environment"].items():
        assert os.environ.get(key) == value, key
    assert "PYTHONPATH" not in os.environ
    assert "FLASHINFER_CUBIN_DIR" not in os.environ
    assert "FLASHINFER_DISABLE_VERSION_CHECK" not in os.environ
    import torch
    import flashinfer
    import flashinfer._build_meta as python_meta
    import flashinfer_cubin
    import flashinfer_cubin._build_meta as cubin_meta
    from flashinfer.jit import env
    import sglang

    torch_after = {
        "torch": str(torch.__version__),
        "torch_cuda": torch.version.cuda,
        "torch_file": torch.__file__,
    }
    assert torch_after == request["before"], (torch_after, request["before"])
    assert python_meta.__git_commit__ == request["flashinfer_sha"]
    assert cubin_meta.__git_version__ == request["flashinfer_sha"]
    assert (
        flashinfer.__version__
        == flashinfer_cubin.__version__
        == request["flashinfer_version"]
    )
    assert importlib.util.find_spec("flashinfer_jit_cache") is None
    assert env.FLASHINFER_AOT_PROVIDERS == ()
    packages = {}
    for distribution in md.distributions():
        name = distribution.metadata["Name"]
        canonical = re.sub(r"[-_.]+", "-", name).lower() if name else ""
        if canonical.startswith("flashinfer-") or canonical == "sglang":
            assert canonical not in packages, ("duplicate distribution", canonical)
            direct_url = distribution.read_text("direct_url.json")
            packages[canonical] = {
                "version": distribution.version,
                "root": str(distribution.locate_file("")),
                "direct_url": json.loads(direct_url) if direct_url else None,
            }
    assert set(packages) == {"flashinfer-python", "flashinfer-cubin", "sglang"}, (
        packages
    )
    for package in packages.values():
        assert package["direct_url"] and package["direct_url"]["url"].startswith(
            "file:"
        ), package
        assert package["direct_url"]["url"].endswith(".whl"), package
    fi_root = Path(flashinfer.__file__).resolve().parent
    sg_root = Path(sglang.__file__).resolve().parent
    for source in request["repositories"].values():
        assert not fi_root.is_relative_to(source["path"])
        assert not sg_root.is_relative_to(source["path"])
    cubins = Path(flashinfer_cubin.__file__).resolve().parent / "cubins"
    assert env.FLASHINFER_CUBIN_DIR.resolve() == cubins.resolve()
    assert next(cubins.rglob("*.cubin"), None) is not None
    files = {}
    for relative, expected in request["files"]["flashinfer"].items():
        installed = fi_root / relative.removeprefix("flashinfer/")
        assert digest(installed) == expected, installed
        files[relative] = {"installed": str(installed), **expected}
    for relative, expected in request["files"]["sglang"].items():
        installed = sg_root / relative.removeprefix("python/sglang/")
        assert digest(installed) == expected, installed
        files[relative] = {"installed": str(installed), **expected}
    # Import the actual optimized frontend rather than proving only package metadata.
    from flashinfer.moe_ep.cute_dsl.megamoe.bf16_nvfp4 import autotune, frontend

    assert Path(frontend.__file__).resolve().is_relative_to(fi_root)
    assert Path(autotune.__file__).resolve().is_relative_to(fi_root)
    gpus = [
        {
            "name": torch.cuda.get_device_name(i),
            "capability": list(torch.cuda.get_device_capability(i)),
        }
        for i in range(torch.cuda.device_count())
    ]
    assert len(gpus) == 8 and all(gpu["capability"] == [10, 3] for gpu in gpus), gpus
    result = {
        "status": "VERIFIED_SOURCE_INSTALL_ONLY",
        "flashinfer_sha": request["flashinfer_sha"],
        "sglang_sha": request["sglang_sha"],
        "flashinfer_version": flashinfer.__version__,
        "torch": torch_after,
        "packages": packages,
        "gpus": gpus,
        "source_files": files,
        "cubin_directory": str(cubins),
        "jit_cache_providers": [],
        "runtime_environment": request["runtime_environment"],
        "qualification": "Cubin package built locally from the pinned checkout and its artifact catalog; required CUDA/CuTe modules compile from pinned source. Server/GPU benchmark validation remains separate.",
    }
    with Path(sys.argv[2]).open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "flashinfer_version": flashinfer.__version__,
                "packages": sorted(packages),
                "gpus": len(gpus),
            }
        )
    )


if __name__ == "__main__":
    main()

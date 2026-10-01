"""Pinned DeepSeek-V4.1 text-chat formatting, loaded from the local checkpoint."""

import hashlib
from functools import lru_cache
from pathlib import Path
from types import ModuleType

ENCODER_SHA256 = "502bdaec8a3fd88ebc24c4721a7038fbe42f2063c664638127056107920035c1"


@lru_cache(maxsize=2)
def _encoder(model_path: str) -> ModuleType:
    path = Path(model_path).resolve() / "encoding/encoding.py"
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ENCODER_SHA256:
        raise ValueError("DeepSeek-V4.1 checkpoint encoder does not match the reviewed source")
    # Compile the bytes just verified, without importing mutable adjacent modules.
    module = ModuleType("inferencex_pinned_dsv41_encoder")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)  # noqa: S102
    return module


def encode_text_chat(model_path: str, prompt: str) -> str:
    text, media = _encoder(model_path).encode_messages(
        [{"role": "user", "content": prompt}],
        thinking_mode="chat",
        reasoning_effort=None,
        return_multi_modal_data=True,
    )
    if not isinstance(text, str) or media != {"images": []}:
        raise ValueError("The random benchmark requires text-only V4.1 chat prompts")
    return text

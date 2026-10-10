#!/usr/bin/env python3
"""Compact InferenceX workload client with measured-only native speculation counters."""

import argparse
import asyncio
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time
from types import ModuleType

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
ENCODER_SHA256 = "502bdaec8a3fd88ebc24c4721a7038fbe42f2063c664638127056107920035c1"
PROMPT_FORMATS = {
    "dsv41": "DeepSeek-V4.1 chat; reasoning_effort=None",
    "glm52": "tokenizer chat template; add_generation_prompt=True",
}


def canonical(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def sha256(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


class ChatTokenizer:
    """Supply the pinned V4.1 chat formatter to InferenceX's unchanged sampler."""

    def __init__(self, tokenizer, checkpoint):
        self.tokenizer = tokenizer
        path = Path(checkpoint) / "encoding/encoding.py"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != ENCODER_SHA256:
            raise ValueError("V4.1 checkpoint encoder differs from the pinned revision")
        self.encoder = ModuleType("inferencex_v41_chat_encoder")
        self.encoder.__file__ = str(path)
        exec(compile(raw, str(path), "exec"), self.encoder.__dict__)

    def __getattr__(self, key):
        return getattr(self.tokenizer, key)

    def apply_chat_template(self, messages, *, add_generation_prompt, tokenize):
        if not add_generation_prompt or tokenize:
            raise ValueError("Expected a rendered generation prompt")
        text, media = self.encoder.encode_messages(
            messages,
            thinking_mode="chat",
            reasoning_effort=None,
            return_multi_modal_data=True,
        )
        if not isinstance(text, str) or media != {"images": []}:
            raise ValueError("Expected a text-only V4.1 chat prompt")
        return text


def prepare_plan(model_id, checkpoint, concurrency):
    import numpy as np
    from infx.bench_serving.benchmark_serving import sample_random_requests
    from infx.bench_serving.backend_request_func import get_tokenizer

    random.seed(0)
    np.random.seed(0)
    tokenizer = get_tokenizer(checkpoint, trust_remote_code=True)
    if model_id == "dsv41":
        tokenizer = ChatTokenizer(tokenizer, checkpoint)
    # The upstream serial sampler is deterministic and runs before timing. A plan
    # is generated once, then shared byte-for-byte across the three target arms.
    requests = sample_random_requests(
        prefix_len=0,
        input_len=1024,
        output_len=8192,
        num_prompts=10 * concurrency,
        range_ratio=0.8,
        tokenizer=tokenizer,
        use_chat_template=True,
        dsv4=False,
        num_workers=1,
    )
    rows = [
        {"prompt": row[0], "input_tokens": row[1], "output_tokens": row[2]}
        for row in requests
    ]
    return {
        "schema_version": 1,
        "model_id": model_id,
        "concurrency": concurrency,
        "prompt_format": PROMPT_FORMATS[model_id],
        "requests": rows,
    }


def payload(request, served_model):
    return {
        "model": served_model,
        "prompt": request["prompt"],
        "temperature": 0.0,
        "best_of": 1,
        "max_tokens": request["output_tokens"],
        "logprobs": None,
        "stream": True,
        "stream_options": {"include_usage": True},
        "ignore_eos": True,
        "return_spec_tokens_details": True,
    }


def native_counters(usage, details, gamma):
    if not isinstance(usage, dict) or not isinstance(details, dict):
        raise ValueError("Missing final usage/speculative details")
    completion = usage.get("completion_tokens")
    counters = [
        details.get(k)
        for k in (
            "spec_verify_ct",
            "spec_num_correct_drafts",
            "spec_num_proposed_drafts",
        )
    ]
    if type(completion) is not int or completion <= 1:
        raise ValueError("Missing final completion count")
    if any(type(value) is not int or value < 0 for value in counters):
        raise ValueError("Malformed native speculative counters")
    verify, correct, proposed = counters
    if verify <= 0 or proposed != gamma * verify or correct > proposed:
        raise ValueError("Invalid native verification/proposal counters")
    for key, expected in (
        ("spec_accept_length", completion / verify),
        ("spec_accept_rate", correct / proposed),
    ):
        value = details.get(key)
        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
            or not math.isclose(value, expected, rel_tol=1e-9, abs_tol=1e-12)
        ):
            raise ValueError("Native ratio disagrees with counters: " + key)
    return {
        "completion_tokens": completion,
        "spec_verify_ct": verify,
        "spec_correct_drafts": correct,
        "spec_proposed_drafts": proposed,
    }


async def request_one(session, url, request, served_model, gamma):
    start = time.perf_counter()
    first = last = None
    intervals = []
    usage = details = None
    done = False
    async with session.post(url, json=payload(request, served_model)) as response:
        if response.status != 200:
            raise RuntimeError(
                f"HTTP {response.status}: {(await response.text())[:2000]}"
            )
        async for raw in response.content:
            line = raw.strip()
            if not line or line.startswith(b":"):
                continue
            if not line.startswith(b"data:"):
                raise ValueError("Unexpected completion stream event")
            data = line[5:].strip()
            if done:
                raise ValueError("Completion data after DONE")
            if data == b"[DONE]":
                done = True
                continue
            event = json.loads(data)
            if "error" in event:
                raise RuntimeError(str(event["error"]))
            if event.get("choices"):
                timestamp = time.perf_counter()
                if first is None:
                    first = timestamp
                else:
                    intervals.append(timestamp - last)
                last = timestamp
            if event.get("usage") is not None:
                if usage is not None:
                    raise ValueError("Duplicate final usage")
                usage = event["usage"]
            found = (event.get("sglext") or {}).get("spec_tokens_details")
            if found is not None:
                if details is not None:
                    raise ValueError("Duplicate final speculative details")
                details = found
    if not done or first is None:
        raise ValueError("Missing final DONE or token-bearing stream event")
    counts = native_counters(usage, details, gamma)
    if counts["completion_tokens"] != request["output_tokens"]:
        raise ValueError("Measured output length differs with ignore_eos enabled")
    # Input length follows the inherited sampler's tokenizer count. Keep the
    # server's usage count too so any tokenization mismatch remains visible.
    server_input = usage.get("prompt_tokens")
    if type(server_input) is not int or server_input <= 0:
        raise ValueError("Missing final server prompt-token count")
    return {
        **counts,
        "input_tokens": request["input_tokens"],
        "server_input_tokens": server_input,
        "ttft_s": first - start,
        "e2el_s": last - start,
        "tpot_s": (last - first) / (counts["completion_tokens"] - 1),
        "itl_s": intervals,
    }


async def execute(plan, url, served_model, timeout):
    import aiohttp

    concurrency = plan["concurrency"]
    gamma = 5 if plan["model_id"] == "dsv41" else 3
    semaphore = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=timeout),
        connector=aiohttp.TCPConnector(limit=concurrency),
    ) as session:

        async def limited(request):
            async with semaphore:
                return await request_one(session, url, request, served_model, gamma)

        # As in the inherited client, warmups repeat the first measured prompt.
        # Unlike the historical implementation, any failed warmup is fatal.
        warmups = await asyncio.gather(
            *[limited(plan["requests"][0]) for _ in range(2 * concurrency)]
        )
        start = time.perf_counter()
        outputs = await asyncio.gather(*[limited(row) for row in plan["requests"]])
        duration = time.perf_counter() - start
    return outputs, duration, len(warmups)


def summarize(plan, outputs, duration, warmups):
    import numpy as np

    count = len(plan["requests"])
    if len(outputs) != count or count != 10 * plan["concurrency"]:
        raise ValueError("Incomplete measured request set")
    if duration <= 0 or not math.isfinite(duration):
        raise ValueError("Invalid measured duration")
    totals = {
        name: sum(row[name] for row in outputs)
        for name in (
            "input_tokens",
            "completion_tokens",
            "spec_verify_ct",
            "spec_correct_drafts",
            "spec_proposed_drafts",
            "server_input_tokens",
        )
    }
    row = {
        "model_id": plan["model_id"],
        "concurrency": plan["concurrency"],
        "tp": 8,
        "ep": 8,
        "dp": 8,
        "requested": count,
        "completed": count,
        "failed": 0,
        "warmup_requested": 2 * plan["concurrency"],
        "warmup_completed": warmups,
        "warmup_failed": 0,
        "duration_s": duration,
        "input_tokens": totals["input_tokens"],
        "server_input_tokens": totals["server_input_tokens"],
        "output_tokens": totals["completion_tokens"],
        "spec_completion_tokens": totals["completion_tokens"],
        "spec_verify_ct": totals["spec_verify_ct"],
        "spec_correct_drafts": totals["spec_correct_drafts"],
        "spec_proposed_drafts": totals["spec_proposed_drafts"],
        "spec_requested": count,
        "spec_covered": count,
        "request_plan_sha256": sha256(plan),
        "prompt_format": plan["prompt_format"],
        "ordered_lengths_sha256": sha256(
            [
                [r["input_tokens"], r["completion_tokens"], r["server_input_tokens"]]
                for r in outputs
            ]
        ),
        "acceptance_length": totals["completion_tokens"] / totals["spec_verify_ct"],
        "acceptance_rate": totals["spec_correct_drafts"]
        / totals["spec_proposed_drafts"],
    }
    for metric in ("ttft", "tpot", "e2el", "itl"):
        values = (
            [x for r in outputs for x in r["itl_s"]]
            if metric == "itl"
            else [r[metric + "_s"] for r in outputs]
        )
        if not values:
            raise ValueError("Missing streaming latency data")
        row.update(
            {
                f"{stat}_{metric}_ms": float(value) * 1000
                for stat, value in (
                    ("mean", np.mean(values)),
                    ("median", np.median(values)),
                    ("p90", np.percentile(values, 90)),
                    ("p99", np.percentile(values, 99)),
                )
            }
        )
    row.update(
        output_tok_s=totals["completion_tokens"] / duration,
        output_tok_s_gpu=totals["completion_tokens"] / duration / 8,
        interactivity_tok_s_user=1000 / row["median_tpot_ms"],
    )
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--model-id", choices=tuple(PROMPT_FORMATS), required=True)
    prepare.add_argument("--checkpoint", required=True)
    prepare.add_argument(
        "--concurrency", type=int, choices=(1, 2, 4, 8, 16, 32, 64), required=True
    )
    prepare.add_argument("--output", type=Path, required=True)
    run = sub.add_parser("run")
    run.add_argument("--plan", type=Path, required=True)
    run.add_argument("--url", required=True)
    run.add_argument("--served-model", required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--timeout", type=int, required=True)
    args = parser.parse_args()
    if args.command == "prepare":
        plan = prepare_plan(args.model_id, args.checkpoint, args.concurrency)
        with gzip.open(args.output, "xb") as stream:
            stream.write(canonical(plan))
        print(json.dumps({"plan": str(args.output), "sha256": sha256(plan)}))
    else:
        with gzip.open(args.plan, "rb") as stream:
            plan = json.load(stream)
        outputs, duration, warmups = asyncio.run(
            execute(plan, args.url, args.served_model, args.timeout)
        )
        write_json(args.output, summarize(plan, outputs, duration, warmups))
        # Small native counters and latency scalars remain on cluster storage.
        # Do not save generated texts or token-level timing arrays.
        records = [{k: v for k, v in row.items() if k != "itl_s"} for row in outputs]
        with gzip.open(args.output.with_name("requests.json.gz"), "xb") as stream:
            stream.write(canonical(records))
        print(json.dumps({"completed": len(outputs), "duration_s": duration}))


if __name__ == "__main__":
    main()

"""
Simple, no-framework comparison of Gemini vs. the alternate free/minimal-
quota LLM: latency + a manual read of response quality on a couple of
representative prompts. This is deliberately NOT a benchmarking harness —
just enough evidence to honestly back the resume claim of having evaluated
a second LLM, per the project spec ("do not build benchmarking
infrastructure, just a simple comparison").

Also doubles as the project's concurrency demonstration: both providers are
called via asyncio.gather so the two independent network calls run at the
same time rather than one after another — the fair way to time-compare two
unrelated APIs, and a legitimate example of concurrent I/O in this project.

Usage:
    python scripts/compare_llms.py
"""

import asyncio
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.integrations.gemini_client import gemini_client  # noqa: E402
from app.integrations.llm_alt_client import alt_llm_client  # noqa: E402

PROMPTS = [
    "Suggest a healthy breakfast alternative to a sugary cereal, in 2 sentences.",
    "Write a short, friendly good-morning message for a nutrition app user.",
]


async def timed_call(client, prompt: str) -> tuple[str, float]:
    start = time.perf_counter()
    text = await client.generate_text(prompt)
    return text, time.perf_counter() - start


async def main() -> None:
    for prompt in PROMPTS:
        print(f"\nPROMPT: {prompt}")
        (gemini_text, gemini_time), (alt_text, alt_time) = await asyncio.gather(
            timed_call(gemini_client, prompt),
            timed_call(alt_llm_client, prompt),
        )
        print(f"  Gemini  ({gemini_time:.2f}s): {gemini_text[:150]}")
        print(f"  AltLLM  ({alt_time:.2f}s): {alt_text[:150]}")


if __name__ == "__main__":
    asyncio.run(main())

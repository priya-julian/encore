"""Thin LLM client with token metering.

Every call in the app goes through here so the report can quote measured
token counts and real cost per run instead of estimates.
"""
import json
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from openai import OpenAI

from . import config

_client = None
_lock = threading.Lock()


class ContentFiltered(Exception):
    """The provider's own safety filter rejected the prompt.

    Worth its own type: it means a request never reached the model, which is
    a different problem from the model answering badly, and it needs a
    different recovery (isolate the offending input, keep the rest).
    """


def client() -> OpenAI:
    global _client
    with _lock:
        if _client is None:
            _client = OpenAI(
                api_key=config.api_key(),
                base_url=config.PORTKEY_BASE_URL,
                default_headers={"x-portkey-provider": "openai"},
            )
    return _client


@dataclass
class Meter:
    """Accumulates token usage for one pipeline run."""

    calls: list = field(default_factory=list)

    def record(self, agent: str, usage, seconds: float, cached: bool = False):
        self.calls.append(
            {
                "agent": agent,
                "prompt_tokens": getattr(usage, "prompt_tokens", 0) if usage else 0,
                "completion_tokens": getattr(usage, "completion_tokens", 0) if usage else 0,
                "seconds": round(seconds, 2),
                "cached": cached,
            }
        )

    def totals(self) -> dict:
        return {
            "calls": len([c for c in self.calls if not c["cached"]]),
            "cache_hits": len([c for c in self.calls if c["cached"]]),
            "prompt_tokens": sum(c["prompt_tokens"] for c in self.calls),
            "completion_tokens": sum(c["completion_tokens"] for c in self.calls),
            "seconds": round(sum(c["seconds"] for c in self.calls), 2),
            "by_agent": self._by_agent(),
        }

    def _by_agent(self) -> dict:
        out: dict = {}
        for c in self.calls:
            slot = out.setdefault(c["agent"], {"prompt": 0, "completion": 0, "calls": 0})
            slot["prompt"] += c["prompt_tokens"]
            slot["completion"] += c["completion_tokens"]
            slot["calls"] += 1
        return out

    def dump(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as fh:
            fh.write(json.dumps({"ts": time.time(), **self.totals()}) + "\n")


def complete(agent: str, system: str, user: str, meter: Meter | None = None,
             json_mode: bool = False) -> str:
    """One chat completion, metered.

    gpt-6-luna only accepts the default temperature, so it is not set here.
    """
    started = time.time()
    kwargs = {
        "model": config.MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        resp = client().chat.completions.create(**kwargs)
    except Exception as exc:
        if "content_filter" in str(exc) or "content management policy" in str(exc):
            raise ContentFiltered(str(exc)[:200]) from exc
        raise
    if meter is not None:
        meter.record(agent, getattr(resp, "usage", None), time.time() - started)
    return resp.choices[0].message.content or ""

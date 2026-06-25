"""LLM provider abstraction.

The app makes two kinds of LLM call — the appraisal parse (engine/evaluator.py)
and the agent reply (agents/agent.py). Both used to talk to Groq directly. This
layer lets us swap the backend without touching engine/agent code:

    LLM_PROVIDER=groq    (default)  cloud, smart — for dev + system-prompt tuning
    LLM_PROVIDER=ollama             local, small — for the offline / live demo

Both providers expose the same `chat(messages, ...) -> str`. The Groq path is
byte-identical to the old direct calls, so leaving LLM_PROVIDER unset changes
nothing.
"""
from __future__ import annotations

import json
import os
import urllib.request
from abc import ABC, abstractmethod

# Defaults are overridable via env so non-coders can retune without edits.
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
# qwen2.5:3b (~1.9 GB Q4) fits a 4 GB GPU and is far better at the appraisal
# JSON + emotional nuance than a 1B. Set OLLAMA_MODEL=llama3.2:1b for a lighter,
# faster-but-dumber fallback on weaker hardware.
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


class LLMProvider(ABC):
    """A minimal chat interface every backend implements."""

    @abstractmethod
    def chat(self, messages: list[dict], *, temperature: float = 0.8,
             max_tokens: int = 256) -> str:
        """Run a chat completion and return the assistant's reply text."""
        raise NotImplementedError


class GroqProvider(LLMProvider):
    def __init__(self, model: str | None = None):
        from groq import Groq  # imported lazily so an Ollama-only setup needs no key

        self.model = model or os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    def chat(self, messages, *, temperature=0.8, max_tokens=256) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content.strip()


class OllamaProvider(LLMProvider):
    """Talks to a local Ollama server over its native /api/chat HTTP endpoint.

    Uses urllib from the stdlib so we add no dependency.
    """

    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        self.host = (host or os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)).rstrip("/")

    def chat(self, messages, *, temperature=0.8, max_tokens=256) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read())
        return data["message"]["content"].strip()


def get_provider(model: str | None = None) -> LLMProvider:
    """Build the provider selected by the LLM_PROVIDER env var (default: groq).

    `model` only applies to Groq (where callers pass an explicit model); Ollama
    reads its model from OLLAMA_MODEL so the two never get crossed.
    """
    name = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
    if name == "ollama":
        return OllamaProvider()
    return GroqProvider(model=model)

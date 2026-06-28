"""Per-session conversational memory + retrieval (RAG, epic #22).

The decision note (#23 ADR) lives in BUILD_NOTES.md. In short:

  * Store: in-memory list, scoped to a ChatSession. This is a single-user local
    demo (like GAME/CHAT in server.py), so per-process memory already "survives
    across requests in a session" (#24) without SQLite. Swap-in point is small.
  * Embeddings: Ollama `nomic-embed-text` over stdlib urllib — no new dependency,
    no API key, runs offline (#25). Cosine similarity in pure Python.
  * Fallback: if embeddings are unavailable (model not pulled / Ollama down /
    Groq-only box), retrieval degrades to token-overlap scoring so the demo never
    breaks. We log which path is live.

Retrieved context is injected into the system prompt with a character budget
(#26) and surfaced in the UI debug panel (#27).
"""
from __future__ import annotations

import json
import math
import os
import re
import urllib.request
from collections import Counter

EMBED_MODEL = os.environ.get("EMBED_MODEL", "nomic-embed-text")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def _embed(text: str) -> list[float] | None:
    """Embed one string via Ollama. Returns None on any failure (caller falls back)."""
    try:
        req = urllib.request.Request(
            f"{OLLAMA_HOST}/api/embeddings",
            data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            vec = json.loads(r.read()).get("embedding")
        return vec if vec else None
    except Exception:
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


_WORD = re.compile(r"\w+", re.UNICODE)


def _tokens(text: str) -> Counter:
    return Counter(_WORD.findall(text.lower()))


def _overlap(a: Counter, b: Counter) -> float:
    """Cosine over token counts — the embedding-free fallback similarity."""
    inter = sum((a & b).values())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return inter / (na * nb) if na and nb else 0.0


class SessionMemory:
    """Stores conversation memory items and retrieves the top-k relevant to a query."""

    def __init__(self, budget_chars: int = 600):
        self.items: list[dict] = []          # {text, embedding|None, tokens}
        self.budget_chars = budget_chars     # token budget for injected context (#26)
        self.backend = "none"                # "embeddings" | "keyword" — for UI/debug

    def add(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        emb = _embed(text)
        self.backend = "embeddings" if emb else "keyword"
        self.items.append({"text": text, "embedding": emb, "tokens": _tokens(text)})

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        """Return up to k most-relevant stored items as {text, score}, best first.

        Call this *before* storing the current turn, so the query never matches
        itself.
        """
        pool = self.items
        if not pool or not query.strip():
            return []

        q_emb = _embed(query)
        if q_emb and all(it["embedding"] for it in pool):
            scored = [(it, _cosine(q_emb, it["embedding"])) for it in pool]
        else:
            q_tok = _tokens(query)
            scored = [(it, _overlap(q_tok, it["tokens"])) for it in pool]

        scored.sort(key=lambda s: s[1], reverse=True)
        return [{"text": it["text"], "score": round(score, 3)}
                for it, score in scored[:k] if score > 0.0]

    def context_block(self, query: str, k: int = 3) -> tuple[str, list[dict]]:
        """Build the prompt-ready context string (within budget) + the raw hits
        (for the debug panel). Returns ("", []) when nothing relevant."""
        hits = self.retrieve(query, k)
        if not hits:
            return "", []
        lines, used = [], 0
        for h in hits:
            line = f"- {h['text']}"
            if used + len(line) > self.budget_chars:
                break
            lines.append(line)
            used += len(line)
        return "\n".join(lines), hits


if __name__ == "__main__":
    # ponytail: self-check — fallback retrieval ranks the relevant item first.
    m = SessionMemory()
    for t in ["The customer's card was blocked at a shop.",
              "We discussed weekend football plans.",
              "He is worried about losing his savings to fraud."]:
        m.add(t)
    hits = m.retrieve("My card got declined, I'm furious", k=2)
    assert hits, "expected at least one hit"
    assert "card" in hits[0]["text"].lower(), f"bad top hit: {hits}"
    blk, raw = m.context_block("fraud on my account", k=2)
    assert "savings" in blk.lower(), f"context missing fraud item: {blk}"
    print(f"OK — backend={m.backend}; top hit: {hits[0]}")

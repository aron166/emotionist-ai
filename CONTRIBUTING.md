# Contributing to Emotionist.ai

Thanks for taking a look. This is a focused demo project, not a sprawling
framework — the goal is that you can clone it and *get it* in a few minutes.

## Setup

```sh
./run.sh        # Linux/macOS  (run.bat on Windows)
```

That's the whole loop: it builds the venv, installs deps, and starts the app at
http://127.0.0.1:8000. See the [README](README.md#installation) for backend config.

Run a module's self-check directly (each non-trivial module has one):

```sh
.venv/bin/python -m agents.personas      # validates the persona registry
.venv/bin/python -m engine.memory        # validates RAG retrieval + fallback
```

## Module map (where things live)

| File | Responsibility |
|------|----------------|
| `emotions/` | `Emotion` base + 30 positive/negative subclasses |
| `entity/entity.py` | `Entity` owns the emotions; `personality_score`, decay, reactivity |
| `engine/evaluator.py` | LLM call: message text → structured appraisal event |
| `engine/appraisal.py` | OCC rules + witness/empathy track + transition cascades |
| `engine/prompt_modifier.py` | Emotion state (+ retrieved context) → first-person system prompt |
| `engine/memory.py` | Per-session RAG: store turns, retrieve top-k relevant |
| `llm/providers.py` | Groq + Ollama backends; runtime-switchable model registry |
| `agents/agent.py` | The full per-turn pipeline |
| `agents/personas.py` | **Scenario presets** — the counterparts you practice against |
| `server.py` | FastAPI: drives the agents, serves `web/`, JSON state API |
| `web/` | Vanilla HTML/CSS/JS frontend (no build step) |

## How to add a practice persona

A persona is a *recipe for a whole agent* — who they are, how reactive, and what
emotions they start with. Adding one is pure data, no engine changes.

1. **Open** [`agents/personas.py`](agents/personas.py).
2. **Add an entry** to the `SCENARIOS` dict:

   ```python
   "impatient_manager": ScenarioPersona(
       id="impatient_manager",
       display_name="Türelmetlen vezető",          # shown in the picker
       role="impatient manager rushing a decision",
       situation="Azonnali döntést követel, nincs ideje a részletekre.",
       category="hr",                               # customer_support | hr | onboarding
       personality_score=-0.4,   # -1 neurotic … +1 resilient (drives decay)
       reactivity=1.3,           # how hard emotions spike (peak, not duration)
       base_persona=(
           "Te egy türelmetlen vezető vagy egy megbeszélésen. Gyors, határozott "
           "döntéseket vársz, és bosszant, ha valaki köntörfalaz. Magyarul beszélsz."
       ),
       seed_emotions={"Reproach": 0.4, "Anticipation": 0.3},  # starting state
   ),
   ```

3. **Validate:** `.venv/bin/python -m agents.personas` — it should list your new persona.
4. **Use it:** restart the app, open `/chat`, and pick it from the scenario dropdown.

Notes:
- `personality_score` maps to one of the three engine presets (neurotic / average /
  resilient) for now — `≤ -0.33` neurotic, `≥ +0.33` resilient, else average.
- `seed_emotions` keys must be valid emotion names (see `entity/entity.py`).
- Keep `base_persona` about *who they are and the situation* — the emotional tone is
  added automatically by `PromptModifier` from their live state.

## Style

- Match the surrounding code: small, legible, no speculative abstraction.
- Non-trivial logic gets one runnable self-check in `if __name__ == "__main__"`.
- This is a showcase demo — favor clarity over cleverness.

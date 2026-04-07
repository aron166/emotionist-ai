
## What this project is

Emotionist.ai is a computational emotion modeling demo. The core idea: AI agents don't just respond to words — they appraise events, accumulate emotional states over time, and have their language shaped by how they feel. A neurotic agent hit with bad news will still be distressed three turns later. A resilient one bounces back fast.

The theoretical backbone is the **OCC (Ortony, Clore & Collins) appraisal model**, which defines 22 emotions triggered by structured appraisals of events (desirability, praiseworthiness, agency, etc.). The numeric ground truth — emotion intensities, behavioral profiles, decay curves, transition probabilities — all comes from actual research.

**This is a demo, not a library.** Decisions favor legibility and showcase value over robustness.

## Running the project

```bash
pip install -r requirements.txt        # groq, python-dotenv, streamlit
cp .env.example .env                   # add GROQ_API_KEY
python -m streamlit run app.py         # full Streamlit UI (use python -m, not just streamlit)
python main.py                         # CLI two-agent loop (no UI)
```

The `streamlit` binary may not be on PATH after pip install — always use `python -m streamlit run app.py`.

## Architecture

Every turn, each agent runs this pipeline:

```
incoming message (text)
  → AppraisalEvaluator  (1 Groq call)
  → structured event: {event_type, severity, directed_at_self, intentional}
  → OCCAppraisalEngine.compute_deltas(event, entity, witness_event)
      ├─ primary track:  OCC rules on the incoming message event
      └─ witness track:  empathy deltas from sender's last_event (what agent witnessed)
  → merged emotion deltas → Entity.apply_deltas()
  → OCCAppraisalEngine.apply_transitions()  (probabilistic emotion cascade)
  → Entity.decay_all()  (per-emotion exponential decay: base_rate × category_modifier)
  → PromptModifier.build_system_prompt()
  → Groq LLM call with emotionally-shaped system prompt
  → reply
```

## Key design choices — read before editing anything

### 1. `personality_score` is the source of truth for personality

Each `Entity` has a `personality_score` float in `[-1.0, +1.0]`. Named presets map to:
- `"neurotic"` → -1.0
- `"average"` → 0.0
- `"resilient"` → +1.0

Decay rate is derived from this score via `_score_to_decay()` (piecewise linear: −1→0.05, 0→0.12, +1→0.22). **Do NOT use `DECAY_RATES[personality]` as the source of truth** — it is kept only as a UI reference dict. The live base decay rate is always computed from `personality_score`.

`personality_label` is a **computed property**, not a stored field — it derives "neurotic / average / resilient" dynamically from the current score (≤−0.33, ≥+0.33, else average). Already wired for when the score starts drifting.

### 2. Emotion decay = base rate × category modifier

The final `decay_rate` baked into each `Emotion` instance at construction is:

```
_score_to_decay(personality_score) × DECAY_CATEGORY_MODIFIER.get(emotion_name, 1.0)
```

`DECAY_CATEGORY_MODIFIER` lives in `entity.py` (exported). Values < 1.0 = stickier; > 1.0 = more fleeting. Current assignments:

| Modifier | Emotions |
|----------|----------|
| 0.30 | Distress, Sadness, FearsConfirmed |
| 0.40 | Disappointment, Love, Hate |
| 0.50 | Remorse, Trust |
| 0.55 | Shame, Guilt |
| 0.60 | Pride, Resentment |
| 0.65 | Envy |
| 0.80 | Fear |
| 1.00 | Anger, Reproach, Joy, Hope, Pity, Admiration, and all others (default) |
| 1.40 | Relief |
| 1.50 | Surprise |

This is a theoretical extension beyond OCC — the model does not define differential decay by emotion type.

**When Step 4 (drift mechanic) is implemented:** updating `personality_score` at runtime requires also updating all `emotion.decay_rate` values. The formula is the same: `_score_to_decay(new_score) * DECAY_CATEGORY_MODIFIER.get(name, 1.0)` for each emotion in `entity.emotions`.

### 3. Reactivity is independent of decay

`REACTIVITY` dict in `appraisal.py` holds personality defaults (`neurotic=1.4, average=1.0, resilient=0.75`). Each agent stores `entity.reactivity` set at construction (overridable via `Agent(reactivity=...)` kwarg). `compute_deltas()` multiplies all deltas by `entity.reactivity` before returning. Decay controls duration; reactivity controls peak. Independent axes.

### 4. The witness/empathy track

**Why it exists:** The appraisal evaluator reads surface language. If a message is calm in tone, it gets tagged low-severity or neutral — even if the underlying event is emotionally significant. This meant agents weren't emotionally affected by what they *witnessed*, only by what was *said*.

**How it works:** `compute_deltas(event, entity, witness_event=None)` accepts the sender's `last_event` as a third argument. This is already computed; no extra LLM call. Witness deltas are scaled at 0.55× severity and fire based on what the sender experienced, regardless of how they phrased their response.

Witness mappings:
- Sender experienced `bad_news / failure / threat` (directed at self) → responder gets `Pity`, `Distress`, `Guilt` (failure only)
- Sender was `insult`ed intentionally → `Pity`, `Reproach`
- Sender received `good_news / achievement` → `HappyFor`, `Joy`
- Sender received `compliment` → `HappyFor`

`sender.last_event` is passed in `do_turn()` in `app.py` and both turn-execution paths in `pages/2_🎬_Scenarios.py`. The Chat page has no second agent — `witness_event` stays `None` there.

### 5. `Agent.last_event` has two consumers

Populated after every `receive_and_respond()` call. Do not remove:
1. UI — appraisal event badge display (event type, severity, flags)
2. Turn engine — passed as `witness_event` to the other agent's next `receive_and_respond()`

### 6. Slider guard in app.py

The timeline scrubber only renders when `n_msgs > 1`. Streamlit raises `StreamlitAPIException` when `min_value == max_value` on a slider — with one message, both bounds would be 1.

### 7. Emotions are first-person experiences in the prompt

`PromptModifier` doesn't say "aggression: high." It says *"You are angry right now — genuinely, physically angry."* Each of the ~30 emotions has a distinct visceral description in `EMOTION_EXPERIENCES`. The LLM inhabits the state rather than following abstract rules.

### 8. Compound emotions fire directly

Anger, Gratification, Gratitude, Remorse are activated directly in `appraisal.py` when both component conditions fire simultaneously. They are not derived from simpler emotions at runtime.

---

## Module map

| File | Responsibility |
|------|---------------|
| `emotions/emotion.py` | Base `Emotion` class. Fields: `name, valence, intensity, decay_rate, max_duration, time_active, is_active`. Decay: `intensity *= exp(-decay_rate)` per step. `decay_rate` is a plain mutable float. |
| `emotions/positive.py` | 13 positive emotion subclasses |
| `emotions/negative.py` | 17 negative emotion subclasses |
| `entity/entity.py` | `Entity` owns all ~30 emotions. Key fields: `personality_score`, `reactivity`, `personality` (initial string label only). Key functions: `_score_to_decay(score)`, `DECAY_CATEGORY_MODIFIER` (both module-level, exported). Key property: `personality_label`. Key methods: `apply_deltas()`, `decay_all()`, `get_active_emotions()`, `display_state()`. |
| `engine/evaluator.py` | `AppraisalEvaluator` — one Groq call, parses text → `{event_type, severity, directed_at_self, intentional}` |
| `engine/appraisal.py` | `OCCAppraisalEngine` — OCC rules + witness empathy track in `compute_deltas(event, entity, witness_event)`. `REACTIVITY` dict (personality defaults). `apply_transitions()` for cascades. |
| `engine/prompt_modifier.py` | `PromptModifier` — emotion state → first-person system prompt. Exports `BEHAVIORAL_PROFILES`, `NEUTRAL_PROFILE`, `_weighted_params`, `_describe_level` for UI use. |
| `agents/agent.py` | `Agent` — full pipeline. `receive_and_respond(incoming_message, witness_event=None)`. Stores `last_event`. Constructor: `Agent(name, personality, base_persona, model, reactivity=None)`. |
| `app.py` | Flagship two-agent demo. `init_state()` reads `alex_reactivity` / `sam_reactivity` from session state. `do_turn()` passes `sender.last_event` as `witness_event`. Timeline scrubber (n_msgs > 1 guard). Reactivity expander. |
| `pages/1_💬_Chat.py` | Single-agent chat. Sidebar: reactivity slider (key tied to personality, auto-resets default on personality change). State panel shows λ and reactivity. |
| `pages/2_🎬_Scenarios.py` | Two-agent scene builder. Reactivity sliders in agent config. Both `Next Turn` and `Run N Turns` pass `sender.last_event` as `witness_event`. |
| `main.py` | CLI demo — no UI, prints emotional state each turn |

---

## Streamlit UI — three pages

1. **app.py** — Flagship demo. Alex (neurotic) vs Sam (resilient). Preset starters, next-turn / run-6-turns, inject, emotion bars, behavioral profile chips, timeline scrubber, reactivity expander.

2. **💬 Chat** — Single-agent chat. Sidebar: name, personality, reactivity, persona, pre-seed emotions, system prompt toggle. State panel: live emotion bars, decay rate, reactivity multiplier.

3. **🎬 Scenarios** — Full scene designer. Both agents configurable (name, personality, reactivity, persona, seed emotions). Five built-in presets. Auto-run 2–20 turns. Mid-conversation injection.

---

## In-progress extension — dynamic personality

`personality_score` is currently fixed at the value set by the initial preset. The architecture is prepared for it to drift.

**Step 1 (done):** `personality_score` is the source of truth. Decay rate derives from it via `_score_to_decay()`. `personality_label` is a computed property. The named presets are anchors, not lookups.

**Step 2 (pending):** Derive `entity.reactivity` from `personality_score` dynamically. Currently reactivity is set once at `Agent.__init__` and never updated.

**Step 3 (pending):** Derive transition probabilities in `apply_transitions()` from `personality_score`. Neurotic agents should be more likely to route Shame → Anger (externalization); resilient agents more likely to route Shame → Sadness (internalization).

**Step 4 (pending):** After each `decay_all()` call, nudge `personality_score` by ~0.01 based on which emotions were active that turn. Shame/Distress active → drift negative. Joy/Gratitude active → drift positive. Also update all `emotion.decay_rate` values to match the new score × category modifier. This makes personality a consequence of emotional history.

**Implementation rule:** do Steps 2–4 one at a time. Run the workplace conflict scenario between each step to observe what each change does in isolation before adding the next.

---

## Ground-truth research data

All numeric values originate from data objects in `.claude/Home.tsx`. Read that file before changing any constants.

| Object | Used in |
|--------|---------|
| `occ22Emotions` | Emotion subclasses, appraisal rules |
| `behavioralProfiles` | `BEHAVIORAL_PROFILES` dict in `prompt_modifier.py` |
| `emotionTransitions` | `_transition_rules()` in `appraisal.py` |
| `intensityDecayData` | Anchor points in `_score_to_decay()` (0.05 / 0.12 / 0.22) |

`DECAY_CATEGORY_MODIFIER` values are **not** from the research data — they are psychologically reasoned extensions. Do not treat them as ground truth; they are tunable.

---

## OCC emotion categories (for reference when editing appraisal rules)

- **Consequences of Events**: Joy, Distress, Hope, Fear, Satisfaction, FearsConfirmed, Relief, Disappointment, HappyFor, Pity, Gloating, Resentment
- **Actions of Agents**: Pride, Shame, Admiration, Reproach
- **Aspects of Objects**: Love, Hate
- **Compound** (both components must fire): Gratification (Pride+Joy), Remorse (Shame+Distress), Gratitude (Admiration+Joy), Anger (Reproach+Distress from intentional other-agency)

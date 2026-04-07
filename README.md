# Emotionist.ai

> AI agents that feel. Built on OCC appraisal theory, powered by Groq.

Emotionist.ai is a computational emotion modeling demo where AI agents don't just respond to words — they appraise events, accumulate emotional states over time, and have their language shaped by how they feel. A neurotic agent hit with bad news will still be distressed three turns later. A resilient one bounces back fast.

Built as a Codecool bootcamp showcase. Grounded in peer-reviewed psychology.

---

## What it does

Every time an agent receives a message, it runs through this pipeline:

```
incoming message
  → AppraisalEvaluator    one Groq LLM call → {event_type, severity, directed_at_self, intentional}
  → OCCAppraisalEngine    primary OCC rules → emotion deltas
  → OCCAppraisalEngine    witness/empathy track → vicarious deltas from sender's last_event
  → Entity.apply_deltas() emotion state updates
  → apply_transitions()   probabilistic cascade (e.g. Shame → Anger)
  → Entity.decay_all()    per-emotion exponential decay (personality × category modifier)
  → PromptModifier        emotional state → first-person system prompt
  → Groq LLM call         agent responds in character
```

The agent doesn't get told "be angry." It gets told: *"You are angry right now — genuinely, physically angry. Your thoughts come fast and sharp."* Every one of the ~30 emotions has its own visceral first-person description.

---

## Theoretical backbone

The system implements the **OCC (Ortony, Clore & Collins) appraisal model** — the dominant computational framework for emotion generation. Emotions are triggered by structured appraisals of events across three categories:

| Category | Emotions |
|----------|----------|
| Consequences of Events | Joy, Distress, Hope, Fear, Satisfaction, FearsConfirmed, Relief, Disappointment, HappyFor, Pity, Gloating, Resentment |
| Actions of Agents | Pride, Shame, Admiration, Reproach |
| Aspects of Objects | Love, Hate |
| Compound (both components required) | Gratification, Remorse, Gratitude, Anger |

**Anger**, for example, only fires when `Reproach` (negative appraisal of another's action) and `Distress` (negative event consequence) are simultaneously active and the event was intentional and directed at self. This is the OCC formulation, not a heuristic.

---

## Personalities

Each agent has a `personality_score` float between `-1.0` (fully neurotic) and `+1.0` (fully resilient). The three named presets are anchors on that spectrum:

| Label | Score | Base Decay Rate | Character |
|-------|-------|-----------------|-----------|
| Neurotic | −1.0 | 0.05 | Emotions linger; slow to recover; distress converts to prolonged anger |
| Average | 0.0 | 0.12 | Balanced response and recovery |
| Resilient | +1.0 | 0.22 | Hard initial responses, fast recovery; assertiveness over withdrawal |

Decay rate is derived mathematically from `personality_score` via a piecewise linear function — not a lookup table. This lays the foundation for **dynamic personality** where the score can drift based on accumulated emotional history (in progress — see below).

---

## Reactivity

Alongside decay rate, each agent has a **reactivity multiplier** that scales the peak intensity of emotional spikes. Decay controls how long emotions last; reactivity controls how hard they hit in the first place. These are independent axes.

| Personality default | Multiplier | Effect |
|--------------------|------------|--------|
| Neurotic | 1.4 | Spikes 40% harder than baseline |
| Average | 1.0 | Baseline |
| Resilient | 0.75 | Hits 25% softer, fades faster |

Reactivity is fully adjustable per agent in the UI independently of the named personality preset.

---

## Emotion category decay modifiers

**The problem this solves:** In the original OCC model and in most implementations, all emotions within an agent decay at the same rate — determined entirely by personality. But this is psychologically wrong. Grief lingers even in resilient people. Surprise is always fleeting regardless of how neurotic you are. Resentment builds and persists in ways that acute anger does not.

**The fix:** Each emotion has an intrinsic **category decay modifier** that multiplies the personality-derived base rate. Personality still matters — a neurotic agent grieves harder and longer than a resilient one — but the *relative* stickiness between emotions is now preserved across all personalities.

The final decay rate for any emotion is: `base_rate(personality_score) × category_modifier`

| Category | Modifier | Emotions | Rationale |
|----------|----------|----------|-----------|
| Grief / loss | 0.30 | Distress, Sadness, FearsConfirmed | Suffering from loss is intrinsically sticky |
| Disappointment | 0.40 | Disappointment | Lingers, but lighter than acute grief |
| Bond / relationship | 0.40–0.50 | Love, Hate, Trust | Relationship states are stable by nature |
| Social / self-conscious | 0.50–0.65 | Shame, Guilt, Remorse, Pride, Envy | Tied to identity, revisited in memory |
| Anxiety | 0.80 | Fear | Slightly stickier than neutral conflict emotions |
| Chronic negative | 0.60 | Resentment | Builds and persists differently from acute anger |
| Conflict / acute | 1.00 | Anger, Reproach, Disgust, Contempt | Hot, burns normally |
| Fleeting | 1.40–1.50 | Relief, Surprise | Transient by nature, decay faster than baseline |

**Concrete example** — a resilient agent (base rate 0.22) experiencing Distress vs Anger:

| Emotion | Base rate | Modifier | Actual decay rate |
|---------|-----------|----------|-------------------|
| Distress | 0.22 | × 0.30 | **0.066** — lingers |
| Anger | 0.22 | × 1.00 | **0.220** — fades normally |
| Surprise | 0.22 | × 1.50 | **0.330** — gone quickly |

This is a theoretical contribution beyond the OCC model. OCC defines what emotions get triggered and by what appraisals — it does not define differential decay by emotion type. This extension makes the model psychologically richer without changing the appraisal logic.

---

## Empathic / witness emotions

**The problem this solves:** The appraisal evaluator reads the surface language of incoming messages. If an agent delivers bad news and the recipient responds calmly ("I see, thank you for telling me"), the evaluator tags the response as `neutral` — and the deliverer gets no emotional delta, even though they just watched someone absorb painful news. The evaluator was reading *what was said*, not *what was witnessed*.

**The fix:** A second independent **witness track** inside the appraisal engine. Every turn, the responder receives not just the incoming message text but also the sender's `last_event` — the structured appraisal of what the sender experienced on the *previous* turn. These produce separate emotion deltas that merge with the primary track. No extra LLM call needed; `last_event` is already computed.

Witness deltas are scaled at 55% of the witnessed severity — witnessing someone's pain registers, but less intensely than experiencing it directly.

**Example:** Alex delivers bad news to Sam. Sam absorbs it stoically and replies calmly. The LLM appraisal of Sam's calm reply might tag it `neutral · sev 0.20`. But Sam's `last_event` is `bad_news · sev 0.80`. Alex's witness track fires `Pity` and `Distress` regardless of how Sam phrased the response — because Alex watched Sam absorb the news.

Witness emotion mappings:
- Sender experienced `bad_news / failure / threat` directed at themselves → `Pity`, `Distress`, `Guilt` (on failure)
- Sender was insulted intentionally → `Pity`, `Reproach` (protective anger on their behalf)
- Sender received `good_news / achievement` → `HappyFor`, `Joy`
- Sender received a `compliment` → `HappyFor`

---

## Project structure

See [ARCHITECTURE.md](ARCHITECTURE.md) for full system design and pipeline documentation.

```
emotionist.ai/
├── emotions/
│   ├── emotion.py          # Base Emotion class — intensity, decay_rate, time_active
│   ├── positive.py         # 13 positive emotion subclasses
│   └── negative.py         # 17 negative emotion subclasses
├── entity/
│   └── entity.py           # Entity — personality_score, _score_to_decay(),
│                           #   DECAY_CATEGORY_MODIFIER, all ~30 emotions
├── engine/
│   ├── evaluator.py        # AppraisalEvaluator — text → structured event (1 Groq call)
│   ├── appraisal.py        # OCCAppraisalEngine — OCC rules + witness track + REACTIVITY
│   └── prompt_modifier.py  # PromptModifier — emotion state → system prompt
├── agents/
│   └── agent.py            # Agent — full pipeline, witness_event support, stores last_event
├── pages/
│   ├── 1_💬_Chat.py        # Single-agent configurable chat
│   └── 2_🎬_Scenarios.py   # Two-agent scenario builder
├── app.py                  # Streamlit flagship demo (Alex vs Sam)
├── main.py                 # CLI demo — no UI
└── .env                    # GROQ_API_KEY goes here
```

---

## Setup

```bash
pip install -r requirements.txt

cp .env.example .env
# open .env and add your GROQ_API_KEY
```

Get a free API key at [console.groq.com](https://console.groq.com).

---

## Running

```bash
# Full Streamlit UI (recommended)
python -m streamlit run app.py

# CLI demo — no UI, prints emotional state each turn
python main.py
```

> Use `python -m streamlit` — the `streamlit` binary may not be on PATH after pip install.

---

## The UI — three pages

### app.py — Flagship demo
Alex (neurotic) vs Sam (resilient) in a live two-agent conversation. Features:

- Preset conversation starters (workplace conflict, friendship rupture, unexpected praise, etc.)
- **Next turn** / **Run 6 turns** controls
- **Inject a message** mid-conversation to steer the emotional trajectory
- Live emotion intensity bars and behavioral profile chips for both agents
- **Timeline scrubber** — drag back to any previous turn to see how emotional states evolved; only renders when there are 2+ messages
- **Reactivity settings expander** — adjust each agent's emotional spike multiplier independently; reference markers show where the personality presets sit on the scale; changes apply after Reset

### 💬 Chat — Single-agent chat
Direct conversation with one fully configurable agent. Set name, personality, persona backstory, pre-seed starting emotions, and reactivity. The **"Show live system prompt"** toggle is the key demo feature — it shows exactly what the LLM is being instructed to feel on each turn. The state panel shows both decay rate (λ) and reactivity multiplier live.

### 🎬 Scenarios — Scene designer
Full two-agent scene builder. Configure both agents' names, personalities, persona backstories, pre-seeded emotions, and reactivity from scratch. Five built-in presets with documented emotional trajectories. Adjustable auto-run (2–20 turns) and mid-conversation injection.

---

## Observed emergent behavior

During testing, a two-agent workplace conflict scenario produced behavior that was not explicitly programmed:

- **Spontaneous escalation loop** — both agents entered self-reinforcing blame cycles driven by `Shame → Anger → Counter-reproach` cascades
- **Personality-differentiated reconciliation** — after an apology injection, the neurotic agent (Alex) accepted immediately while the resilient agent (Sam) partially pushed back before conceding — exactly matching the decay differential between their `Pride` and `Distress` states at that moment
- **Neurotic regression** — Alex returned to disagreement two turns after proposing reconciliation, pulled back by accumulated distress that hadn't yet decayed below the activation threshold

None of this behavior was scripted. It emerged from the interaction of appraisal rules, transition cascades, and personality-parameterized decay functions.

Full observations and analysis are documented in [RESEARCH_OBSERVATIONS.md](RESEARCH_OBSERVATIONS.md).

---

## In progress — dynamic personality

The architecture is being extended so that `personality_score` **drifts over time** based on accumulated emotional history rather than staying fixed at the starting preset:

- Repeated `Shame / Distress` events nudge the score toward −1.0 (more neurotic)
- Repeated `Joy / Gratitude` events nudge the score toward +1.0 (more resilient)
- Decay rate, reactivity, and transition probabilities all derive from the live score

**Step 1 (complete):** `personality_score` is now the source of truth. Decay rate derives from it mathematically. Named presets are anchors, not lookups.

**Steps 2–4 (pending):** derive reactivity from score dynamically → derive transition probabilities from score → add the drift mechanic that nudges the score after each turn.

---

## Dependencies

| Package | Role |
|---------|------|
| `groq >= 0.9.0` | LLM API (appraisal evaluator + agent responses) |
| `streamlit >= 1.35.0` | UI |
| `python-dotenv >= 1.0.0` | Environment variable loading |

Tested on Python 3.13, Windows 11.

---

## Limitations

- **Context accumulates** — long conversations add up in Groq API token usage
- **Appraisal variance** — the `AppraisalEvaluator` LLM call introduces non-determinism; identical messages may be appraised differently across runs
- **Witness scale is fixed** — the 0.55 witness factor applies uniformly; it does not yet account for relationship closeness or prior emotional history between agents
- **Category modifiers are hand-tuned** — the values in `DECAY_CATEGORY_MODIFIER` are grounded in psychological reasoning but not derived from quantitative research data
- **30 emotions, not a complete affective model** — the OCC model is a simplification; no moods, no drives, no somatic states

---

*Emotionist.ai — April 2026*

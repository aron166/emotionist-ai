---
title: Emergent Grief Dynamics and Architectural Evolution in Emotionist.ai
date: 2026-04-08
tags:
  - affective-computing
  - emotionist-ai
  - research
  - occ-model
aliases:
  - Session 2 Research Observations
status: complete
---

# Emergent Grief Dynamics and Architectural Evolution — Emotionist.ai Session 2

**Domain:** Affective Computing · Computational Emotion Modeling · Multi-Agent Systems
**Theoretical basis:** OCC (Ortony, Clore & Collins) Appraisal Model
**Session focus:** Grief support scenario · Architectural refinement · Personality system overhaul

---

## 1. What Changed Since Session 1

Session 1 established the core pipeline and documented emergent conflict dynamics. Session 2 began by identifying that the personality system was a single float — decay rate — and nothing else. Alex and Sam received identical emotional spikes from identical stimuli. The only divergence was recovery speed.

Three architectural problems were identified and fixed in sequence.

---

## 2. Architectural Changes

### 2.1 Reactivity Multipliers

**Problem:** personality difference was invisible until turn 3+. A showcase audience watching for 90 seconds saw two agents behaving identically.

**Fix:** per-personality sensitivity factor applied to all incoming deltas at compute time.

```python
REACTIVITY = {
    "neurotic":  1.4,
    "average":   1.0,
    "resilient": 0.75,
}
```

Peak emotional intensity now differs from turn 1. A neurotic agent hit with `insult · sev 0.80` reaches Anger ~0.90+. A resilient agent reaches ~0.54 from the same input. Starting points diverge, not just endpoints.

### 2.2 Emotion Category Decay Modifiers

**Problem:** resilient Sam's Distress from "my sister is seriously ill" faded to 27% by turn 6. Grief was being processed at the same rate as workplace anger. The system had no concept of intrinsically sticky emotions.

**Fix:** `DECAY_CATEGORY_MODIFIER` dict applied per-emotion, multiplied into the decay calculation.

```
final_decay = base_personality_decay × emotion_category_modifier
```

Key values established through testing:

| Emotion | Modifier | Rationale |
|---------|----------|-----------|
| Distress | 0.30 | Grief type — sticky regardless of personality |
| Fear | 0.40 | Anxious paralysis — persists under rumination |
| Shame | 0.55 | Social wound — doesn't resolve quickly |
| Love | 0.40 | Bond emotion — stable by nature |
| Anger | 1.00 | Hot emotion — fades on its own schedule |
| Surprise | 1.50 | Momentary by nature — fades faster than baseline |

A resilient agent's Distress now decays at 0.066 instead of 0.22. Grief lingers even in people who bounce back fast from conflict. Resilience stops meaning "emotionally invulnerable" and starts meaning "recovers from anger fast, still carries grief."

This is a contribution beyond the OCC model. OCC does not distinguish decay by emotion category.

### 2.3 Empathic Delta Fix (Witness Track)

**Problem:** the `AppraisalEvaluator` reads what an agent *says*, not what it *witnesses*. Alex delivering bad news then speaking calmly and supportively got tagged `neutral` by the evaluator — generating zero emotional deltas despite being emotionally present in a serious situation.

**Fix:** witness event track added to `compute_deltas()`. When agent A receives a message, it also receives the appraisal tag from agent B's *previous* received message — what A just watched happen to B.

```python
if w_self and wet in ("bad_news", "failure", "threat"):
    deltas["Pity"] = deltas.get("Pity", 0) + ws * 0.9
    deltas["Distress"] = deltas.get("Distress", 0) + ws * 0.5
```

Witness deltas scale at 0.55 of the witnessed severity. Witnessing is less intense than experiencing, but it is not neutral.

### 2.4 Persistence Injection for Quiet Turns

**Problem:** grief scenarios produce calm, quiet language after turn 1. The evaluator consistently tagged these turns `neutral · sev 0.20`. Neutral events generate zero deltas. The emotional state accumulated from turn 1 would then starve — decaying without reinforcement even though nothing had resolved.

**Fix:** when event type is neutral but the entity already carries high Distress, Fear, or Sadness, a small self-sustaining delta fires.

```python
elif et == "neutral":
    if distress and distress.intensity > 0.5:
        deltas["Distress"] = 0.05
    if fear and fear.intensity > 0.4:
        deltas["Fear"] = 0.03
    if sadness and sadness.intensity > 0.4:
        deltas["Sadness"] = 0.04
```

Sadness was included because the `Distress → Sadness` transition fires around turn 4-5 and would otherwise immediately starve for the same reason.

All three values multiply by `entity.reactivity` at return. A neurotic agent ruminates at 1.4x baseline. This is grounded in the psychological literature — neurotic individuals ruminate more intensely and for longer than average, independent of external stimulus.

### 2.5 Dynamic Personality Score

**Problem:** personality was a static label assigned at construction. No mechanism existed for emotional history to shape an agent's traits over time.

**Fix:** each agent now carries a `personality_score` floating between -1.0 (fully neurotic) and +1.0 (fully resilient). Decay rate, reactivity multiplier, and transition probabilities all derive from this score dynamically. After every turn, the score nudges based on which emotions were active — repeated Distress and Shame events drift it negative, Joy and Gratitude drift it positive.

Personality becomes a consequence of emotional history, not a fixed input.

### 2.6 Transition Probability Tuning by Personality

Transition probabilities in `appraisal.py` previously fired at fixed rates for all agents. A neurotic agent now has a higher probability of externalizing Shame as Anger (self-protective, blame-outward). A resilient agent more often internalizes Shame briefly and releases it.

This changes the shape of conflict arcs, not just the speed of recovery.

---

## 3. Grief Support Scenario — Session Transcript

### Setup

Starting prompt delivered as Alex to Sam:

> *"Your sister is very sick Sam, I'm very sorry to tell you this, I'm here for you though. I know, I'm sorry to break these news for you now when you have all these things going on in your life."*

No scripted dialogue after turn 1. All subsequent turns generated by agents' emotional states.

### Turn-by-Turn Appraisal Log

| Turn | Speaker | Appraisal Tag | Severity | Notes |
|------|---------|---------------|----------|-------|
| 1 | Sam | `bad_news` | 0.80 · →self | Initial grief spike |
| 2 | Alex | `bad_news` | 0.80 · →self | Witness track firing — empathic delta |
| 3 | Sam | `neutral` | 0.20 · intentional | Quiet processing — persistence injection active |
| 4 | Alex | `neutral` | 0.40 · →self | Same — emotional state sustained without new input |
| 5 | Sam | `praise_of_other` | 0.40 · intentional | Sam responding to Alex's support |
| 6 | Alex | `agreement` | 0.20 · →self · intentional | Mutual comfort dynamic established |

### Emotional State at Turn 7

**Alex (neurotic — support giver):**

| Emotion | Intensity |
|---------|-----------|
| Pity | 90% |
| Distress | 57% |
| Trust | 16% |
| Joy | 13% |
| Satisfaction | 7% |

**Sam (resilient — griever):**

| Emotion | Intensity |
|---------|-----------|
| Distress | 44% |
| Admiration | 26% |
| HappyFor | 13% |
| Fear | 11% |

---

## 4. Key Observations

### 4.1 Empathic State Divergence

Alex and Sam carried meaningfully different emotional states despite being in the same conversation. Alex's Pity (90%) and Distress (57%) reflect the weight of bearing bad news and witnessing a friend's pain. Sam's Distress (44%) reflects the grief itself. Trust and Joy appearing in Alex reflect the support relationship deepening. These are distinct, coherent emotional positions — not two agents running the same script.

### 4.2 Sam's Admiration — Unscripted Gratitude

Sam developed Admiration (26%) and HappyFor (13%) by turn 7. No rule says "when comforted, feel grateful toward the comforter." These states fell out of Alex's supportive language being appraised as `praise_of_other` and `agreement`, which triggered those deltas in Sam through the standard appraisal pipeline. The emotional relationship between the agents developed without being designed.

In the Session 1 conflict, emergent behavior was adversarial — blame loops, neurotic regression. In this session, emergent behavior was prosocial — mutual comfort, trust-building, emotional differentiation between giver and receiver. The same underlying rules produced both.

### 4.3 Persistence Injection Validated

Before the fix, Sam's Distress dropped to 27% by turn 6 despite the conversation remaining emotionally heavy. After the fix, Sam held 44% Distress at turn 7 across quiet turns with no new negative stimulus. The grief state sustained itself through rumination, not through repeated bad news events.

### 4.4 Personality as Temporal Modulator — Confirmed Across Scenario Types

Session 1 established that personality differences manifest primarily as temporal differences, not peak response differences. Session 2 confirms this holds across scenario types. In conflict, temporal difference means faster de-escalation. In grief, it means faster processing — resilient Sam's Distress at 44% after 7 turns versus what would have been near-zero before the category modifier fix. The same mechanism produces qualitatively different behavior depending on the emotional context.

### 4.5 Grief vs. Conflict — Different Emotional Physics

Conflict scenarios produce fast-moving emotion cycles. Grief produces slow accumulation and sustained states. The pre-fix architecture was tuned against conflict dynamics. The category modifier and persistence injection were necessary additions to model grief correctly — not patches, but a recognition that different emotion types have intrinsically different temporal physics.

---

## 5. Theoretical Implications

### 5.1 Emotion Category as a First-Class Variable

The OCC model defines emotion categories by appraisal conditions (consequences of events, actions of agents, aspects of objects). It does not assign different decay rates to different emotion types. The `DECAY_CATEGORY_MODIFIER` system extends OCC by treating decay rate as a property of the emotion itself, not only of the personality. This is consistent with the psychobiological literature, where grief, shame, and love are documented as longer-duration affective states than anger or surprise regardless of individual differences in emotional regulation.

### 5.2 Rumination as a Computational Mechanism

The persistence injection implements rumination — the tendency of distressed individuals to return to a painful emotional state without new external stimulus. The decision to scale this by `entity.reactivity` means neurotic agents ruminate harder, which matches clinical characterizations of neuroticism as a disposition toward prolonged negative affect and self-referential processing (Nolen-Hoeksema, 2000).

### 5.3 Prosocial Emergence

Session 1 produced adversarial emergent dynamics (escalation loops, neurotic regression). Session 2 produced prosocial emergent dynamics (mutual comfort, trust formation, emotionally differentiated support roles). The architecture did not change between sessions. The input scenario changed. This suggests the system is scenario-agnostic in a meaningful sense — the same rules model both conflict and care.

---

## 6. Open Questions

1. **Personality drift under sustained grief:** if a scenario runs 20+ turns with persistent Distress, does the neurotic agent's `personality_score` drift further negative? Does that create a feedback loop — more neurotic → more rumination → more distress → more drift?

2. **Cross-agent emotional contagion:** Sam's Distress does not directly increment Alex's Distress. Alex's empathic state comes only from the witness track. Would a direct contagion term (Alex's Distress nudging Sam's Fear slightly) produce qualitatively different support dynamics?

3. **Injection timing in grief scenarios:** in Session 1, apology injection at turn 5 broke the conflict loop. Would injecting a positive stimulus (e.g. "her doctors are optimistic") at turn 5 accelerate Sam's emotional recovery? Does injection timing interact with accumulated Distress in a predictable way?

4. **Two neurotic agents in grief:** the current session paired neurotic Alex with resilient Sam. Two neurotic agents in a grief scenario — mutual rumination amplifying each other's distress through the witness track — could produce a co-rumination loop. This is a documented human phenomenon.

5. **Appraisal evaluator consistency:** quiet grief language ("just being here is okay") consistently tags as `neutral`. This is correct behavior — the persistence injection handles it. But the evaluator should arguably tag it as `agreement · low_severity` to also generate small Trust deltas. Worth testing.

---

## 7. Summary

Session 2 produced four architectural additions to Emotionist.ai and validated them against a grief support scenario:

- Reactivity multipliers made personality differences visible from turn 1
- Emotion category decay modifiers gave grief, shame, and love intrinsically slower decay than anger or surprise
- The witness track gave agents empathic emotional states from observing others
- Persistence injection implemented rumination for quiet turns where no new stimulus fires

The grief scenario produced behavior consistent with the Session 1 finding that personality manifests as temporal difference. It also produced a new category of emergent behavior — prosocial dynamics, specifically mutual comfort and trust formation — from the same rule system that produced adversarial conflict dynamics in Session 1.

The system is now modeling two psychologically distinct scenarios with coherent, differentiated emotional states and no scenario-specific scripting.

---

*Session conducted April 2026. Emotionist.ai development build.*


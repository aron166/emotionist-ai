import random
from entity.entity import Entity


# Emotion transition rules from emotionTransitions research data
# Format: (from_emotion, condition_fn, to_emotion, probability)
def _transition_rules(entity: Entity) -> list[tuple]:
    fear = entity.emotions.get("Fear")
    shame = entity.emotions.get("Shame")
    anger = entity.emotions.get("Anger")
    distress = entity.emotions.get("Distress")
    hope = entity.emotions.get("Hope")
    disappointment = entity.emotions.get("Disappointment")
    joy = entity.emotions.get("Joy")

    return [
        # Fear → Anxiety (prolonged + uncertain): time_active > 3 steps
        (fear, lambda e: e.is_active and e.time_active > 3, "Fear", "Distress", 0.75),
        # Shame → Anger (blame externalized)
        (shame, lambda e: e.is_active and e.intensity > 0.4, "Shame", "Anger", 0.60),
        # Shame → Sadness (internalized + chronic)
        (shame, lambda e: e.is_active and e.time_active > 5, "Shame", "Sadness", 0.55),
        # Anger → Guilt (harm caused to liked agent)
        (anger, lambda e: e.is_active and e.intensity > 0.6, "Anger", "Guilt", 0.50),
        # Distress → Sadness (coping failed + time)
        (distress, lambda e: e.is_active and e.time_active > 4, "Distress", "Sadness", 0.80),
        # Hope → Anticipation (likelihood increases)
        (hope, lambda e: e.is_active and e.intensity > 0.5, "Hope", "Anticipation", 0.70),
        # Disappointment → Resentment (other-agency)
        (disappointment, lambda e: e.is_active and e.intensity > 0.4, "Disappointment", "Resentment", 0.55),
        # Joy → Gratitude (other-agency identified)
        (joy, lambda e: e.is_active and e.intensity > 0.5, "Joy", "Gratitude", 0.65),
    ]


REACTIVITY = {
    "neurotic":  1.4,   # hits harder, spikes higher
    "average":   1.0,
    "resilient": 0.75,  # lower peak, but fades faster too
}


class OCCAppraisalEngine:
    """Maps structured appraisal events to emotion intensity deltas using OCC rules."""

    def compute_deltas(
        self, event: dict, entity: Entity, witness_event: dict = None
    ) -> dict[str, float]:
        """
        Returns a dict of {emotion_name: delta} to apply to the entity.
        event keys: event_type, severity, directed_at_self, intentional

        witness_event: the appraisal event the *sender* experienced receiving the
        previous message (i.e. what this agent just watched happen to the other
        agent). Used to generate empathic / vicarious emotion deltas.
        """
        et = event.get("event_type", "neutral")
        sev = float(event.get("severity", 0.2))
        self_directed = bool(event.get("directed_at_self", False))
        intentional = bool(event.get("intentional", False))

        deltas: dict[str, float] = {}

        if et == "compliment":
            if self_directed:
                deltas["Pride"] = sev * 0.8
                deltas["Joy"] = sev * 0.6
            else:
                deltas["Admiration"] = sev * 0.7
                deltas["HappyFor"] = sev * 0.4

        elif et == "insult":
            if self_directed and intentional:
                # Compound Anger = Reproach + Distress
                deltas["Reproach"] = sev * 0.7
                deltas["Distress"] = sev * 0.6
                deltas["Anger"] = sev * 0.9
            elif self_directed:
                deltas["Distress"] = sev * 0.7
                deltas["Shame"] = sev * 0.4
            else:
                deltas["Reproach"] = sev * 0.5

        elif et == "threat":
            if self_directed:
                deltas["Fear"] = sev * 0.9
                deltas["Distress"] = sev * 0.4
            else:
                deltas["Fear"] = sev * 0.5

        elif et == "good_news":
            if self_directed:
                deltas["Joy"] = sev * 0.9
                deltas["Satisfaction"] = sev * 0.5
            else:
                deltas["HappyFor"] = sev * 0.6
                deltas["Hope"] = sev * 0.3

        elif et == "bad_news":
            if self_directed:
                deltas["Distress"] = sev * 0.9
                deltas["Fear"] = sev * 0.4
            else:
                deltas["Pity"] = sev * 0.5
                deltas["Distress"] = sev * 0.3

        elif et == "achievement":
            if self_directed:
                # Gratification = Pride + Joy (own praiseworthy action)
                deltas["Pride"] = sev * 0.8
                deltas["Joy"] = sev * 0.7
                deltas["Gratification"] = sev * 0.9
            else:
                deltas["Admiration"] = sev * 0.7

        elif et == "failure":
            if self_directed:
                # Remorse = Shame + Distress
                deltas["Shame"] = sev * 0.7
                deltas["Distress"] = sev * 0.6
                deltas["Remorse"] = sev * 0.5
            else:
                deltas["Pity"] = sev * 0.5

        elif et == "agreement":
            deltas["Joy"] = sev * 0.5
            deltas["Trust"] = sev * 0.6
            deltas["Satisfaction"] = sev * 0.3

        elif et == "disagreement":
            deltas["Distress"] = sev * 0.5
            if intentional:
                deltas["Reproach"] = sev * 0.4
                deltas["Resentment"] = sev * 0.3

        elif et == "praise_of_other":
            deltas["Admiration"] = sev * 0.6
            deltas["HappyFor"] = sev * 0.3

        elif et == "blame_of_other":
            deltas["Reproach"] = sev * 0.6
            if self_directed:
                # other's blameworthy action caused harm to self → Anger
                deltas["Anger"] = sev * 0.7

        elif et == "neutral":
            # Rumination / persistence injection: grief and fear sustain themselves
            # without needing a new trigger. Quiet turns in a grief scenario get
            # tagged neutral — this prevents the emotional state from starving.
            distress = entity.emotions.get("Distress")
            fear = entity.emotions.get("Fear")
            sadness = entity.emotions.get("Sadness")
            if distress and distress.intensity > 0.5:
                deltas["Distress"] = 0.05
            if fear and fear.intensity > 0.4:
                deltas["Fear"] = 0.03
            if sadness and sadness.intensity > 0.4:
                deltas["Sadness"] = 0.04

        # ── Witness / empathy track ───────────────────────────────────────────
        # Apply vicarious emotion deltas from what this agent *witnessed* the
        # other agent experience, regardless of what the other agent said.
        # Scaled at ~0.55 of the witnessed severity so witnessing < experiencing.
        if witness_event:
            wet = witness_event.get("event_type", "neutral")
            wsev = float(witness_event.get("severity", 0.0))
            w_self = bool(witness_event.get("directed_at_self", False))
            w_intent = bool(witness_event.get("intentional", False))
            ws = wsev * 0.55  # witness scale factor

            if w_self and wet in ("bad_news", "failure", "threat", "fears_confirmed"):
                # Witnessing someone suffer bad news / failure / threat
                deltas["Pity"] = deltas.get("Pity", 0) + ws * 0.9
                deltas["Distress"] = deltas.get("Distress", 0) + ws * 0.5
                if wet == "failure":
                    # Guilt if this agent may have contributed
                    deltas["Guilt"] = deltas.get("Guilt", 0) + ws * 0.35

            elif w_self and wet == "insult" and w_intent:
                # Witnessing someone get insulted — protective reproach
                deltas["Pity"] = deltas.get("Pity", 0) + ws * 0.7
                deltas["Reproach"] = deltas.get("Reproach", 0) + ws * 0.5

            elif w_self and wet in ("good_news", "achievement"):
                # Witnessing someone receive good news / succeed
                deltas["HappyFor"] = deltas.get("HappyFor", 0) + ws * 0.8
                deltas["Joy"] = deltas.get("Joy", 0) + ws * 0.3

            elif w_self and wet == "compliment":
                deltas["HappyFor"] = deltas.get("HappyFor", 0) + ws * 0.6

        return {name: delta * entity.reactivity for name, delta in deltas.items()}

    def apply_transitions(self, entity: Entity):
        """Check and probabilistically fire emotion transitions."""
        for source_emotion, condition_fn, from_name, to_name, prob in _transition_rules(entity):
            if source_emotion is None:
                continue
            try:
                if condition_fn(source_emotion) and random.random() < prob:
                    carry = source_emotion.intensity * 0.3
                    if to_name in entity.emotions:
                        entity.emotions[to_name].activate(carry)
            except Exception:
                pass

from emotions.positive import (
    Joy, Hope, Satisfaction, Relief, HappyFor,
    Pride, Admiration, Love, Gratification, Gratitude,
    Trust, Surprise, Anticipation,
)
from emotions.negative import (
    Distress, Fear, FearsConfirmed, Disappointment, Pity,
    Gloating, Resentment, Shame, Reproach, Hate,
    Remorse, Anger, Sadness, Disgust, Envy, Guilt, Contempt,
)


_PERSONALITY_SCORES = {"neurotic": -1.0, "average": 0.0, "resilient": 1.0}

# Keep for UI reference / backwards compat
_DECAY_RATES_REF = {"neurotic": 0.05, "average": 0.12, "resilient": 0.22}

# Per-emotion decay modifiers — applied on top of the personality-derived base rate.
# Values < 1.0 make that emotion stickier (slower decay) regardless of personality.
# Values > 1.0 make it more fleeting. Personality still matters; this shifts the floor.
# Exported so the UI can display it.
DECAY_CATEGORY_MODIFIER: dict[str, float] = {
    # Grief / loss — intrinsically sticky. Even resilient agents grieve.
    "Distress":      0.30,
    "Sadness":       0.30,
    "FearsConfirmed":0.30,
    "Disappointment":0.40,

    # Social / self-conscious — tied to identity, linger in memory.
    "Shame":         0.55,
    "Guilt":         0.55,
    "Remorse":       0.50,
    "Pride":         0.60,
    "Envy":          0.65,

    # Bond / relationship — very stable, change slowly.
    "Love":          0.40,
    "Hate":          0.40,
    "Trust":         0.50,

    # Anxiety — slightly stickier than neutral conflict emotions.
    "Fear":          0.80,
    "Resentment":    0.60,

    # Fleeting — transient by nature, decay faster than personality baseline.
    "Surprise":      1.50,
    "Relief":        1.40,

    # Everything else (Joy, Anger, Hope, Pity, Reproach, etc.) uses 1.0 — no entry needed.
}


def _score_to_decay(score: float) -> float:
    """Map personality_score [-1, +1] → decay rate [0.05, 0.22].
    Piecewise linear through the three research anchor points:
      -1.0 → 0.05 (neurotic), 0.0 → 0.12 (average), +1.0 → 0.22 (resilient)
    """
    score = max(-1.0, min(1.0, score))
    if score <= 0:
        return 0.05 + (score + 1.0) * 0.07   # 0.05 … 0.12
    else:
        return 0.12 + score * 0.10            # 0.12 … 0.22


class Entity:
    DECAY_RATES = _DECAY_RATES_REF   # kept for UI / external reads

    def __init__(self, name: str, personality: str = "average", reactivity: float = 1.0):
        if personality not in _PERSONALITY_SCORES:
            raise ValueError(f"personality must be one of {list(_PERSONALITY_SCORES)}")
        self.name = name
        self.personality = personality
        self.personality_score: float = _PERSONALITY_SCORES[personality]
        self.reactivity = reactivity
        base_dr = _score_to_decay(self.personality_score)

        def dr(name: str) -> float:
            return base_dr * DECAY_CATEGORY_MODIFIER.get(name, 1.0)

        self.emotions: dict = {
            # OCC 22
            "Joy":             Joy(dr("Joy")),
            "Hope":            Hope(dr("Hope")),
            "Satisfaction":    Satisfaction(dr("Satisfaction")),
            "Relief":          Relief(dr("Relief")),
            "HappyFor":        HappyFor(dr("HappyFor")),
            "Pride":           Pride(dr("Pride")),
            "Admiration":      Admiration(dr("Admiration")),
            "Love":            Love(dr("Love")),
            "Gratification":   Gratification(dr("Gratification")),
            "Gratitude":       Gratitude(dr("Gratitude")),
            "Distress":        Distress(dr("Distress")),
            "Fear":            Fear(dr("Fear")),
            "FearsConfirmed":  FearsConfirmed(dr("FearsConfirmed")),
            "Disappointment":  Disappointment(dr("Disappointment")),
            "Pity":            Pity(dr("Pity")),
            "Gloating":        Gloating(dr("Gloating")),
            "Resentment":      Resentment(dr("Resentment")),
            "Shame":           Shame(dr("Shame")),
            "Reproach":        Reproach(dr("Reproach")),
            "Hate":            Hate(dr("Hate")),
            "Remorse":         Remorse(dr("Remorse")),
            "Anger":           Anger(dr("Anger")),
            # Extended (from behavioralProfiles)
            "Trust":           Trust(dr("Trust")),
            "Surprise":        Surprise(dr("Surprise")),
            "Anticipation":    Anticipation(dr("Anticipation")),
            "Sadness":         Sadness(dr("Sadness")),
            "Disgust":         Disgust(dr("Disgust")),
            "Envy":            Envy(dr("Envy")),
            "Guilt":           Guilt(dr("Guilt")),
            "Contempt":        Contempt(dr("Contempt")),
        }

    @property
    def personality_label(self) -> str:
        """Human-readable label derived from current personality_score."""
        if self.personality_score <= -0.33:
            return "neurotic"
        elif self.personality_score >= 0.33:
            return "resilient"
        return "average"

    def apply_deltas(self, deltas: dict[str, float]):
        """Apply emotion intensity changes from appraisal."""
        for name, delta in deltas.items():
            if name in self.emotions:
                self.emotions[name].activate(delta)

    def decay_all(self):
        """Advance one time step: decay all active emotions."""
        for emotion in self.emotions.values():
            emotion.decay()

    def get_active_emotions(self) -> list[tuple[str, float]]:
        """Return list of (name, intensity) for all active emotions, sorted by intensity."""
        active = [(e.name, e.intensity) for e in self.emotions.values() if e.is_active]
        return sorted(active, key=lambda x: x[1], reverse=True)

    def get_dominant_emotions(self, n: int = 3) -> list[tuple[str, float]]:
        return self.get_active_emotions()[:n]

    def display_state(self) -> str:
        dominant = self.get_dominant_emotions()
        label = f"{self.personality_label} ({self.personality_score:+.2f})"
        if not dominant:
            return f"{self.name} [{label}]: calm"
        parts = ", ".join(f"{name}={intensity:.2f}" for name, intensity in dominant)
        return f"{self.name} [{label}]: {parts}"

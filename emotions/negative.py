from .emotion import Emotion


class Distress(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Distress", -1, decay_rate)


class Fear(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Fear", -1, decay_rate)


class FearsConfirmed(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("FearsConfirmed", -1, decay_rate)


class Disappointment(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Disappointment", -1, decay_rate)


class Pity(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Pity", -1, decay_rate)


class Gloating(Emotion):
    """Mixed valence: pleased about misfortune of disliked other."""
    def __init__(self, decay_rate: float):
        super().__init__("Gloating", 0, decay_rate)


class Resentment(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Resentment", -1, decay_rate)


class Shame(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Shame", -1, decay_rate)


class Reproach(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Reproach", -1, decay_rate)


class Hate(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Hate", -1, decay_rate)


class Remorse(Emotion):
    """Compound: Shame + Distress (own blameworthy action → undesirable event)."""
    def __init__(self, decay_rate: float):
        super().__init__("Remorse", -1, decay_rate)


class Anger(Emotion):
    """Compound: Reproach + Distress (other's action → undesirable event for self)."""
    def __init__(self, decay_rate: float):
        super().__init__("Anger", -1, decay_rate)


class Sadness(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Sadness", -1, decay_rate)


class Disgust(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Disgust", -1, decay_rate)


class Envy(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Envy", -1, decay_rate)


class Guilt(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Guilt", -1, decay_rate)


class Contempt(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Contempt", -1, decay_rate)

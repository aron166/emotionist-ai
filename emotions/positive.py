from .emotion import Emotion


class Joy(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Joy", 1, decay_rate)


class Hope(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Hope", 1, decay_rate)


class Satisfaction(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Satisfaction", 1, decay_rate)


class Relief(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Relief", 1, decay_rate)


class HappyFor(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("HappyFor", 1, decay_rate)


class Pride(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Pride", 1, decay_rate)


class Admiration(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Admiration", 1, decay_rate)


class Love(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Love", 1, decay_rate)


class Gratification(Emotion):
    """Compound: Pride + Joy (own praiseworthy action -> desirable event)."""
    def __init__(self, decay_rate: float):
        super().__init__("Gratification", 1, decay_rate)


class Gratitude(Emotion):
    """Compound: Admiration + Joy (other's action -> desirable event for self)."""
    def __init__(self, decay_rate: float):
        super().__init__("Gratitude", 1, decay_rate)


class Trust(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Trust", 1, decay_rate)


class Surprise(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Surprise", 1, decay_rate)


class Anticipation(Emotion):
    def __init__(self, decay_rate: float):
        super().__init__("Anticipation", 1, decay_rate)

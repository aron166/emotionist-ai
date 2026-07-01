import math


class Emotion:
    # Intensity below this is treated as "not felt": the emotion deactivates
    # on decay and does not activate on tiny deltas.
    ACTIVATION_THRESHOLD = 0.05

    def __init__(self, name: str, valence: int, decay_rate: float, max_duration: int = 20):
        self.name = name
        self.valence = valence        # 1 = positive, -1 = negative, 0 = mixed
        self.intensity = 0.0
        self.decay_rate = decay_rate  # set by Entity based on personality
        self.max_duration = max_duration
        self.time_active = 0
        self.is_active = False

    def activate(self, delta: float):
        """Adjust intensity by delta - positive raises it, negative soothes it -
        clamped to [0, 1]. Drops to fully inactive when it falls to a non-felt level."""
        self.intensity = max(0.0, min(1.0, self.intensity + delta))
        if self.intensity <= self.ACTIVATION_THRESHOLD:
            self.intensity = 0.0
            self.is_active = False
            self.time_active = 0
        else:
            self.is_active = True

    def decay(self):
        """Apply one step of exponential decay."""
        if not self.is_active:
            return
        self.time_active += 1
        self.intensity = self.intensity * math.exp(-self.decay_rate)
        if self.intensity < self.ACTIVATION_THRESHOLD or self.time_active >= self.max_duration:
            self.intensity = 0.0
            self.is_active = False
            self.time_active = 0

    def __repr__(self):
        return f"{self.name}({self.intensity:.2f})"

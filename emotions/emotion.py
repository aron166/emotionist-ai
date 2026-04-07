import math


class Emotion:
    def __init__(self, name: str, valence: int, decay_rate: float, max_duration: int = 20):
        self.name = name
        self.valence = valence        # 1 = positive, -1 = negative, 0 = mixed
        self.intensity = 0.0
        self.decay_rate = decay_rate  # set by Entity based on personality
        self.max_duration = max_duration
        self.time_active = 0
        self.is_active = False

    def activate(self, delta: float):
        """Increase intensity by delta, capped at 1.0."""
        self.intensity = min(1.0, self.intensity + delta)
        if self.intensity > 0.05:
            self.is_active = True

    def decay(self):
        """Apply one step of exponential decay."""
        if not self.is_active:
            return
        self.time_active += 1
        self.intensity = self.intensity * math.exp(-self.decay_rate)
        if self.intensity < 0.05 or self.time_active >= self.max_duration:
            self.intensity = 0.0
            self.is_active = False
            self.time_active = 0

    def __repr__(self):
        return f"{self.name}({self.intensity:.2f})"

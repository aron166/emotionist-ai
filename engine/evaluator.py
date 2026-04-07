import json
import os
from groq import Groq


SYSTEM_PROMPT = """You are an emotion appraisal parser. Given a message, output a JSON object with exactly these fields:
- event_type: one of ["compliment", "insult", "threat", "good_news", "bad_news", "achievement", "failure", "agreement", "disagreement", "praise_of_other", "blame_of_other", "neutral"]
- severity: float 0.0 to 1.0 (how emotionally charged the message is)
- directed_at_self: boolean (true if the event is about or aimed at the listener)
- intentional: boolean (true if the action or event was caused deliberately)

Respond ONLY with the JSON object, no explanation."""


class AppraisalEvaluator:
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        self.model = model

    def evaluate(self, message: str) -> dict:
        """Convert raw message text into a structured appraisal event."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            max_tokens=128,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            event = {
                "event_type": "neutral",
                "severity": 0.1,
                "directed_at_self": False,
                "intentional": False,
            }
        return event

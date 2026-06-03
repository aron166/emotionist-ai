import json
import os
from groq import Groq


SYSTEM_PROMPT = """You are an emotion appraisal parser for a two-agent conversation system.

Your job: classify what emotional event the LISTENER experiences when receiving this message.

Rules:
- directed_at_self: true only if the event directly affects the listener's situation, reputation, or wellbeing. NOT true just because someone is talking to them.
- intentional: true if a person deliberately caused the event (not accidents or circumstances)
- severity: 0.0-0.2 = minor, 0.3-0.5 = moderate, 0.6-0.8 = significant, 0.9-1.0 = severe
- Use "neutral" when the message is processing, thinking out loud, or transitional — even if the topic is heavy

Event type definitions:
- bad_news: listener learns of something negative happening TO THEM specifically
- failure: listener failed at something they were responsible for  
- insult: listener is attacked, criticized, or demeaned
- threat: listener faces a warning of future harm
- good_news: listener learns of something positive happening TO THEM
- compliment: listener is praised or appreciated
- achievement: listener accomplished something
- agreement: listener's view or action is validated
- disagreement: listener's view or action is challenged
- praise_of_other: someone else is praised (listener witnesses)
- blame_of_other: someone else is blamed (listener witnesses)
- neutral: transitional, processing, or ambient conversation

Examples:

Message: "You completely dropped the ball on this project."
{"event_type": "insult", "severity": 0.75, "directed_at_self": true, "intentional": true}

Message: "I just got fired today, I don't know what to do."
{"event_type": "bad_news", "severity": 0.85, "directed_at_self": false, "intentional": false}

Message: "Yeah, walking might help clear my head a bit."
{"event_type": "neutral", "severity": 0.10, "directed_at_self": false, "intentional": false}

Message: "Thanks for being here, it means a lot."
{"event_type": "compliment", "severity": 0.45, "directed_at_self": true, "intentional": true}

Message: "Maybe we can figure something out together?"
{"event_type": "agreement", "severity": 0.25, "directed_at_self": false, "intentional": true}

Message: "I heard the client pulled out of the deal entirely."
{"event_type": "bad_news", "severity": 0.70, "directed_at_self": false, "intentional": false}

Message: "You did a great job on that presentation."
{"event_type": "compliment", "severity": 0.60, "directed_at_self": true, "intentional": true}

Message: "I don't know if talking about it will help."
{"event_type": "neutral", "severity": 0.15, "directed_at_self": false, "intentional": false}

Message: "That's really sweet of you, thanks."
{"event_type": "compliment", "severity": 0.35, "directed_at_self": true, "intentional": true}

Message: "Let's just walk and see where we end up."
{"event_type": "neutral", "severity": 0.10, "directed_at_self": false, "intentional": false}

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

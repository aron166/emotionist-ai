import json
import re

from llm import get_provider


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

# Returned when the LLM response cannot be parsed — a low-severity neutral
# event leaves the agent's emotional state effectively untouched.
FALLBACK_EVENT = {
    "event_type": "neutral",
    "severity": 0.1,
    "directed_at_self": False,
    "intentional": False,
}


def _extract_json_object(raw: str) -> dict | None:
    """Pull a JSON object out of an LLM reply.

    Big models return clean JSON; small local models often wrap it in code
    fences or chatter ("Sure! Here you go: {...}"). We try, in order: the whole
    string, the string minus a ```json fence, then the first {...} block we can
    find. Returns the parsed dict, or None if nothing parses.
    """
    raw = raw.strip()

    candidates = [raw]
    if raw.startswith("```"):
        inner = raw.split("```")[1]
        if inner.startswith("json"):
            inner = inner[4:]
        candidates.append(inner.strip())
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


class AppraisalEvaluator:
    def __init__(self, model: str = "llama-3.3-70b-versatile", provider: str | None = None):
        # Appraisal follows the same backend as the reply, so "switch to local"
        # keeps the whole pipeline offline (and parses Hungarian on the same model).
        self.provider = get_provider(model, provider=provider)

    def evaluate(self, message: str) -> dict:
        """Convert raw message text into a structured appraisal event."""
        raw = self.provider.chat(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            max_tokens=128,
        )
        event = _extract_json_object(raw)
        if event is None:
            return dict(FALLBACK_EVENT)
        # Fill any missing fields and keep severity in the expected range.
        event = {**FALLBACK_EVENT, **event}
        try:
            event["severity"] = max(0.0, min(1.0, float(event["severity"])))
        except (TypeError, ValueError):
            event["severity"] = FALLBACK_EVENT["severity"]
        return event

"""
Emotionist.ai — FastAPI backend.

A thin HTTP layer over the existing emotion engine. The engine (agents/, engine/,
entity/, emotions/) is untouched: this server just drives two Agent instances and
serializes their state to JSON for the custom web frontend in web/.

Run:  uv run python server.py     (or: uv run uvicorn server:app --reload)
"""

import os
from contextlib import suppress

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.agent import Agent
from engine.appraisal import REACTIVITY
from engine.prompt_modifier import NEUTRAL_PROFILE, weighted_params, describe_level
from entity.entity import _score_to_decay

load_dotenv()

# ── Demo content (kept in sync with the original app) ─────────────────────────
ALEX_PERSONA = (
    "You are Alex, a thoughtful but anxious person who tends to overthink. "
    "You are having a conversation with Sam, a colleague."
)
SAM_PERSONA = (
    "You are Sam, an optimistic and adaptable person who bounces back easily. "
    "You are having a conversation with Alex, a colleague."
)

STARTER_TOPICS = {
    "Dog died": (
        "Alex",
        "Sam, I had a car accident today and I lived thank god — but my dog Mr. Larry didn't make it.",
    ),
    "Cancelled project": (
        "Alex",
        "Hey, I heard the big presentation got cancelled last minute — the client just pulled out entirely. Did you know about this?",
    ),
    "Unexpected praise": (
        "Sam",
        "Alex, I just got out of a meeting and the director specifically called out your work as the reason the Q1 numbers looked so good. Genuinely impressive.",
    ),
    "Unfair blame": (
        "Alex",
        "I cannot believe they pinned the whole deployment failure on our team. We followed the process exactly. This is completely unfair.",
    ),
    "New opportunity": (
        "Sam",
        "Good news — leadership approved the new project proposal and they want us to lead it. This could be a huge deal for both of us.",
    ),
}


# ── Game state (single-user local demo) ───────────────────────────────────────
class Game:
    """Holds the two agents and the turn loop. One global instance — this is a
    local single-user demo, same scope as the original Streamlit session."""

    def __init__(self):
        self.reset("Cancelled project")

    def reset(self, topic_key: str, alex_rx: float | None = None, sam_rx: float | None = None):
        if topic_key not in STARTER_TOPICS:
            topic_key = "Cancelled project"
        speaker, opening = STARTER_TOPICS[topic_key]
        self.alex = Agent("Alex", "neurotic", ALEX_PERSONA,
                          reactivity=alex_rx if alex_rx is not None else REACTIVITY["neurotic"])
        self.sam = Agent("Sam", "resilient", SAM_PERSONA,
                         reactivity=sam_rx if sam_rx is not None else REACTIVITY["resilient"])
        self.messages: list[dict] = []
        self.turn = 0
        self.next_message = opening
        self.next_speaker_is_sam = (speaker == "Alex")  # Sam responds to Alex opener
        self.opening = {"speaker": speaker, "text": opening}
        self.topic = topic_key

    def step(self, message: str | None = None) -> dict:
        """Run one turn. Mirrors the original do_turn(): the next agent responds to
        the current message, reacting to what it *witnessed* (the sender's last event)."""
        if message:
            self.next_message = message

        responder = self.sam if self.next_speaker_is_sam else self.alex
        sender = self.alex if self.next_speaker_is_sam else self.sam

        reply = responder.receive_and_respond(
            self.next_message, witness_event=sender.last_event or None
        )

        self.turn += 1
        msg = {
            "turn": self.turn,
            "speaker": responder.name,
            "text": reply,
            "event": responder.last_event,
            "alex": agent_state(self.alex),
            "sam": agent_state(self.sam),
        }
        self.messages.append(msg)
        self.next_message = reply
        self.next_speaker_is_sam = not self.next_speaker_is_sam
        return msg


GAME = Game()


# ── Serialization ─────────────────────────────────────────────────────────────
PARAM_KEYS = ["aggression", "openness", "creativity", "confidence", "cooperation"]


def agent_state(agent: Agent) -> dict:
    dominant = agent.entity.get_dominant_emotions(n=5)
    params = weighted_params(dominant) if dominant else NEUTRAL_PROFILE.copy()
    base_decay = round(_score_to_decay(agent.entity.personality_score), 3)
    return {
        "name": agent.name,
        "personality": agent.entity.personality,
        "decay": base_decay,
        "emotions": [
            {"name": n, "intensity": round(i, 4)}
            for n, i in agent.entity.get_active_emotions()[:7]
        ],
        "params": {k: {"level": describe_level(params[k]), "value": round(params[k], 1)} for k in PARAM_KEYS},
    }


def full_state() -> dict:
    return {
        "turn": GAME.turn,
        "topic": GAME.topic,
        "topics": list(STARTER_TOPICS.keys()),
        "opening": GAME.opening,
        "next_speaker": "Sam" if GAME.next_speaker_is_sam else "Alex",
        "messages": GAME.messages,
        "alex": agent_state(GAME.alex),
        "sam": agent_state(GAME.sam),
        "reactivity_ref": REACTIVITY,
        "has_key": bool(os.environ.get("GROQ_API_KEY")),
    }


# ── API ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Emotionist.ai")


class ResetReq(BaseModel):
    topic: str = "Cancelled project"
    alex_reactivity: float | None = None
    sam_reactivity: float | None = None


class TurnReq(BaseModel):
    message: str | None = None


@app.get("/api/state")
def get_state():
    return full_state()


@app.post("/api/reset")
def reset(req: ResetReq):
    GAME.reset(req.topic, req.alex_reactivity, req.sam_reactivity)
    return full_state()


@app.post("/api/turn")
def turn(req: TurnReq):
    if not os.environ.get("GROQ_API_KEY"):
        return {"error": "GROQ_API_KEY not set in .env"}
    GAME.step(req.message)
    return full_state()


# ── Static frontend ───────────────────────────────────────────────────────────
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


app.mount("/", StaticFiles(directory=WEB_DIR), name="web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

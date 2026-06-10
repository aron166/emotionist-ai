"""
Emotionist.ai — FastAPI backend.

A thin HTTP layer over the existing emotion engine. The engine (agents/, engine/,
entity/, emotions/) is untouched: this server just drives two Agent instances and
serializes their state to JSON for the custom web frontend in web/.

Run:  uv run python server.py     (or: uv run uvicorn server:app --reload)
"""

import os

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
    single-user local demo, so global state is intentional."""

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
PARAM_KEYS = list(NEUTRAL_PROFILE)


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


# ── Human ↔ agent chat (single-agent mode) ────────────────────────────────────
SEED_EMOTIONS = ["Joy", "Anger", "Fear", "Shame", "Pride", "Distress",
                 "Gratitude", "Sadness", "Anticipation", "Trust"]
PERSONALITIES = ["neurotic", "average", "resilient"]


class ChatSession:
    """One configurable agent the human talks to directly (no witness track)."""

    def __init__(self):
        self.reset("Morgan", "average", REACTIVITY["average"],
                   "You are Morgan, a thoughtful person having a conversation.")

    def reset(self, name, personality, reactivity, persona,
              seed_emotion=None, seed_intensity=0.0):
        if personality not in PERSONALITIES:
            personality = "average"
        self.agent = Agent(name or "Morgan", personality, persona or "", reactivity=reactivity)
        self.messages: list[dict] = []
        if (seed_emotion and seed_emotion != "None"
                and seed_emotion in self.agent.entity.emotions and seed_intensity > 0):
            self.agent.entity.emotions[seed_emotion].activate(seed_intensity)

    def send(self, message: str) -> str:
        reply = self.agent.receive_and_respond(message)  # human chat: no witness_event
        self.messages.append({"role": "user", "text": message})
        self.messages.append({"role": "agent", "text": reply, "event": self.agent.last_event})
        return reply


CHAT = ChatSession()


def chat_state() -> dict:
    a = CHAT.agent
    s = agent_state(a)
    s["persona"] = a.base_persona
    s["reactivity"] = round(a.entity.reactivity, 2)
    s["system_prompt"] = a.prompt_modifier.build_system_prompt(a.entity, a.base_persona)
    return {
        "agent": s,
        "messages": CHAT.messages,
        "seed_options": SEED_EMOTIONS,
        "personalities": PERSONALITIES,
        "reactivity_ref": REACTIVITY,
        "has_key": bool(os.environ.get("GROQ_API_KEY")),
    }


class ChatResetReq(BaseModel):
    name: str = "Morgan"
    personality: str = "average"
    reactivity: float = 1.0
    persona: str = "You are Morgan, a thoughtful person having a conversation."
    seed_emotion: str | None = None
    seed_intensity: float = 0.0


class ChatSendReq(BaseModel):
    message: str


@app.get("/api/chat/state")
def chat_get_state():
    return chat_state()


@app.post("/api/chat/reset")
def chat_reset(req: ChatResetReq):
    CHAT.reset(req.name, req.personality, req.reactivity, req.persona,
               req.seed_emotion, req.seed_intensity)
    return chat_state()


@app.post("/api/chat/send")
def chat_send(req: ChatSendReq):
    if not os.environ.get("GROQ_API_KEY"):
        return {"error": "GROQ_API_KEY not set in .env"}
    if req.message.strip():
        CHAT.send(req.message.strip())
    return chat_state()


# ── Static frontend ───────────────────────────────────────────────────────────
WEB_DIR = os.path.join(os.path.dirname(__file__), "web")


@app.get("/")
def index():
    return FileResponse(os.path.join(WEB_DIR, "index.html"))


@app.get("/chat")
def chat_page():
    return FileResponse(os.path.join(WEB_DIR, "chat.html"))


app.mount("/", StaticFiles(directory=WEB_DIR), name="web")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

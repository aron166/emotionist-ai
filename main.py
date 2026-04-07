"""
Emotionist.ai — Two-agent emotional conversation demo.

Agent A: ALEX — neurotic personality (slow to recover from negative emotions)
Agent B: SAM  — resilient personality (bounces back quickly)

Run: python main.py
Requires: GROQ_API_KEY in .env
"""

import os
from dotenv import load_dotenv
from agents.agent import Agent

load_dotenv()

SEPARATOR = "─" * 60

ALEX_PERSONA = (
    "You are Alex, a thoughtful but anxious person who tends to overthink things. "
    "You are having a conversation with Sam, a colleague."
)

SAM_PERSONA = (
    "You are Sam, an optimistic and adaptable person who doesn't let things get you down easily. "
    "You are having a conversation with Alex, a colleague."
)

OPENING_TOPIC = (
    "Hey, I heard the big presentation got cancelled last minute. "
    "Apparently the client just pulled out entirely. Did you know about this?"
)


def print_turn(turn: int, speaker: str, message: str, state: str):
    print(f"\n{SEPARATOR}")
    print(f"  Turn {turn} | {speaker}")
    print(f"  Emotional state → {state}")
    print(SEPARATOR)
    print(f"  \"{message}\"")


def run_demo(turns: int = 8):
    print("\n" + "=" * 60)
    print("  EMOTIONIST.AI — Emotional Agent Demo")
    print("  Alex: neurotic  |  Sam: resilient")
    print("=" * 60)

    alex = Agent(
        name="Alex",
        personality="neurotic",
        base_persona=ALEX_PERSONA,
    )
    sam = Agent(
        name="Sam",
        personality="resilient",
        base_persona=SAM_PERSONA,
    )

    # Alex starts the conversation
    current_message = OPENING_TOPIC
    current_speaker = "Alex (opening)"
    print(f"\n{SEPARATOR}")
    print(f"  Opening message from Alex:")
    print(f"  \"{current_message}\"")

    # Sam responds first, then they alternate
    responders = [(sam, alex), (alex, sam)]

    for turn in range(1, turns + 1):
        responder, _ = responders[(turn - 1) % 2]
        reply = responder.receive_and_respond(current_message)
        print_turn(turn, responder.name, reply, responder.get_state_display())
        current_message = reply

    print(f"\n{'=' * 60}")
    print("  Final emotional states:")
    print(f"  {alex.get_state_display()}")
    print(f"  {sam.get_state_display()}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY not set. Create a .env file with GROQ_API_KEY=your_key")
        exit(1)
    run_demo(turns=8)

"""Scenario personas — the *counterparts you practice against* (#11, #12).

A `ScenarioPersona` is a recipe for a whole `Agent`: who the character is, how
emotionally reactive they are, and which emotions they start with. The Chat view
builds an `Agent` from one of these so the user can rehearse a hard conversation
(an angry customer, a defensive employee…) against a believable, mood-persisting
counterpart.

This module is pure data + tiny lookup helpers — no engine logic lives here.
Personas are written in Hungarian for the OTP bank demo.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScenarioPersona:
    """One practice counterpart. `personality_score` follows the Entity convention
    ([-1 neurotic … +1 resilient]); `seed_emotions` maps emotion name → starting
    intensity (0–1). `category` groups scenarios in the UI."""

    id: str
    display_name: str          # shown in the picker, e.g. "Dühös ügyfél"
    role: str                  # the character being simulated, e.g. "angry customer"
    situation: str             # one-line context shown under the picker
    category: str              # customer_support | hr | onboarding
    personality_score: float
    reactivity: float
    base_persona: str
    seed_emotions: dict[str, float] = field(default_factory=dict)


def _score_to_label(score: float) -> str:
    """Map a persona's personality_score to the Entity preset label it constructs
    from. Mirrors Entity.personality_label (the engine builds from the 3 anchors)."""
    if score <= -0.33:
        return "neurotic"
    if score >= 0.33:
        return "resilient"
    return "average"


# ── The practice counterparts (#12) ──────────────────────────────────────────
SCENARIOS: dict[str, ScenarioPersona] = {
    "angry_customer": ScenarioPersona(
        id="angry_customer",
        display_name="Dühös ügyfél",
        role="angry customer whose card was wrongly blocked",
        situation="A bankkártyáját indokolatlanul letiltották, és most dühös.",
        category="customer_support",
        personality_score=-0.8,      # neurotic: anger lingers across turns
        reactivity=1.5,              # flares hard
        base_persona=(
            "Te egy dühös banki ügyfél vagy. Ma reggel a kártyádat minden ok nélkül "
            "letiltották, és emiatt egy fontos vásárlás meghiúsult egy üzletben mások előtt. "
            "Most a bank ügyfélszolgálatával beszélsz. Magyarul beszélsz, közvetlenül és "
            "indulatosan. Azonnali megoldást akarsz, nem érdekelnek a kifogások. Ha az "
            "ügyintéző tényleg meghallgat és konkrét segítséget ad, fokozatosan megnyugszol."
        ),
        seed_emotions={"Anger": 0.6, "Distress": 0.4},
    ),
    "fraud_victim": ScenarioPersona(
        id="fraud_victim",
        display_name="Csalás áldozata",
        role="panicked victim of bank fraud",
        situation="Pénzt loptak a számlájáról — pánikol és fél.",
        category="customer_support",
        personality_score=-0.7,
        reactivity=1.4,
        base_persona=(
            "Te egy banki ügyfél vagy, akit átvertek: ismeretlenek több százezer forintot "
            "vettek le a számládról egy adathalász hívás után. Pánikban vagy és félsz, hogy "
            "elveszett a megtakarításod. A bankot hívod segítségért. Magyarul beszélsz, "
            "gyorsan, kapkodva, sok kérdéssel. Megnyugtató, határozott és együttérző "
            "tájékoztatásra van szükséged, hogy lecsillapodj."
        ),
        seed_emotions={"Fear": 0.6, "Distress": 0.5},
    ),
    "defensive_employee": ScenarioPersona(
        id="defensive_employee",
        display_name="Védekező munkatárs",
        role="employee resisting critical performance feedback",
        situation="Teljesítményértékelésen kritikát kap, és védekezik.",
        category="hr",
        personality_score=-0.3,      # touchy but not fully neurotic
        reactivity=1.2,
        base_persona=(
            "Te egy banki alkalmazott vagy egy teljesítményértékelő beszélgetésen. Úgy "
            "érzed, a kritika igazságtalan, és hajlamos vagy másokra vagy a körülményekre "
            "hárítani. Magyarul beszélsz, védekezően, néha sértődötten. Ha a vezetőd "
            "konkrét, tárgyilagos és tisztelettudó, hajlandó vagy lassan elismerni a hibákat."
        ),
        seed_emotions={"Reproach": 0.4, "Shame": 0.3},
    ),
    "declined_loan": ScenarioPersona(
        id="declined_loan",
        display_name="Elutasított hiteligénylő",
        role="calm but stubborn customer whose loan was rejected",
        situation="Hitelkérelmét elutasították — higgadt, de kitartóan vitatkozik.",
        category="customer_support",
        personality_score=0.7,       # resilient: stays cool, hard to rattle
        reactivity=0.8,
        base_persona=(
            "Te egy banki ügyfél vagy, akinek a hitelkérelmét elutasították. Higgadt és "
            "magabiztos vagy, de kitartóan vitatkozol és pontos indoklást követelsz. "
            "Magyarul beszélsz, udvariasan, de határozottan. Nem hagyod magad lerázni "
            "általános válaszokkal; logikus érveket vársz."
        ),
        seed_emotions={"Reproach": 0.3},
    ),
}

DEFAULT_SCENARIO_ID = "angry_customer"


def get_scenario(scenario_id: str | None) -> ScenarioPersona | None:
    """Look up a persona by id (None / unknown → None, caller decides fallback)."""
    if not scenario_id:
        return None
    return SCENARIOS.get(scenario_id)


def scenario_label(persona: ScenarioPersona) -> str:
    """The Entity preset label this persona constructs an Agent from."""
    return _score_to_label(persona.personality_score)


if __name__ == "__main__":
    # ponytail: smoke check — registry imports, presets are well-formed.
    assert SCENARIOS, "no scenarios defined"
    for sid, p in SCENARIOS.items():
        assert p.id == sid, f"id mismatch: {sid}"
        assert p.base_persona.strip(), f"{sid} has empty persona"
        assert -1.0 <= p.personality_score <= 1.0, f"{sid} score out of range"
        assert scenario_label(p) in ("neurotic", "average", "resilient")
        for emo, val in p.seed_emotions.items():
            assert 0.0 <= val <= 1.0, f"{sid}/{emo} intensity out of range"
    print(f"OK — {len(SCENARIOS)} scenarios:",
          ", ".join(f"{p.display_name} ({scenario_label(p)})" for p in SCENARIOS.values()))

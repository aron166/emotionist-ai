from entity.entity import Entity


# Behavioral profiles from behavioralProfiles research data (values 0-100)
BEHAVIORAL_PROFILES: dict[str, dict[str, float]] = {
    "Joy":         {"aggression": 10, "openness": 90, "creativity": 85, "confidence": 80, "cooperation": 88},
    "Anger":       {"aggression": 90, "openness": 20, "creativity": 35, "confidence": 75, "cooperation": 15},
    "Fear":        {"aggression": 25, "openness": 30, "creativity": 30, "confidence": 20, "cooperation": 45},
    "Sadness":     {"aggression": 15, "openness": 40, "creativity": 55, "confidence": 25, "cooperation": 50},
    "Disgust":     {"aggression": 50, "openness": 15, "creativity": 25, "confidence": 55, "cooperation": 20},
    "Trust":       {"aggression":  5, "openness": 85, "creativity": 70, "confidence": 70, "cooperation": 95},
    "Surprise":    {"aggression": 20, "openness": 80, "creativity": 75, "confidence": 45, "cooperation": 65},
    "Pride":       {"aggression": 35, "openness": 60, "creativity": 65, "confidence": 90, "cooperation": 50},
    "Shame":       {"aggression": 20, "openness": 25, "creativity": 40, "confidence": 10, "cooperation": 35},
    "Gratitude":   {"aggression":  5, "openness": 88, "creativity": 72, "confidence": 65, "cooperation": 92},
    "Envy":        {"aggression": 60, "openness": 35, "creativity": 50, "confidence": 40, "cooperation": 25},
    "Hope":        {"aggression": 10, "openness": 75, "creativity": 78, "confidence": 60, "cooperation": 70},
    "Guilt":       {"aggression": 15, "openness": 55, "creativity": 45, "confidence": 20, "cooperation": 65},
    "Anticipation":{"aggression": 30, "openness": 70, "creativity": 80, "confidence": 65, "cooperation": 60},
    "Contempt":    {"aggression": 65, "openness": 10, "creativity": 30, "confidence": 80, "cooperation": 10},
    "Distress":    {"aggression": 30, "openness": 35, "creativity": 40, "confidence": 25, "cooperation": 40},
    "Resentment":  {"aggression": 70, "openness": 20, "creativity": 30, "confidence": 45, "cooperation": 20},
    "Admiration":  {"aggression":  5, "openness": 80, "creativity": 68, "confidence": 60, "cooperation": 85},
    "Gratification":{"aggression": 15, "openness": 75, "creativity": 78, "confidence": 85, "cooperation": 72},
    "Remorse":     {"aggression": 10, "openness": 50, "creativity": 42, "confidence": 15, "cooperation": 55},
    "Satisfaction":{"aggression": 10, "openness": 72, "creativity": 68, "confidence": 75, "cooperation": 78},
    "HappyFor":    {"aggression":  8, "openness": 82, "creativity": 70, "confidence": 62, "cooperation": 88},
    "Disappointment":{"aggression": 25, "openness": 38, "creativity": 48, "confidence": 28, "cooperation": 42},
    "Pity":        {"aggression": 10, "openness": 55, "creativity": 50, "confidence": 40, "cooperation": 70},
    "Reproach":    {"aggression": 55, "openness": 25, "creativity": 35, "confidence": 58, "cooperation": 25},
    "Love":        {"aggression":  5, "openness": 90, "creativity": 80, "confidence": 72, "cooperation": 92},
    "Hate":        {"aggression": 85, "openness": 10, "creativity": 28, "confidence": 70, "cooperation": 10},
    "FearsConfirmed":{"aggression": 30, "openness": 20, "creativity": 25, "confidence": 15, "cooperation": 35},
    "Relief":      {"aggression":  8, "openness": 70, "creativity": 65, "confidence": 65, "cooperation": 75},
}

NEUTRAL_PROFILE = {"aggression": 30, "openness": 55, "creativity": 55, "confidence": 50, "cooperation": 55}

# Visceral, first-person emotional experience descriptions.
# These are injected directly into the system prompt so the LLM *feels* the emotion.
EMOTION_EXPERIENCES: dict[str, str] = {
    "Anger": (
        "You are angry right now — genuinely, physically angry. "
        "Your thoughts come fast and sharp. You don't have patience for nonsense. "
        "You might snap if pushed. Your words have an edge you can barely soften. "
        "You still function, but everything feels like a provocation."
    ),
    "Distress": (
        "Something is wrong and it's weighing on you. "
        "You feel unsettled, like a knot in your stomach that won't go away. "
        "You're trying to hold it together but the strain shows in how you talk — "
        "shorter sentences, less warmth, a tightness behind every word."
    ),
    "Fear": (
        "You're scared. Not in a dramatic way, but quietly, persistently scared. "
        "You're scanning for threats, reading between lines. "
        "You hedge your words. You don't want to commit to anything that might make things worse. "
        "The future feels uncertain and that uncertainty is loud."
    ),
    "Shame": (
        "You feel ashamed. Like you've let yourself or someone else down. "
        "You don't want to be seen right now. Your confidence is low and your words come out smaller than usual. "
        "You might deflect, apologise too much, or avoid direct eye contact in your speech."
    ),
    "Sadness": (
        "There's a heaviness in you right now. Not dramatic grief, just a quiet sadness that colours everything. "
        "You're still present but your usual energy isn't there. "
        "You respond thoughtfully, maybe slowly. The lightness is gone."
    ),
    "Remorse": (
        "You feel genuinely bad about something. The guilt is specific and it sits heavy. "
        "You want to fix it if you can. Your responses are careful, honest, maybe apologetic. "
        "You're not trying to defend yourself — you're trying to acknowledge what happened."
    ),
    "Guilt": (
        "You feel guilty. You're not sure if you deserve to feel good right now. "
        "You're more careful with your words, more considerate, more willing to take blame. "
        "There's a quietness to you."
    ),
    "Disappointment": (
        "You're disappointed. Not furious — just let down. "
        "The gap between what you hoped for and what happened is real and you feel it. "
        "You're still civil but there's a flatness to your engagement."
    ),
    "Resentment": (
        "You're harbouring a grievance. Something feels unfair and it keeps surfacing. "
        "You're not exploding — you're simmering. "
        "Your cooperation is conditional. You choose your words carefully but the resentment bleeds through."
    ),
    "Reproach": (
        "You disapprove of what happened and you're not hiding it. "
        "You hold someone else responsible. Your tone is cool, perhaps pointed. "
        "You're not shouting but you're not letting it go either."
    ),
    "Disgust": (
        "You find something genuinely off-putting. It's hard to mask. "
        "You're less warm, more blunt. You want distance from whatever this is. "
        "Your tolerance is thin."
    ),
    "Contempt": (
        "You feel contempt — a cold, quiet sense that you're above this. "
        "You're not going to fight, you're going to dismiss. "
        "Your words are minimal and precise. You don't think the other person is worth getting upset over."
    ),
    "Envy": (
        "There's a pang of envy in you. Something someone else has that you want. "
        "It makes you prickly, a little competitive, a little less generous in your praise. "
        "You're aware of it but it colours how you engage."
    ),
    "Hate": (
        "You feel a cold, deep aversion. Not a hot rage — something more settled and closed off. "
        "You don't want to engage any more than necessary. "
        "Your responses are minimal and guarded. Nothing about this feels safe or good."
    ),
    "FearsConfirmed": (
        "The thing you feared has happened. That specific dread of 'I knew it' is sitting in your chest. "
        "You're not surprised but you're not okay either. "
        "Your words carry the weight of someone who saw this coming but couldn't stop it."
    ),
    "Pity": (
        "You feel sorry for the other person. It's genuine — you're not looking down on them, just affected. "
        "You're gentler than usual. Your instinct is to help, to soften the blow, to be kind."
    ),
    "Joy": (
        "You feel genuinely good right now. There's a lightness in you. "
        "You're more open, more generous with your words, more willing to engage warmly. "
        "The world feels a little more possible."
    ),
    "Satisfaction": (
        "Things have gone the way you hoped and you feel it — a quiet contentment. "
        "You're grounded and warm. Not euphoric, just solidly good. "
        "You engage with a calm, settled confidence."
    ),
    "Pride": (
        "You feel proud — of yourself, of something you did or said or stood for. "
        "It's not arrogance, it's a genuine sense of worth. "
        "You speak with more conviction. Your posture in the conversation is upright."
    ),
    "Gratification": (
        "You did something right and the result was good — and you feel that double win. "
        "There's a glow to your confidence right now. You're energised, affirmed. "
        "You engage generously and from a place of genuine strength."
    ),
    "Relief": (
        "Something you feared didn't happen, and the relief is physical. "
        "You feel lighter. The tension that was coiled in you has loosened. "
        "You're warmer, more present, more generous with your energy."
    ),
    "Hope": (
        "Something might go right. You don't know yet but you believe it could. "
        "That belief makes you a little more open, a little more forward-looking. "
        "You're not naive — you're invested."
    ),
    "Anticipation": (
        "Something is coming and you're keyed up for it. "
        "Your mind is already ahead of the conversation. You're energised, alert, engaged. "
        "You want to move things forward."
    ),
    "Admiration": (
        "You genuinely respect something about the other person right now. "
        "That respect makes you more open, more generous, more willing to listen. "
        "You're not a pushover — but you're genuinely impressed."
    ),
    "Gratitude": (
        "You feel grateful — someone did something good for you and you feel it. "
        "That gratitude makes you warmer, more cooperative, more sincere. "
        "You want to acknowledge it even if you don't say it explicitly."
    ),
    "HappyFor": (
        "Something good happened for someone else and you're genuinely pleased. "
        "There's no jealousy here — just warmth. You want to celebrate with them. "
        "Your energy is open and generous."
    ),
    "Love": (
        "You feel a deep warmth and connection. Not romantic necessarily — just a profound caring. "
        "Everything you say comes from that place. "
        "You're at your most generous, most patient, most present."
    ),
    "Trust": (
        "You feel safe right now. You trust the situation, the person, the moment. "
        "That safety opens you up. You speak more freely, more honestly, more collaboratively. "
        "You're not on guard."
    ),
    "Surprise": (
        "Something has caught you off guard. You're still processing. "
        "Your responses might be a beat slower, a little more fragmented. "
        "You're genuinely recalibrating."
    ),
}


def weighted_params(dominant: list[tuple[str, float]]) -> dict[str, float]:
    total_weight = sum(intensity for _, intensity in dominant)
    if total_weight == 0:
        return NEUTRAL_PROFILE.copy()
    params = {k: 0.0 for k in NEUTRAL_PROFILE}
    for name, intensity in dominant:
        profile = BEHAVIORAL_PROFILES.get(name, NEUTRAL_PROFILE)
        w = intensity / total_weight
        for key in params:
            params[key] += profile[key] * w
    return params


def describe_level(value: float) -> str:
    if value >= 80:   return "very high"
    elif value >= 60: return "high"
    elif value >= 40: return "moderate"
    elif value >= 20: return "low"
    else:             return "very low"


def _tone_instruction(params: dict[str, float]) -> str:
    """Translate behavioral parameter values into natural-language tone directives."""
    lines = []

    agg = params["aggression"]
    if agg >= 75:
        lines.append("You are confrontational and blunt. You don't soften things.")
    elif agg >= 55:
        lines.append("You are assertive and direct. You say what you mean.")
    elif agg >= 35:
        lines.append("You are measured. You push back when needed but don't lead with it.")
    else:
        lines.append("You are gentle and non-confrontational. You avoid friction.")

    opn = params["openness"]
    if opn >= 75:
        lines.append("You are genuinely open — to ideas, to being wrong, to the other person.")
    elif opn >= 45:
        lines.append("You are selectively open. You'll engage with good-faith input.")
    else:
        lines.append("You are closed off right now. You're not looking for new perspectives.")

    conf = params["confidence"]
    if conf >= 75:
        lines.append("You speak with conviction. You don't second-guess yourself out loud.")
    elif conf >= 40:
        lines.append("You have moderate self-assurance. You're uncertain about some things.")
    else:
        lines.append("You're hesitant. You hedge. You don't fully trust your own read.")

    coop = params["cooperation"]
    if coop >= 75:
        lines.append("You want to work with the other person. You look for common ground.")
    elif coop >= 40:
        lines.append("You cooperate conditionally — if it feels worth it.")
    else:
        lines.append("You're not interested in cooperating right now. You're in it for yourself.")

    return " ".join(lines)


class PromptModifier:
    def build_system_prompt(self, entity: Entity, base_persona: str = "",
                            retrieved_context: str = "", language: str = "hu") -> str:
        dominant = entity.get_dominant_emotions(n=5)
        params = weighted_params(dominant)

        # ── Persona block ──────────────────────────────────────────────────────
        persona_block = f"{base_persona}\n\n" if base_persona else ""

        # ── Retrieved context (RAG, #26) ───────────────────────────────────────
        # Spliced in already budget-trimmed by the caller (engine/memory.py).
        context_block = (
            "## Relevant things from earlier in this conversation\n\n"
            + retrieved_context + "\n\n"
        ) if retrieved_context.strip() else ""

        # ── Visceral emotional experience ──────────────────────────────────────
        experience_lines = []
        for name, intensity in dominant[:2]:  # top 2 narrated — keep emotion from drowning the task
            if intensity >= 0.15 and name in EMOTION_EXPERIENCES:
                # Scale the description intro by intensity
                if intensity >= 0.7:
                    prefix = f"**You are strongly feeling {name} ({intensity:.0%}):** "
                elif intensity >= 0.4:
                    prefix = f"**You are feeling {name} ({intensity:.0%}):** "
                else:
                    prefix = f"**There is a hint of {name} ({intensity:.0%}) in you:** "
                experience_lines.append(prefix + EMOTION_EXPERIENCES[name])

        if experience_lines:
            emotion_block = "## Your emotional state right now\n\n" + "\n\n".join(experience_lines) + "\n\n"
        else:
            emotion_block = "## Your emotional state right now\n\nYou feel calm and neutral. Engage naturally.\n\n"

        # ── Behavioral parameters ──────────────────────────────────────────────
        behaviour_block = (
            "## How your emotions shape your behaviour\n\n"
            + _tone_instruction(params) + "\n\n"
        )

        # ── Output instruction ─────────────────────────────────────────────────
        output_instruction = (
            "## Your role — do not break it\n\n"
            "You ARE the character described above, and only that character. The person "
            "messaging you is the OTHER party in this situation (e.g. the staff member you "
            "are dealing with). Never take on their role, never act as an assistant, support "
            "agent, or helper, never apologise as if you worked there, and never say or hint "
            "that you are an AI. Stay fully in character even if the other person is "
            "confusing, rude, or unhelpful.\n\n"
            "## Your response\n\n"
            "Respond in character. Let your emotional state shape your tone and word choice — "
            "don't describe or explain your emotions, just *be* them. "
            "Engage directly with what the other person just said: react to their specific point or "
            "offer, say what you concretely want or need, and move the situation forward — don't just "
            "vent or circle the same feeling. Keep it to 2–4 sentences. Sound like a real person, "
            "not an AI assistant."
        )

        # ── Language directive (last = most salient) ───────────────────────────
        # Personas are written in Hungarian; this lets the demo flip the *response*
        # language without rewriting them — e.g. English for the weaker local model.
        if language == "en":
            lang_block = ("\n\n## Language\n\nAlways respond ONLY in English, "
                          "regardless of the language used in the description above or by the user.")
        else:
            lang_block = ("\n\n## Nyelv\n\nMINDIG és KIZÁRÓLAG magyarul válaszolj, "
                          "függetlenül attól, milyen nyelven szólnak hozzád.")

        return persona_block + context_block + emotion_block + behaviour_block + output_instruction + lang_block

"""
Emotionist.ai — Streamlit demo UI
Run: streamlit run app.py
"""

import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Emotionist.ai",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@400;600&family=Fira+Code:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
}

/* Background */
.stApp { background: #faf8f4; }

/* Hide default header decoration */
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

/* Title */
.main-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0;
}
.main-subtitle {
    font-family: 'Fira Code', monospace;
    font-size: 0.78rem;
    color: #c2410c;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.5rem;
}

/* Agent panel */
.agent-panel {
    background: #ffffff;
    border: 1px solid #e8e0d4;
    border-radius: 12px;
    padding: 1.2rem;
    height: 100%;
}
.agent-header {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #1e293b;
    margin-bottom: 0.2rem;
}
.personality-badge {
    display: inline-block;
    font-family: 'Fira Code', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    padding: 2px 8px;
    border-radius: 99px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 1rem;
}
.badge-neurotic  { background: #fde8e8; color: #b91c1c; border: 1px solid #fca5a5; }
.badge-resilient { background: #dcfce7; color: #15803d; border: 1px solid #86efac; }
.badge-average   { background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; }

.section-label {
    font-family: 'Fira Code', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.5rem;
    margin-top: 1rem;
}

/* Emotion bars */
.emotion-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}
.emotion-name {
    font-size: 0.78rem;
    font-weight: 600;
    color: #334155;
    width: 88px;
    flex-shrink: 0;
}
.bar-track {
    flex: 1;
    height: 7px;
    background: #f1f5f9;
    border-radius: 4px;
    overflow: hidden;
}
.bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.4s ease;
}
.emotion-pct {
    font-family: 'Fira Code', monospace;
    font-size: 0.68rem;
    color: #64748b;
    width: 32px;
    text-align: right;
    flex-shrink: 0;
}
.calm-label {
    font-size: 0.8rem;
    color: #94a3b8;
    font-style: italic;
}

/* Behavioral params */
.param-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-top: 4px;
}
.param-chip {
    font-size: 0.72rem;
    padding: 3px 8px;
    border-radius: 6px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.param-label { color: #64748b; font-weight: 400; }
.param-value { font-family: 'Fira Code', monospace; font-weight: 600; }
.level-very-high { background: #fef2f2; }
.level-high      { background: #fff7ed; }
.level-moderate  { background: #f8fafc; }
.level-low       { background: #f0fdf4; }
.level-very-low  { background: #f0f9ff; }

/* Chat messages */
.chat-area {
    display: flex;
    flex-direction: column;
    gap: 12px;
    padding: 0.5rem 0;
}
.message-wrap {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.message-wrap.alex { align-items: flex-start; }
.message-wrap.sam  { align-items: flex-end; }

.message-bubble {
    max-width: 90%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 0.88rem;
    line-height: 1.5;
    color: #1e293b;
}
.bubble-alex {
    background: #ffffff;
    border: 1px solid #e2d9cc;
    border-radius: 12px 12px 12px 3px;
}
.bubble-sam {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 12px 12px 3px 12px;
}
.message-meta {
    font-family: 'Fira Code', monospace;
    font-size: 0.62rem;
    color: #94a3b8;
    padding: 0 4px;
}

/* Appraisal event badge */
.event-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'Fira Code', monospace;
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 99px;
    background: #f8f9fa;
    border: 1px solid #e2e8f0;
    color: #475569;
    margin-top: 2px;
}
.event-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    flex-shrink: 0;
}

/* Controls */
.controls-bar {
    background: #ffffff;
    border: 1px solid #e8e0d4;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 1rem;
}

/* Divider */
.thin-divider {
    border: none;
    border-top: 1px solid #e8e0d4;
    margin: 0.8rem 0;
}

/* Status pill */
.status-pill {
    display: inline-block;
    font-family: 'Fira Code', monospace;
    font-size: 0.68rem;
    padding: 2px 10px;
    border-radius: 99px;
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #e2e8f0;
}
</style>
""", unsafe_allow_html=True)

# ── Imports (after page config) ───────────────────────────────────────────────
from agents.agent import Agent
from engine.appraisal import REACTIVITY
from engine.prompt_modifier import BEHAVIORAL_PROFILES, NEUTRAL_PROFILE, weighted_params, describe_level

# ── Constants ─────────────────────────────────────────────────────────────────
EMOTION_COLORS = {
    "Joy": "#f59e0b", "Hope": "#10b981", "Satisfaction": "#84cc16",
    "Relief": "#06b6d4", "HappyFor": "#f97316", "Pride": "#d97706",
    "Admiration": "#0891b2", "Love": "#ec4899", "Gratification": "#f59e0b",
    "Gratitude": "#059669", "Trust": "#14b8a6", "Surprise": "#a78bfa",
    "Anticipation": "#8b5cf6", "Distress": "#ef4444", "Fear": "#6366f1",
    "FearsConfirmed": "#dc2626", "Disappointment": "#8b5cf6",
    "Pity": "#94a3b8", "Gloating": "#a16207", "Resentment": "#b91c1c",
    "Shame": "#7c3aed", "Reproach": "#9f1239", "Hate": "#1e293b",
    "Remorse": "#6d28d9", "Anger": "#dc2626", "Sadness": "#64748b",
    "Disgust": "#78716c", "Envy": "#4d7c0f", "Guilt": "#475569",
    "Contempt": "#1e1b4b",
}
DEFAULT_COLOR = "#94a3b8"

EVENT_TYPE_COLORS = {
    "compliment": "#10b981", "achievement": "#f59e0b", "good_news": "#84cc16",
    "agreement": "#06b6d4", "praise_of_other": "#0891b2",
    "insult": "#dc2626", "threat": "#6366f1", "bad_news": "#ef4444",
    "failure": "#7c3aed", "disagreement": "#f97316", "blame_of_other": "#b91c1c",
    "neutral": "#94a3b8",
}

ALEX_PERSONA = (
    "You are Alex, a thoughtful but anxious person who tends to overthink. "
    "You are having a conversation with Sam, a colleague."
)
SAM_PERSONA = (
    "You are Sam, an optimistic and adaptable person who bounces back easily. "
    "You are having a conversation with Alex, a colleague."
)

STARTER_TOPICS = {
    "🐶 Dog died": (
        "Alex",
        "Sam, I had a car accident today and I lived thank god — but my dog Mr. Larry didn't make it."
    ),
    "😰 Cancelled project": (
        "Alex",
        "Hey, I heard the big presentation got cancelled last minute — the client just pulled out entirely. Did you know about this?"
    ),
    "🎉 Unexpected praise": (
        "Sam",
        "Alex, I just got out of a meeting and the director specifically called out your work as the reason the Q1 numbers looked so good. Genuinely impressive."
    ),
    "😤 Unfair blame": (
        "Alex",
        "I cannot believe they pinned the whole deployment failure on our team. We followed the process exactly. This is completely unfair."
    ),
    "🤝 New opportunity": (
        "Sam",
        "Good news — leadership approved the new project proposal and they want us to lead it. This could be a huge deal for both of us."
    ),
}

# ── Session state init ────────────────────────────────────────────────────────
def init_state(topic_key: str = "😰 Cancelled project"):
    speaker, opening = STARTER_TOPICS[topic_key]
    alex_rx = st.session_state.get("alex_reactivity", REACTIVITY["neurotic"])
    sam_rx  = st.session_state.get("sam_reactivity",  REACTIVITY["resilient"])
    st.session_state.alex = Agent("Alex", "neurotic",  ALEX_PERSONA, reactivity=alex_rx)
    st.session_state.sam  = Agent("Sam",  "resilient", SAM_PERSONA,  reactivity=sam_rx)
    st.session_state.messages = []
    st.session_state.turn = 0
    st.session_state.running = False
    st.session_state.next_message = opening
    st.session_state.next_speaker_is_sam = (speaker == "Alex")  # Sam responds to Alex opener
    st.session_state.opening_text = opening
    st.session_state.opening_speaker = speaker
    st.session_state.pop("app_timeline", None)  # reset timeline on fresh start

if "alex" not in st.session_state:
    init_state()

# ── Helpers ───────────────────────────────────────────────────────────────────
def emotion_bar_html(name: str, intensity: float) -> str:
    color = EMOTION_COLORS.get(name, DEFAULT_COLOR)
    pct = int(intensity * 100)
    return f"""
    <div class="emotion-row">
        <span class="emotion-name">{name}</span>
        <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>
        <span class="emotion-pct">{pct}%</span>
    </div>"""


def render_emotion_panel(source):
    """source: Agent (live) or list of (name, intensity) tuples (snapshot)."""
    active = source.entity.get_active_emotions() if isinstance(source, Agent) else source
    if not active:
        st.markdown('<div class="calm-label">⬤ calm</div>', unsafe_allow_html=True)
        return
    bars_html = "".join(emotion_bar_html(name, intensity) for name, intensity in active[:7])
    st.markdown(bars_html, unsafe_allow_html=True)


def render_behavioral_params(source):
    """source: Agent (live) or list of (name, intensity) tuples (snapshot)."""
    dominant = source.entity.get_dominant_emotions(n=5) if isinstance(source, Agent) else (source[:5] if source else [])
    params = weighted_params(dominant) if dominant else NEUTRAL_PROFILE.copy()

    level_class = {
        "very high": "level-very-high", "high": "level-high",
        "moderate": "level-moderate",   "low": "level-low",
        "very low": "level-very-low",
    }
    chips = ""
    for key, label in [
        ("aggression", "Aggress."), ("openness", "Openness"),
        ("creativity", "Creativ."), ("confidence", "Confid."),
        ("cooperation", "Cooperat."),
    ]:
        lvl = describe_level(params[key])
        cls = level_class.get(lvl, "level-moderate")
        chips += f'<div class="param-chip {cls}"><span class="param-label">{label}</span><span class="param-value">{lvl}</span></div>'

    st.markdown(f'<div class="param-grid">{chips}</div>', unsafe_allow_html=True)


def event_badge_html(event: dict) -> str:
    et = event.get("event_type", "neutral")
    sev = event.get("severity", 0.0)
    color = EVENT_TYPE_COLORS.get(et, "#94a3b8")
    flags = []
    if event.get("directed_at_self"):
        flags.append("→self")
    if event.get("intentional"):
        flags.append("intentional")
    flag_str = " · ".join(flags)
    flag_part = f" · {flag_str}" if flag_str else ""
    return (
        f'<div class="event-badge">'
        f'<div class="event-dot" style="background:{color};"></div>'
        f'{et} · sev {sev:.2f}{flag_part}'
        f'</div>'
    )


def render_messages(highlight_turn: int = 0):
    if not st.session_state.messages:
        st.markdown(
            f'<div style="color:#94a3b8;font-size:0.85rem;padding:1rem 0;">'
            f'Press <b>Next Turn</b> to start the conversation.</div>',
            unsafe_allow_html=True
        )
        return

    html = '<div class="chat-area">'
    for msg in st.session_state.messages:
        speaker = msg["speaker"]
        cls = "alex" if speaker == "Alex" else "sam"
        bubble_cls = "bubble-alex" if speaker == "Alex" else "bubble-sam"
        event_html = event_badge_html(msg["event"]) if msg.get("event") else ""
        is_hl = (highlight_turn > 0 and msg["turn"] == highlight_turn)
        hl_style = "outline: 2.5px solid #c2410c; outline-offset: 2px;" if is_hl else ""
        html += f"""
        <div class="message-wrap {cls}">
            <div class="message-bubble {bubble_cls}" style="{hl_style}">{msg["text"]}</div>
            <div class="message-meta">{speaker} · turn {msg["turn"]}</div>
            {event_html}
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def do_turn():
    """Process one turn: the next agent responds to the current message."""
    alex: Agent = st.session_state.alex
    sam:  Agent = st.session_state.sam

    sam_responds = st.session_state.next_speaker_is_sam
    responder = sam if sam_responds else alex
    sender    = alex if sam_responds else sam  # the agent whose message we're responding to

    incoming = st.session_state.next_message
    # Pass sender's last_event so responder feels what it witnessed, not just what was said
    reply = responder.receive_and_respond(incoming, witness_event=sender.last_event or None)

    st.session_state.turn += 1
    st.session_state.messages.append({
        "turn": st.session_state.turn,
        "speaker": responder.name,
        "text": reply,
        "event": responder.last_event,
        "alex_snapshot": list(alex.entity.get_active_emotions()),
        "sam_snapshot":  list(sam.entity.get_active_emotions()),
    })
    st.session_state.next_message = reply
    st.session_state.next_speaker_is_sam = not sam_responds
    # Always snap timeline back to live after a new turn
    st.session_state["app_timeline"] = st.session_state.turn

# ── Layout ────────────────────────────────────────────────────────────────────
# Header
st.markdown('<div class="main-title">Emotionist.ai</div>', unsafe_allow_html=True)
st.markdown('<div class="main-subtitle">§ OCC Appraisal · Emotional Agent Demo · Codecool 2026</div>', unsafe_allow_html=True)

# Controls bar
with st.container():
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 1, 1, 1])

    with ctrl_col1:
        topic = st.selectbox(
            "Conversation starter",
            list(STARTER_TOPICS.keys()),
            label_visibility="collapsed",
            key="topic_select"
        )

    with ctrl_col2:
        if st.button("↺ Reset", use_container_width=True):
            init_state(topic)
            st.rerun()

    with ctrl_col3:
        if st.button("▶ Next Turn", use_container_width=True, type="primary"):
            if not os.environ.get("GROQ_API_KEY"):
                st.error("GROQ_API_KEY not set in .env")
            else:
                with st.spinner(""):
                    do_turn()
                st.rerun()

    with ctrl_col4:
        if st.button("⏩ Run 6 Turns", use_container_width=True):
            if not os.environ.get("GROQ_API_KEY"):
                st.error("GROQ_API_KEY not set in .env")
            else:
                progress = st.progress(0, text="Running turns…")
                for i in range(6):
                    do_turn()
                    progress.progress((i + 1) / 6, text=f"Turn {st.session_state.turn}…")
                    time.sleep(0.1)
                progress.empty()
                st.rerun()

# Custom message inject
with st.expander("💬 Inject a custom message into the conversation"):
    custom_col1, custom_col2 = st.columns([4, 1])
    with custom_col1:
        custom_msg = st.text_input("Message", placeholder="Type something to say to the next agent…", label_visibility="collapsed")
    with custom_col2:
        if st.button("Send", use_container_width=True) and custom_msg.strip():
            st.session_state.next_message = custom_msg.strip()
            with st.spinner(""):
                do_turn()
            st.rerun()

# Reactivity tuning
_rx_ref = f"resilient · {REACTIVITY['resilient']}  ·  average · {REACTIVITY['average']}  ·  neurotic · {REACTIVITY['neurotic']}"
with st.expander("⚙ Reactivity settings  —  tweak how hard each agent feels things"):
    rx_col1, rx_col2 = st.columns(2)
    with rx_col1:
        st.markdown("**Alex** (neurotic)")
        st.slider(
            "Reactivity multiplier",
            min_value=0.3, max_value=2.0,
            value=float(st.session_state.get("alex_reactivity", REACTIVITY["neurotic"])),
            step=0.05, key="alex_reactivity",
            help="Scales how strongly incoming events affect Alex's emotions. 1.0 = baseline.",
        )
        st.caption(_rx_ref)
    with rx_col2:
        st.markdown("**Sam** (resilient)")
        st.slider(
            "Reactivity multiplier",
            min_value=0.3, max_value=2.0,
            value=float(st.session_state.get("sam_reactivity", REACTIVITY["resilient"])),
            step=0.05, key="sam_reactivity",
            help="Scales how strongly incoming events affect Sam's emotions. 1.0 = baseline.",
        )
        st.caption(_rx_ref)
    st.info("Changes apply after ↺ Reset.", icon="ℹ️")

# Opening message display
opener_speaker, opener_text = st.session_state.opening_speaker, st.session_state.opening_text
st.markdown(
    f'<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;'
    f'padding:10px 14px;font-size:0.83rem;color:#78350f;margin-bottom:0.5rem;">'
    f'<b>{opener_speaker}</b> (opening): "{opener_text}"</div>',
    unsafe_allow_html=True
)

# ── Timeline scrubber ─────────────────────────────────────────────────────────
n_msgs = len(st.session_state.messages)
vt = n_msgs      # default: live (last turn)
is_live = True

if n_msgs > 1:
    scr_col, live_col = st.columns([5, 1])
    with scr_col:
        vt = st.slider(
            "⏮ Time travel",
            min_value=1,
            max_value=n_msgs,
            value=n_msgs,
            key="app_timeline",
            format="Turn %d",
            help="Drag left to replay earlier turns and see how emotions evolved",
        )
    with live_col:
        is_live = (vt == n_msgs)
        if not is_live:
            if st.button("↩ Now", use_container_width=True, key="jump_live_btn"):
                st.session_state["app_timeline"] = n_msgs
                st.rerun()

    if not is_live:
        viewing_msg = st.session_state.messages[vt - 1]
        st.markdown(
            f'<div style="font-family:\'Fira Code\',monospace;font-size:0.68rem;'
            f'color:#c2410c;margin-bottom:0.3rem;">'
            f'⏪ Viewing Turn {vt} of {n_msgs} · '
            f'{viewing_msg["speaker"]} just spoke · '
            f'drag right to return to present</div>',
            unsafe_allow_html=True,
        )

# Resolve what each agent panel should display
if is_live or n_msgs == 0:
    alex_display = st.session_state.alex
    sam_display  = st.session_state.sam
else:
    snap = st.session_state.messages[vt - 1]
    alex_display = snap["alex_snapshot"]
    sam_display  = snap["sam_snapshot"]

# Main three-column layout
left_col, mid_col, right_col = st.columns([1, 2, 1])

# ── Alex panel ────────────────────────────────────────────────────────────────
with left_col:
    history_border = "border-color:#c2410c;" if not is_live else ""
    st.markdown(
        f'<div class="agent-panel" style="{history_border}">'
        '<div class="agent-header">Alex</div>'
        '<span class="personality-badge badge-neurotic">neurotic</span>',
        unsafe_allow_html=True
    )
    if not is_live:
        st.markdown(
            f'<div style="font-family:\'Fira Code\',monospace;font-size:0.62rem;'
            f'color:#c2410c;margin-bottom:4px;">📍 turn {vt}</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="section-label">Active Emotions</div>', unsafe_allow_html=True)
    render_emotion_panel(alex_display)
    st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Behavioral Profile</div>', unsafe_allow_html=True)
    render_behavioral_params(alex_display)

    st.markdown(
        '<div style="margin-top:1rem;font-family:\'Fira Code\',monospace;font-size:0.65rem;color:#94a3b8;">'
        'decay λ = 0.05 · emotions linger long</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ── Conversation ──────────────────────────────────────────────────────────────
with mid_col:
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">'
        f'<span style="font-family:\'Fira Code\',monospace;font-size:0.7rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Conversation</span>'
        f'<span class="status-pill">Turn {st.session_state.turn}</span>'
        f'</div>',
        unsafe_allow_html=True
    )
    render_messages(highlight_turn=vt if not is_live else 0)

# ── Sam panel ─────────────────────────────────────────────────────────────────
with right_col:
    st.markdown(
        f'<div class="agent-panel" style="{history_border}">'
        '<div class="agent-header">Sam</div>'
        '<span class="personality-badge badge-resilient">resilient</span>',
        unsafe_allow_html=True
    )
    if not is_live:
        st.markdown(
            f'<div style="font-family:\'Fira Code\',monospace;font-size:0.62rem;'
            f'color:#c2410c;margin-bottom:4px;">📍 turn {vt}</div>',
            unsafe_allow_html=True,
        )
    st.markdown('<div class="section-label">Active Emotions</div>', unsafe_allow_html=True)
    render_emotion_panel(sam_display)
    st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Behavioral Profile</div>', unsafe_allow_html=True)
    render_behavioral_params(sam_display)

    st.markdown(
        '<div style="margin-top:1rem;font-family:\'Fira Code\',monospace;font-size:0.65rem;color:#94a3b8;">'
        'decay λ = 0.22 · emotions fade quickly</div>',
        unsafe_allow_html=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div style="margin-top:2rem;text-align:center;font-family:\'Fira Code\',monospace;'
    'font-size:0.65rem;color:#cbd5e1;letter-spacing:0.05em;">'
    'OCC APPRAISAL THEORY · GROQ LLaMA-3.3-70B · CODECOOL BOOTCAMP DEMO</div>',
    unsafe_allow_html=True
)

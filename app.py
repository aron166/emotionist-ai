"""
Emotionist.ai — Streamlit demo UI
Run: streamlit run app.py
"""

import os
import time
import html
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="Emotionist.ai",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Design system ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root{
    --void:#08080a;
    --surface:#111114;
    --surface-2:#16161b;
    --border:rgba(255,255,255,0.08);
    --border-strong:rgba(255,255,255,0.16);
    --violet:#7c4dff;
    --violet-bright:#9d7bff;
    --violet-dim:#5b3bc4;
    --violet-glow:rgba(124,77,255,0.35);
    --amber:#facc15;
    --cyan:#22d3ee;
    --text:#f4f4f5;
    --muted:#a1a1aa;
    --dim:#5c5c66;
}

/* ── Base / atmosphere ─────────────────────────────────────────────────── */
html, body, [class*="css"] { font-family:'Hanken Grotesk', sans-serif; }

.stApp{
    background:
        radial-gradient(120% 80% at 88% -12%, rgba(124,77,255,0.20) 0%, rgba(124,77,255,0) 55%),
        radial-gradient(90% 70% at -5% 112%, rgba(34,211,238,0.07) 0%, rgba(0,0,0,0) 50%),
        var(--void);
}
/* film grain */
.stApp::before{
    content:""; position:fixed; inset:0; pointer-events:none; z-index:0; opacity:0.045;
    background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
}
/* chrome decoration, top-right (the deck's signature) */
.stApp::after{
    content:""; position:fixed; top:-30px; right:-40px; width:480px; height:230px;
    background:url('app/static/chrome.png') no-repeat right top / contain;
    opacity:0.5; pointer-events:none; z-index:0;
    -webkit-mask-image:linear-gradient(225deg, #000 25%, transparent 78%);
            mask-image:linear-gradient(225deg, #000 25%, transparent 78%);
}
.block-container{ position:relative; z-index:1; padding-top:2.2rem; padding-bottom:3rem; max-width:1540px; }

/* ── Hero / header ─────────────────────────────────────────────────────── */
.main-title{
    font-family:'Anton', sans-serif; font-weight:400;
    font-size:3.4rem; line-height:0.9; letter-spacing:0.01em;
    text-transform:uppercase; color:#fff; margin:0;
    text-shadow:0 0 40px rgba(124,77,255,0.25);
}
.main-title .dot{ color:var(--violet); }
.main-subtitle{
    font-family:'JetBrains Mono', monospace; font-size:0.68rem;
    color:var(--muted); letter-spacing:0.3em; text-transform:uppercase;
    margin-top:0.55rem; margin-bottom:1.8rem;
}

/* ── Section + meta labels ─────────────────────────────────────────────── */
.section-label{
    font-family:'JetBrains Mono', monospace; font-size:0.58rem;
    letter-spacing:0.2em; text-transform:uppercase; color:var(--dim);
    margin:1.1rem 0 0.6rem; display:flex; align-items:center; gap:9px;
}
.section-label::before{ content:""; width:14px; height:1px; background:var(--violet); display:inline-block; }
.decay-note{
    font-family:'JetBrains Mono', monospace; font-size:0.58rem;
    color:var(--dim); letter-spacing:0.08em; margin-top:1.1rem;
}
.hist-marker{
    font-family:'JetBrains Mono', monospace; font-size:0.58rem;
    color:var(--violet-bright); letter-spacing:0.08em; margin:2px 0 6px;
}

/* ── Agent header + badges ─────────────────────────────────────────────── */
.agent-header{
    font-family:'Anton', sans-serif; font-size:1.6rem; line-height:1;
    text-transform:uppercase; letter-spacing:0.02em; color:#fff;
}
.personality-badge{
    display:inline-block; font-family:'JetBrains Mono', monospace; font-size:0.56rem;
    font-weight:500; padding:3px 10px; border-radius:99px; letter-spacing:0.14em;
    text-transform:uppercase; margin-top:9px;
}
.badge-neurotic  { background:rgba(124,77,255,0.14); color:var(--violet-bright); border:1px solid rgba(124,77,255,0.42); }
.badge-resilient { background:rgba(34,211,238,0.12);  color:var(--cyan);          border:1px solid rgba(34,211,238,0.38); }
.badge-average   { background:rgba(250,204,21,0.12);  color:var(--amber);         border:1px solid rgba(250,204,21,0.35); }

/* ── Emotion bars ──────────────────────────────────────────────────────── */
.emotion-row{ display:flex; align-items:center; gap:10px; margin-bottom:7px; }
.emotion-name{ font-size:0.72rem; font-weight:600; color:#d4d4d8; width:92px; flex-shrink:0; }
.bar-track{ flex:1; height:6px; background:rgba(255,255,255,0.06); border-radius:99px; overflow:hidden; }
.bar-fill{
    height:100%; border-radius:99px;
    transition:width .55s cubic-bezier(.2,.8,.2,1);
    box-shadow:0 0 12px -3px rgba(255,255,255,0.45);
}
.emotion-pct{ font-family:'JetBrains Mono', monospace; font-size:0.62rem; color:var(--muted); width:30px; text-align:right; flex-shrink:0; }
.calm-label{ font-family:'JetBrains Mono', monospace; font-size:0.72rem; color:var(--dim); letter-spacing:0.06em; }

/* ── Behavioral param chips ────────────────────────────────────────────── */
.param-grid{ display:grid; grid-template-columns:1fr 1fr; gap:7px; margin-top:6px; }
.param-chip{
    font-size:0.68rem; padding:5px 10px; border-radius:8px;
    display:flex; justify-content:space-between; align-items:center;
    background:var(--surface-2); border:1px solid var(--border);
}
.param-label{ color:var(--muted); font-weight:400; }
.param-value{ font-family:'JetBrains Mono', monospace; font-weight:500; font-size:0.6rem; letter-spacing:0.04em; }
.level-very-high .param-value{ color:#fb7185; }
.level-high      .param-value{ color:var(--amber); }
.level-moderate  .param-value{ color:var(--muted); }
.level-low       .param-value{ color:#a3e635; }
.level-very-low  .param-value{ color:var(--cyan); }

/* ── Chat ──────────────────────────────────────────────────────────────── */
.chat-area{ display:flex; flex-direction:column; gap:14px; padding:0.3rem 0; }
.message-wrap{ display:flex; flex-direction:column; gap:5px; }
.message-wrap.alex{ align-items:flex-start; }
.message-wrap.sam { align-items:flex-end; }
.message-bubble{
    max-width:88%; padding:11px 15px; border-radius:14px;
    font-size:0.86rem; line-height:1.55; color:var(--text);
    background:var(--surface); border:1px solid var(--border);
}
.bubble-alex{ border-bottom-left-radius:4px;  border-left:2px solid var(--violet); }
.bubble-sam { border-bottom-right-radius:4px; border-right:2px solid var(--cyan); }
.message-meta{
    font-family:'JetBrains Mono', monospace; font-size:0.56rem; color:var(--dim);
    padding:0 6px; letter-spacing:0.1em; text-transform:uppercase;
}

/* ── Appraisal event badge ─────────────────────────────────────────────── */
.event-badge{
    display:inline-flex; align-items:center; gap:7px;
    font-family:'JetBrains Mono', monospace; font-size:0.6rem;
    padding:3px 9px; border-radius:99px;
    background:rgba(255,255,255,0.04); border:1px solid var(--border);
    color:var(--muted); margin-top:3px; letter-spacing:0.05em;
}
.event-dot{ width:6px; height:6px; border-radius:50%; flex-shrink:0; }

/* ── Conversation head + status pill ───────────────────────────────────── */
.conv-head{ display:flex; align-items:center; justify-content:space-between; margin-bottom:0.8rem; }
.conv-label{ font-family:'JetBrains Mono', monospace; font-size:0.64rem; color:var(--dim); text-transform:uppercase; letter-spacing:0.2em; }
.status-pill{
    display:inline-block; font-family:'JetBrains Mono', monospace; font-size:0.62rem;
    padding:3px 11px; border-radius:99px; letter-spacing:0.06em;
    background:rgba(124,77,255,0.1); color:var(--violet-bright); border:1px solid rgba(124,77,255,0.3);
}

/* ── Opening line + history banner ─────────────────────────────────────── */
.opener{
    background:var(--surface); border:1px solid var(--border); border-left:2px solid var(--amber);
    border-radius:10px; padding:11px 15px; font-size:0.82rem; color:var(--muted); margin-bottom:1rem;
}
.opener-who{ color:var(--text); font-weight:600; }
.hist-banner{
    font-family:'JetBrains Mono', monospace; font-size:0.62rem;
    color:var(--violet-bright); letter-spacing:0.05em; margin-bottom:0.4rem;
}
.thin-divider{ border:none; border-top:1px solid var(--border); margin:0.9rem 0; }
.footer{
    margin-top:2.4rem; text-align:center; font-family:'JetBrains Mono', monospace;
    font-size:0.6rem; color:#3a3a42; letter-spacing:0.16em; text-transform:uppercase;
}

/* ── Streamlit widget overrides ────────────────────────────────────────── */
/* cards = bordered containers */
[data-testid="stVerticalBlockBorderWrapper"]{
    background:linear-gradient(180deg, var(--surface) 0%, #0c0c0f 100%);
    border:1px solid var(--border) !important;
    border-radius:16px;
    padding:1.3rem 1.3rem 1.5rem;
    box-shadow:0 1px 0 rgba(255,255,255,0.04) inset, 0 24px 48px -34px rgba(0,0,0,0.9);
    animation:riseIn .5s ease both;
}
@keyframes riseIn{ from{ opacity:0; transform:translateY(12px); } to{ opacity:1; transform:none; } }

/* buttons */
.stButton > button{
    font-family:'Hanken Grotesk', sans-serif; font-weight:600; font-size:0.82rem;
    border-radius:10px; border:1px solid var(--border-strong);
    background:var(--surface-2); color:var(--text);
    transition:all .18s ease; letter-spacing:0.02em;
}
.stButton > button:hover{ border-color:var(--violet); color:#fff; background:#1c1c22; transform:translateY(-1px); }
.stButton > button[kind="primary"]{
    background:linear-gradient(135deg, var(--violet) 0%, var(--violet-dim) 100%);
    border:1px solid var(--violet-bright); color:#fff;
    box-shadow:0 10px 28px -12px var(--violet);
}
.stButton > button[kind="primary"]:hover{ filter:brightness(1.12); transform:translateY(-1px); }

/* expander */
[data-testid="stExpander"]{ border:1px solid var(--border); border-radius:12px; background:var(--surface); }
[data-testid="stExpander"] summary{ font-family:'JetBrains Mono', monospace; font-size:0.72rem; letter-spacing:0.04em; color:var(--muted); }

/* selectbox / inputs */
[data-baseweb="select"] > div, [data-baseweb="input"] > div{ border-radius:10px !important; }
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
    "Dog died": (
        "Alex",
        "Sam, I had a car accident today and I lived thank god — but my dog Mr. Larry didn't make it."
    ),
    "Cancelled project": (
        "Alex",
        "Hey, I heard the big presentation got cancelled last minute — the client just pulled out entirely. Did you know about this?"
    ),
    "Unexpected praise": (
        "Sam",
        "Alex, I just got out of a meeting and the director specifically called out your work as the reason the Q1 numbers looked so good. Genuinely impressive."
    ),
    "Unfair blame": (
        "Alex",
        "I cannot believe they pinned the whole deployment failure on our team. We followed the process exactly. This is completely unfair."
    ),
    "New opportunity": (
        "Sam",
        "Good news — leadership approved the new project proposal and they want us to lead it. This could be a huge deal for both of us."
    ),
}

# ── Session state init ────────────────────────────────────────────────────────
def init_state(topic_key: str = "Cancelled project"):
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
        st.markdown('<div class="calm-label">— calm —</div>', unsafe_allow_html=True)
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
        flags.append("self")
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
            '<div style="color:#5c5c66;font-size:0.85rem;padding:1.2rem 0;">'
            'Press <b style="color:#a1a1aa;">Next Turn</b> to start the conversation.</div>',
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
        hl_style = "outline:2px solid var(--violet);outline-offset:2px;" if is_hl else ""
        html += f"""
        <div class="message-wrap {cls}">
            <div class="message-bubble {bubble_cls}" style="{hl_style}">{html.escape(msg["text"])}</div>
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
st.markdown(
    '<div class="main-title">EMOTIONIST<span class="dot">.AI</span></div>',
    unsafe_allow_html=True
)
st.markdown(
    '<div class="main-subtitle">OCC Appraisal Engine — Emotional Agent Demo</div>',
    unsafe_allow_html=True
)

# Controls bar
with st.container():
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([2, 1, 1, 1])

    with ctrl_col1:
        topic = st.selectbox(
            "Conversation starter",
            list(STARTER_TOPICS.keys()),
            index=list(STARTER_TOPICS).index("Cancelled project"),
            label_visibility="collapsed",
            key="topic_select"
        )

    with ctrl_col2:
        if st.button("Reset", use_container_width=True):
            init_state(topic)
            st.rerun()

    with ctrl_col3:
        if st.button("Next Turn", use_container_width=True, type="primary"):
            if not os.environ.get("GROQ_API_KEY"):
                st.error("GROQ_API_KEY not set in .env")
            else:
                with st.spinner(""):
                    do_turn()
                st.rerun()

    with ctrl_col4:
        if st.button("Run 6 Turns", use_container_width=True):
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
with st.expander("Inject a custom message into the conversation"):
    custom_col1, custom_col2 = st.columns([4, 1])
    with custom_col1:
        custom_msg = st.text_input("Message", placeholder="Type something to say to the next agent…", label_visibility="collapsed")
    with custom_col2:
        if st.button("Send", use_container_width=True) and custom_msg.strip():
            if not os.environ.get("GROQ_API_KEY"):
                st.error("GROQ_API_KEY not set in .env")
            else:
                st.session_state.next_message = custom_msg.strip()
                with st.spinner(""):
                    do_turn()
                st.rerun()

# Reactivity tuning
_rx_ref = f"resilient {REACTIVITY['resilient']}  ·  average {REACTIVITY['average']}  ·  neurotic {REACTIVITY['neurotic']}"
with st.expander("Reactivity settings — tweak how hard each agent feels things"):
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
    st.caption("Changes apply after Reset.")

# Opening message display
opener_speaker, opener_text = st.session_state.opening_speaker, st.session_state.opening_text
st.markdown(
    f'<div class="opener"><span class="opener-who">{opener_speaker}</span> · opening — “{opener_text}”</div>',
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
            "Time travel",
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
            if st.button("Now", use_container_width=True, key="jump_live_btn"):
                st.session_state["app_timeline"] = n_msgs
                st.rerun()

    if not is_live:
        viewing_msg = st.session_state.messages[vt - 1]
        st.markdown(
            f'<div class="hist-banner">Viewing Turn {vt} of {n_msgs} · '
            f'{viewing_msg["speaker"]} just spoke · drag right to return to present</div>',
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
left_col, mid_col, right_col = st.columns([1, 2, 1], gap="large")

# ── Alex panel ────────────────────────────────────────────────────────────────
with left_col:
    with st.container(border=True):
        st.markdown(
            '<div class="agent-header">Alex</div>'
            '<span class="personality-badge badge-neurotic">neurotic</span>',
            unsafe_allow_html=True
        )
        if not is_live:
            st.markdown(f'<div class="hist-marker">turn {vt}</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Active Emotions</div>', unsafe_allow_html=True)
        render_emotion_panel(alex_display)
        st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Behavioral Profile</div>', unsafe_allow_html=True)
        render_behavioral_params(alex_display)
        st.markdown('<div class="decay-note">decay λ 0.05 · emotions linger long</div>', unsafe_allow_html=True)

# ── Conversation ──────────────────────────────────────────────────────────────
with mid_col:
    st.markdown(
        '<div class="conv-head">'
        '<span class="conv-label">Conversation</span>'
        f'<span class="status-pill">Turn {st.session_state.turn}</span>'
        '</div>',
        unsafe_allow_html=True
    )
    render_messages(highlight_turn=vt if not is_live else 0)

# ── Sam panel ─────────────────────────────────────────────────────────────────
with right_col:
    with st.container(border=True):
        st.markdown(
            '<div class="agent-header">Sam</div>'
            '<span class="personality-badge badge-resilient">resilient</span>',
            unsafe_allow_html=True
        )
        if not is_live:
            st.markdown(f'<div class="hist-marker">turn {vt}</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Active Emotions</div>', unsafe_allow_html=True)
        render_emotion_panel(sam_display)
        st.markdown('<hr class="thin-divider">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Behavioral Profile</div>', unsafe_allow_html=True)
        render_behavioral_params(sam_display)
        st.markdown('<div class="decay-note">decay λ 0.22 · emotions fade quickly</div>', unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="footer">OCC Appraisal Theory · Groq LLaMA-3.3-70B · Emotionist.ai</div>',
    unsafe_allow_html=True
)

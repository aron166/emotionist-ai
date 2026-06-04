"""
Emotionist.ai — Single agent chat
"""
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Chat · Emotionist.ai",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Source+Sans+3:wght@400;600&family=Fira+Code:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Source Sans 3', sans-serif; }
.stApp { background: #faf8f4; }
.block-container { padding-top: 1.5rem; }

.page-title { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 700; color: #1e293b; }
.page-sub { font-family: 'Fira Code', monospace; font-size: 0.72rem; color: #c2410c; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 1.5rem; }

.emotion-row { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
.emotion-name { font-size:0.78rem; font-weight:600; color:#334155; width:100px; flex-shrink:0; }
.bar-track { flex:1; height:7px; background:#f1f5f9; border-radius:4px; overflow:hidden; }
.bar-fill { height:100%; border-radius:4px; }
.emotion-pct { font-family:'Fira Code',monospace; font-size:0.65rem; color:#64748b; width:30px; text-align:right; flex-shrink:0; }

.section-label { font-family:'Fira Code',monospace; font-size:0.62rem; letter-spacing:0.1em; text-transform:uppercase; color:#94a3b8; margin-bottom:0.4rem; margin-top:0.9rem; }

.user-bubble { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px 12px 3px 12px; padding:10px 14px; font-size:0.88rem; color:#1e293b; margin-bottom:4px; }
.agent-bubble { background:#ffffff; border:1px solid #e2d9cc; border-radius:12px 12px 12px 3px; padding:10px 14px; font-size:0.88rem; color:#1e293b; margin-bottom:4px; }
.meta { font-family:'Fira Code',monospace; font-size:0.62rem; color:#94a3b8; margin-bottom:10px; }

.event-badge { display:inline-flex; align-items:center; gap:5px; font-family:'Fira Code',monospace; font-size:0.63rem; padding:2px 8px; border-radius:99px; background:#f8f9fa; border:1px solid #e2e8f0; color:#475569; }
.event-dot { width:6px; height:6px; border-radius:50%; flex-shrink:0; }

.personality-badge { display:inline-block; font-family:'Fira Code',monospace; font-size:0.65rem; padding:2px 8px; border-radius:99px; letter-spacing:0.05em; text-transform:uppercase; }
.badge-neurotic  { background:#fde8e8; color:#b91c1c; border:1px solid #fca5a5; }
.badge-resilient { background:#dcfce7; color:#15803d; border:1px solid #86efac; }
.badge-average   { background:#eff6ff; color:#1d4ed8; border:1px solid #93c5fd; }

.system-prompt-box { background:#1e1b2e; color:#a9b1d6; font-family:'Fira Code',monospace; font-size:0.7rem; border-radius:8px; padding:1rem; line-height:1.6; white-space:pre-wrap; max-height:300px; overflow-y:auto; }
</style>
""", unsafe_allow_html=True)

from agents.agent import Agent
from engine.appraisal import REACTIVITY

EMOTION_COLORS = {
    "Joy":"#f59e0b","Hope":"#10b981","Satisfaction":"#84cc16","Relief":"#06b6d4",
    "HappyFor":"#f97316","Pride":"#d97706","Admiration":"#0891b2","Love":"#ec4899",
    "Gratification":"#f59e0b","Gratitude":"#059669","Trust":"#14b8a6","Surprise":"#a78bfa",
    "Anticipation":"#8b5cf6","Distress":"#ef4444","Fear":"#6366f1","FearsConfirmed":"#dc2626",
    "Disappointment":"#8b5cf6","Pity":"#94a3b8","Gloating":"#a16207","Resentment":"#b91c1c",
    "Shame":"#7c3aed","Reproach":"#9f1239","Hate":"#1e293b","Remorse":"#6d28d9",
    "Anger":"#dc2626","Sadness":"#64748b","Disgust":"#78716c","Envy":"#4d7c0f",
    "Guilt":"#475569","Contempt":"#1e1b4b",
}

EVENT_COLORS = {
    "compliment":"#10b981","achievement":"#f59e0b","good_news":"#84cc16",
    "agreement":"#06b6d4","praise_of_other":"#0891b2","insult":"#dc2626",
    "threat":"#6366f1","bad_news":"#ef4444","failure":"#7c3aed",
    "disagreement":"#f97316","blame_of_other":"#b91c1c","neutral":"#94a3b8",
}

# ── Sidebar config ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Agent Setup")
    agent_name = st.text_input("Name", value="Morgan")
    personality = st.selectbox("Personality", ["neurotic", "average", "resilient"], index=1)
    _rx_default = REACTIVITY.get(personality, 1.0)
    reactivity = st.slider(
        "Reactivity",
        min_value=0.3, max_value=2.0,
        value=_rx_default, step=0.05,
        key=f"chat_reactivity_{personality}",
        help="Scales how strongly events spike this agent's emotions. 1.0 = baseline.",
    )
    st.caption(f"resilient · {REACTIVITY['resilient']}  ·  average · {REACTIVITY['average']}  ·  neurotic · {REACTIVITY['neurotic']}")
    persona_text = st.text_area(
        "Persona",
        value=f"You are {agent_name}, a thoughtful person having a conversation.",
        height=120,
    )

    st.markdown("---")
    st.markdown("### Pre-seed emotions")
    st.caption("Optionally inject emotions before the conversation starts.")

    seed_options = ["None", "Anger", "Joy", "Fear", "Shame", "Pride", "Distress", "Gratitude", "Sadness", "Anticipation"]
    seed_emotion = st.selectbox("Emotion", seed_options)
    seed_intensity = st.slider("Intensity", 0.1, 1.0, 0.5, 0.05)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Apply seed", use_container_width=True):
            if "chat_agent" in st.session_state and seed_emotion != "None":
                st.session_state.chat_agent.entity.emotions[seed_emotion].activate(seed_intensity)
                st.rerun()
    with col_b:
        if st.button("Reset agent", use_container_width=True):
            st.session_state.chat_agent = Agent(agent_name, personality, persona_text, reactivity=reactivity)
            st.session_state.chat_messages = []
            st.rerun()

    st.markdown("---")
    show_system_prompt = st.toggle("Show live system prompt", value=False)
    show_event_badges = st.toggle("Show appraisal events", value=True)

# ── Init ──────────────────────────────────────────────────────────────────────
if "chat_agent" not in st.session_state or st.session_state.get("chat_agent_name") != agent_name:
    st.session_state.chat_agent = Agent(agent_name, personality, persona_text, reactivity=reactivity)
    st.session_state.chat_messages = []
    st.session_state.chat_agent_name = agent_name

agent: Agent = st.session_state.chat_agent

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">💬 Chat</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Talk to a single emotional agent · watch its state shift in real time</div>', unsafe_allow_html=True)

# ── Main layout ───────────────────────────────────────────────────────────────
chat_col, state_col = st.columns([3, 1])

with state_col:
    badge_cls = f"badge-{personality}"
    st.markdown(
        f'<div style="font-family:\'Playfair Display\',serif;font-size:1.1rem;font-weight:700;color:#1e293b;margin-bottom:4px;">{agent_name}</div>'
        f'<span class="personality-badge {badge_cls}">{personality}</span>',
        unsafe_allow_html=True
    )

    st.markdown('<div class="section-label">Active Emotions</div>', unsafe_allow_html=True)
    active = agent.entity.get_active_emotions()
    if not active:
        st.markdown('<div style="color:#94a3b8;font-size:0.8rem;font-style:italic;">calm</div>', unsafe_allow_html=True)
    else:
        bars = ""
        for name, intensity in active[:8]:
            color = EMOTION_COLORS.get(name, "#94a3b8")
            pct = int(intensity * 100)
            bars += (
                f'<div class="emotion-row">'
                f'<span class="emotion-name">{name}</span>'
                f'<div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color};"></div></div>'
                f'<span class="emotion-pct">{pct}%</span>'
                f'</div>'
            )
        st.markdown(bars, unsafe_allow_html=True)

    st.markdown('<div class="section-label">Parameters</div>', unsafe_allow_html=True)
    dr = agent.entity.DECAY_RATES[personality]
    rx = agent.entity.reactivity
    st.markdown(
        f'<div style="font-family:\'Fira Code\',monospace;font-size:0.68rem;color:#64748b;">'
        f'λ decay = {dr} &nbsp;·&nbsp; reactivity = {rx:.2f}</div>',
        unsafe_allow_html=True
    )

    if show_system_prompt:
        st.markdown('<div class="section-label" style="margin-top:1.2rem;">Live System Prompt</div>', unsafe_allow_html=True)
        live_prompt = agent.prompt_modifier.build_system_prompt(agent.entity, agent.base_persona)
        st.markdown(f'<div class="system-prompt-box">{live_prompt}</div>', unsafe_allow_html=True)

with chat_col:
    # Message history
    for msg in st.session_state.chat_messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["text"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="meta" style="text-align:right;">You</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="agent-bubble">{msg["text"]}</div>', unsafe_allow_html=True)
            meta_parts = [agent_name]
            if show_event_badges and msg.get("event"):
                ev = msg["event"]
                et = ev.get("event_type", "neutral")
                sev = ev.get("severity", 0.0)
                color = EVENT_COLORS.get(et, "#94a3b8")
                flags = []
                if ev.get("directed_at_self"): flags.append("→self")
                if ev.get("intentional"): flags.append("intentional")
                flag_str = (" · " + " · ".join(flags)) if flags else ""
                badge = (
                    f'<span class="event-badge">'
                    f'<span class="event-dot" style="background:{color};"></span>'
                    f'{et} · {sev:.2f}{flag_str}'
                    f'</span>'
                )
                st.markdown(f'<div class="meta">{agent_name} &nbsp;{badge}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="meta">{agent_name}</div>', unsafe_allow_html=True)

    if not st.session_state.chat_messages:
        st.markdown(
            '<div style="color:#94a3b8;font-size:0.85rem;padding:2rem 0;text-align:center;">'
            'Say something to start the conversation.</div>',
            unsafe_allow_html=True
        )

    # Input
    with st.form("chat_form", clear_on_submit=True):
        input_col, btn_col = st.columns([5, 1])
        with input_col:
            user_input = st.text_input(
                "Message",
                placeholder=f"Say something to {agent_name}…",
                label_visibility="collapsed",
            )
        with btn_col:
            submitted = st.form_submit_button("Send", use_container_width=True, type="primary")

    if submitted and user_input.strip():
        if not os.environ.get("GROQ_API_KEY"):
            st.error("GROQ_API_KEY not set in .env")
        else:
            st.session_state.chat_messages.append({"role": "user", "text": user_input})
            with st.spinner(""):
                reply = agent.receive_and_respond(user_input)
            st.session_state.chat_messages.append({
                "role": "agent",
                "text": reply,
                "event": agent.last_event,
            })
            st.rerun()

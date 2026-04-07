"""
Emotionist.ai — Scenario Builder
Design your own two-agent emotional scenario and run it.
"""
import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Scenarios · Emotionist.ai",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
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
.emotion-name { font-size:0.75rem; font-weight:600; color:#334155; width:88px; flex-shrink:0; }
.bar-track { flex:1; height:6px; background:#f1f5f9; border-radius:4px; overflow:hidden; }
.bar-fill { height:100%; border-radius:4px; }
.emotion-pct { font-family:'Fira Code',monospace; font-size:0.63rem; color:#64748b; width:28px; text-align:right; flex-shrink:0; }

.section-label { font-family:'Fira Code',monospace; font-size:0.62rem; letter-spacing:0.1em; text-transform:uppercase; color:#94a3b8; margin-bottom:0.4rem; margin-top:0.9rem; }
.card { background:#ffffff; border:1px solid #e8e0d4; border-radius:12px; padding:1.2rem; }

.personality-badge { display:inline-block; font-family:'Fira Code',monospace; font-size:0.65rem; padding:2px 8px; border-radius:99px; letter-spacing:0.05em; text-transform:uppercase; }
.badge-neurotic  { background:#fde8e8; color:#b91c1c; border:1px solid #fca5a5; }
.badge-resilient { background:#dcfce7; color:#15803d; border:1px solid #86efac; }
.badge-average   { background:#eff6ff; color:#1d4ed8; border:1px solid #93c5fd; }

.bubble-a { background:#fff7ed; border:1px solid #fed7aa; border-radius:12px 12px 12px 3px; padding:10px 14px; font-size:0.88rem; color:#1e293b; margin-bottom:3px; }
.bubble-b { background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12px 12px 3px 12px; padding:10px 14px; font-size:0.88rem; color:#1e293b; margin-bottom:3px; }
.meta { font-family:'Fira Code',monospace; font-size:0.62rem; color:#94a3b8; margin-bottom:8px; }
.event-badge { display:inline-flex;align-items:center;gap:5px;font-family:'Fira Code',monospace;font-size:0.63rem;padding:2px 8px;border-radius:99px;background:#f8f9fa;border:1px solid #e2e8f0;color:#475569; }
.event-dot { width:6px;height:6px;border-radius:50%;flex-shrink:0; }
</style>
""", unsafe_allow_html=True)

from agents.agent import Agent
from engine.appraisal import REACTIVITY

EMOTION_COLORS = {
    "Joy":"#f59e0b","Hope":"#10b981","Satisfaction":"#84cc16","Relief":"#06b6d4",
    "HappyFor":"#f97316","Pride":"#d97706","Admiration":"#0891b2","Love":"#ec4899",
    "Gratification":"#f59e0b","Gratitude":"#059669","Trust":"#14b8a6","Surprise":"#a78bfa",
    "Anticipation":"#8b5cf6","Distress":"#ef4444","Fear":"#6366f1","FearsConfirmed":"#dc2626",
    "Disappointment":"#8b5cf6","Pity":"#94a3b8","Resentment":"#b91c1c","Shame":"#7c3aed",
    "Reproach":"#9f1239","Hate":"#1e293b","Remorse":"#6d28d9","Anger":"#dc2626",
    "Sadness":"#64748b","Disgust":"#78716c","Envy":"#4d7c0f","Guilt":"#475569","Contempt":"#1e1b4b",
}
EVENT_COLORS = {
    "compliment":"#10b981","achievement":"#f59e0b","good_news":"#84cc16",
    "agreement":"#06b6d4","praise_of_other":"#0891b2","insult":"#dc2626",
    "threat":"#6366f1","bad_news":"#ef4444","failure":"#7c3aed",
    "disagreement":"#f97316","blame_of_other":"#b91c1c","neutral":"#94a3b8",
}

PRESET_SCENARIOS = {
    "✍️ Custom (blank)": {
        "agent_a_name": "Agent A", "agent_a_personality": "neurotic",
        "agent_a_persona": "You are Agent A. You are having a conversation with Agent B.",
        "agent_a_seed": "None", "agent_a_seed_intensity": 0.0,
        "agent_b_name": "Agent B", "agent_b_personality": "resilient",
        "agent_b_persona": "You are Agent B. You are having a conversation with Agent A.",
        "agent_b_seed": "None", "agent_b_seed_intensity": 0.0,
        "opening_speaker": "A",
        "opening_message": "Hey, what do you think we should do about this situation?",
    },
    "😤 Workplace conflict": {
        "agent_a_name": "Jordan", "agent_a_personality": "neurotic",
        "agent_a_persona": "You are Jordan, a senior developer who has been working nights to hit a deadline. You feel undervalued and you're barely holding it together. You're talking to Casey, your project manager.",
        "agent_a_seed": "Distress", "agent_a_seed_intensity": 0.55,
        "agent_b_name": "Casey", "agent_b_personality": "average",
        "agent_b_persona": "You are Casey, a project manager. You've just been told that a key milestone was missed and you're under pressure from above. You're talking to Jordan, your senior dev.",
        "agent_b_seed": "Fear", "agent_b_seed_intensity": 0.45,
        "opening_speaker": "A",
        "opening_message": "Casey, I need you to tell leadership that the deadline was unrealistic. I've worked 60-hour weeks and the goalposts keep moving. This isn't fair.",
    },
    "💔 Friendship rupture": {
        "agent_a_name": "Alex", "agent_a_personality": "neurotic",
        "agent_a_persona": "You are Alex. You found out your close friend Sam told other people something you shared in confidence. You feel deeply betrayed. You're confronting Sam about it.",
        "agent_a_seed": "Anger", "agent_a_seed_intensity": 0.7,
        "agent_b_name": "Sam", "agent_b_personality": "resilient",
        "agent_b_persona": "You are Sam. Your friend Alex is upset with you and you're not entirely sure why — you thought you were just being helpful by sharing some context. You feel defensive but you care about the friendship.",
        "agent_b_seed": "Surprise", "agent_b_seed_intensity": 0.5,
        "opening_speaker": "A",
        "opening_message": "I can't believe you told people what I told you. I trusted you. That was private.",
    },
    "🎉 Unexpected good news": {
        "agent_a_name": "Riley", "agent_a_personality": "resilient",
        "agent_a_persona": "You are Riley, a colleague who has just heard that a mutual friend got the promotion they both applied for. You're genuinely happy for them but also dealing with your own disappointment privately. You're talking to the person who got promoted.",
        "agent_a_seed": "HappyFor", "agent_a_seed_intensity": 0.5,
        "agent_b_name": "Drew", "agent_b_personality": "average",
        "agent_b_persona": "You are Drew. You just found out you got the promotion and you know Riley also applied. You're thrilled but aware it's complicated. You want to share the news with Riley.",
        "agent_b_seed": "Pride", "agent_b_seed_intensity": 0.65,
        "opening_speaker": "B",
        "opening_message": "Hey Riley — I just got the call. I got the promotion. I genuinely didn't know how to tell you first.",
    },
    "🧊 Negotiation standoff": {
        "agent_a_name": "Victor", "agent_a_personality": "average",
        "agent_a_persona": "You are Victor, a business development manager. You are negotiating contract terms with a supplier who is pushing back hard. You need this deal but you can't go above your budget.",
        "agent_a_seed": "Fear", "agent_a_seed_intensity": 0.4,
        "agent_b_name": "Elena", "agent_b_personality": "neurotic",
        "agent_b_persona": "You are Elena, a supplier account manager. You've been pushed on pricing too many times this quarter and you're exhausted. You believe your product is worth the price and you're not backing down this time.",
        "agent_b_seed": "Resentment", "agent_b_seed_intensity": 0.55,
        "opening_speaker": "A",
        "opening_message": "Elena, I appreciate your position but we simply cannot agree to that rate. There has to be some flexibility here.",
    },
}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown('<div class="page-title">🎬 Scenario Builder</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Design agents · set personas · seed emotions · run the scene</div>', unsafe_allow_html=True)

# ── Scenario selector ─────────────────────────────────────────────────────────
preset = st.selectbox("Load a preset scenario", list(PRESET_SCENARIOS.keys()), key="preset_select")
sc = PRESET_SCENARIOS[preset]

# ── Config form ───────────────────────────────────────────────────────────────
with st.expander("⚙️ Configure agents & opening", expanded=True):
    cfg_a, cfg_b = st.columns(2)

    with cfg_a:
        st.markdown("**Agent A**")
        a_name = st.text_input("Name", value=sc["agent_a_name"], key="a_name")
        a_personality = st.selectbox("Personality", ["neurotic", "average", "resilient"],
                                     index=["neurotic","average","resilient"].index(sc["agent_a_personality"]), key="a_pers")
        a_persona = st.text_area("Persona / backstory", value=sc["agent_a_persona"], height=130, key="a_persona")
        a_seed_emotions = ["None","Joy","Anger","Fear","Distress","Shame","Pride","Guilt","Sadness","Resentment","Anticipation","Gratitude"]
        a_seed = st.selectbox("Pre-seed emotion", a_seed_emotions,
                              index=a_seed_emotions.index(sc["agent_a_seed"]) if sc["agent_a_seed"] in a_seed_emotions else 0,
                              key="a_seed")
        a_seed_int = st.slider("Seed intensity", 0.1, 1.0,
                               sc["agent_a_seed_intensity"] if sc["agent_a_seed_intensity"] > 0 else 0.5,
                               0.05, key="a_seed_int", disabled=(a_seed == "None"))
        _rx_ref = f"resilient · {REACTIVITY['resilient']}  ·  average · {REACTIVITY['average']}  ·  neurotic · {REACTIVITY['neurotic']}"
        a_reactivity = st.slider("Reactivity", 0.3, 2.0,
                                 REACTIVITY.get(a_personality, 1.0), 0.05, key="a_reactivity",
                                 help="Scales emotional spike magnitude. 1.0 = baseline.")
        st.caption(_rx_ref)

    with cfg_b:
        st.markdown("**Agent B**")
        b_name = st.text_input("Name", value=sc["agent_b_name"], key="b_name")
        b_personality = st.selectbox("Personality", ["neurotic", "average", "resilient"],
                                     index=["neurotic","average","resilient"].index(sc["agent_b_personality"]), key="b_pers")
        b_persona = st.text_area("Persona / backstory", value=sc["agent_b_persona"], height=130, key="b_persona")
        b_seed_emotions = ["None","Joy","Anger","Fear","Distress","Shame","Pride","Guilt","Sadness","Resentment","Anticipation","Gratitude"]
        b_seed = st.selectbox("Pre-seed emotion", b_seed_emotions,
                              index=b_seed_emotions.index(sc["agent_b_seed"]) if sc["agent_b_seed"] in b_seed_emotions else 0,
                              key="b_seed")
        b_seed_int = st.slider("Seed intensity", 0.1, 1.0,
                               sc["agent_b_seed_intensity"] if sc["agent_b_seed_intensity"] > 0 else 0.5,
                               0.05, key="b_seed_int", disabled=(b_seed == "None"))
        b_reactivity = st.slider("Reactivity", 0.3, 2.0,
                                 REACTIVITY.get(b_personality, 1.0), 0.05, key="b_reactivity",
                                 help="Scales emotional spike magnitude. 1.0 = baseline.")
        st.caption(_rx_ref)

    st.markdown("**Opening message**")
    opener_who = st.radio("Who speaks first?", ["A", "B"],
                          index=0 if sc["opening_speaker"] == "A" else 1,
                          horizontal=True, key="opener_who")
    opening_msg = st.text_area("Opening line", value=sc["opening_message"], height=80, key="opening_msg")

# ── Init / Reset ──────────────────────────────────────────────────────────────
def build_agents():
    agent_a = Agent(a_name, a_personality, a_persona, reactivity=a_reactivity)
    agent_b = Agent(b_name, b_personality, b_persona, reactivity=b_reactivity)
    if a_seed != "None":
        agent_a.entity.emotions[a_seed].activate(a_seed_int)
    if b_seed != "None":
        agent_b.entity.emotions[b_seed].activate(b_seed_int)
    return agent_a, agent_b

if "sc_agent_a" not in st.session_state:
    st.session_state.sc_agent_a, st.session_state.sc_agent_b = build_agents()
    st.session_state.sc_messages = []
    st.session_state.sc_turn = 0
    st.session_state.sc_next_msg = opening_msg
    st.session_state.sc_next_is_b = (opener_who == "A")  # B responds to A's opener

# ── Run controls ──────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3, ctrl4 = st.columns([1, 1, 1, 2])

with ctrl1:
    if st.button("↺ Reset scene", use_container_width=True):
        st.session_state.sc_agent_a, st.session_state.sc_agent_b = build_agents()
        st.session_state.sc_messages = []
        st.session_state.sc_turn = 0
        st.session_state.sc_next_msg = opening_msg
        st.session_state.sc_next_is_b = (opener_who == "A")
        st.rerun()

with ctrl2:
    if st.button("▶ Next Turn", use_container_width=True, type="primary"):
        if not os.environ.get("GROQ_API_KEY"):
            st.error("GROQ_API_KEY not set")
        else:
            responder = st.session_state.sc_agent_b if st.session_state.sc_next_is_b else st.session_state.sc_agent_a
            sender    = st.session_state.sc_agent_a if st.session_state.sc_next_is_b else st.session_state.sc_agent_b
            with st.spinner(""):
                reply = responder.receive_and_respond(st.session_state.sc_next_msg, witness_event=sender.last_event or None)
            st.session_state.sc_turn += 1
            st.session_state.sc_messages.append({
                "turn": st.session_state.sc_turn,
                "speaker": "B" if st.session_state.sc_next_is_b else "A",
                "name": responder.name,
                "text": reply,
                "event": responder.last_event,
            })
            st.session_state.sc_next_msg = reply
            st.session_state.sc_next_is_b = not st.session_state.sc_next_is_b
            st.rerun()

with ctrl3:
    turns_to_run = st.number_input("Auto-run turns", min_value=2, max_value=20, value=6, key="auto_turns", label_visibility="collapsed")

with ctrl4:
    if st.button(f"⏩ Run {int(turns_to_run)} turns", use_container_width=True):
        if not os.environ.get("GROQ_API_KEY"):
            st.error("GROQ_API_KEY not set")
        else:
            progress = st.progress(0, text="Running…")
            for i in range(int(turns_to_run)):
                responder = st.session_state.sc_agent_b if st.session_state.sc_next_is_b else st.session_state.sc_agent_a
                sender    = st.session_state.sc_agent_a if st.session_state.sc_next_is_b else st.session_state.sc_agent_b
                reply = responder.receive_and_respond(st.session_state.sc_next_msg, witness_event=sender.last_event or None)
                st.session_state.sc_turn += 1
                st.session_state.sc_messages.append({
                    "turn": st.session_state.sc_turn,
                    "speaker": "B" if st.session_state.sc_next_is_b else "A",
                    "name": responder.name,
                    "text": reply,
                    "event": responder.last_event,
                })
                st.session_state.sc_next_msg = reply
                st.session_state.sc_next_is_b = not st.session_state.sc_next_is_b
                progress.progress((i + 1) / int(turns_to_run), text=f"Turn {st.session_state.sc_turn}…")
                time.sleep(0.05)
            progress.empty()
            st.rerun()

# ── Scene display ─────────────────────────────────────────────────────────────
scene_col, side_col = st.columns([3, 1])

with scene_col:
    st.markdown(
        f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.5rem;">'
        f'<span style="font-family:\'Fira Code\',monospace;font-size:0.68rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em;">Scene</span>'
        f'<span style="font-family:\'Fira Code\',monospace;font-size:0.68rem;color:#94a3b8;background:#f1f5f9;padding:2px 10px;border-radius:99px;border:1px solid #e2e8f0;">Turn {st.session_state.sc_turn}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Opening
    opener_name = a_name if opener_who == "A" else b_name
    bubble_cls = "bubble-a" if opener_who == "A" else "bubble-b"
    align = "flex-start" if opener_who == "A" else "flex-end"
    st.markdown(
        f'<div style="display:flex;flex-direction:column;align-items:{align};margin-bottom:8px;">'
        f'<div class="{bubble_cls}">{opening_msg}</div>'
        f'<div class="meta">{opener_name} · opening</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    if not st.session_state.sc_messages:
        st.markdown('<div style="color:#94a3b8;font-size:0.82rem;padding:0.5rem 0;">Press Next Turn to continue the scene.</div>', unsafe_allow_html=True)

    for msg in st.session_state.sc_messages:
        is_a = msg["speaker"] == "A"
        bubble_cls = "bubble-a" if is_a else "bubble-b"
        align = "flex-start" if is_a else "flex-end"

        ev = msg.get("event", {})
        et = ev.get("event_type", "neutral")
        sev = ev.get("severity", 0.0)
        color = EVENT_COLORS.get(et, "#94a3b8")
        flags = []
        if ev.get("directed_at_self"): flags.append("→self")
        if ev.get("intentional"): flags.append("intentional")
        flag_str = (" · " + " · ".join(flags)) if flags else ""
        event_html = (
            f'<span class="event-badge">'
            f'<span class="event-dot" style="background:{color};"></span>'
            f'{et} · {sev:.2f}{flag_str}'
            f'</span>'
        )

        st.markdown(
            f'<div style="display:flex;flex-direction:column;align-items:{align};margin-bottom:8px;">'
            f'<div class="{bubble_cls}">{msg["text"]}</div>'
            f'<div class="meta">{msg["name"]} · turn {msg["turn"]} &nbsp; {event_html}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Custom inject
    with st.form("inject_form", clear_on_submit=True):
        inj_col1, inj_col2 = st.columns([4, 1])
        with inj_col1:
            inject_msg = st.text_input("Inject a message", placeholder="Force a specific line into the conversation…", label_visibility="collapsed")
        with inj_col2:
            inj_submitted = st.form_submit_button("Inject", use_container_width=True)
    if inj_submitted and inject_msg.strip():
        st.session_state.sc_next_msg = inject_msg.strip()
        st.rerun()

with side_col:
    # Agent A emotions
    agent_a: Agent = st.session_state.sc_agent_a
    agent_b: Agent = st.session_state.sc_agent_b

    badge_a = f"badge-{a_personality}"
    st.markdown(
        f'<div class="card" style="margin-bottom:0.8rem;">'
        f'<div style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;color:#1e293b;margin-bottom:3px;">{a_name}</div>'
        f'<span class="personality-badge {badge_a}">{a_personality}</span>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-label">Emotions</div>', unsafe_allow_html=True)
    active_a = agent_a.entity.get_active_emotions()
    if not active_a:
        st.markdown('<div style="color:#94a3b8;font-size:0.75rem;font-style:italic;">calm</div>', unsafe_allow_html=True)
    else:
        bars = "".join(
            f'<div class="emotion-row"><span class="emotion-name">{n}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{int(i*100)}%;background:{EMOTION_COLORS.get(n,"#94a3b8")};"></div></div>'
            f'<span class="emotion-pct">{int(i*100)}%</span></div>'
            for n, i in active_a[:6]
        )
        st.markdown(bars, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    badge_b = f"badge-{b_personality}"
    st.markdown(
        f'<div class="card">'
        f'<div style="font-family:\'Playfair Display\',serif;font-size:1rem;font-weight:700;color:#1e293b;margin-bottom:3px;">{b_name}</div>'
        f'<span class="personality-badge {badge_b}">{b_personality}</span>',
        unsafe_allow_html=True
    )
    st.markdown('<div class="section-label">Emotions</div>', unsafe_allow_html=True)
    active_b = agent_b.entity.get_active_emotions()
    if not active_b:
        st.markdown('<div style="color:#94a3b8;font-size:0.75rem;font-style:italic;">calm</div>', unsafe_allow_html=True)
    else:
        bars = "".join(
            f'<div class="emotion-row"><span class="emotion-name">{n}</span>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{int(i*100)}%;background:{EMOTION_COLORS.get(n,"#94a3b8")};"></div></div>'
            f'<span class="emotion-pct">{int(i*100)}%</span></div>'
            for n, i in active_b[:6]
        )
        st.markdown(bars, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

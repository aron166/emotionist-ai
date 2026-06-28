import { useEffect, useRef, useState } from "react";
import { api } from "../api.js";
import EmotionBars from "../components/EmotionBars.jsx";
import ParamChips from "../components/ParamChips.jsx";
import EventBadge from "../components/EventBadge.jsx";

const DEFAULT_PERSONA = "You are Morgan, a thoughtful person having a conversation.";

export default function Chat() {
  const [state, setState] = useState(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");
  const [spOpen, setSpOpen] = useState(false);

  // custom-agent config (advanced)
  const [cfg, setCfg] = useState({
    name: "Morgan", personality: "average", reactivity: 1.0,
    persona: DEFAULT_PERSONA, seed: "None", seedInt: 0.5,
  });

  const chatRef = useRef(null);
  useEffect(() => { api("/api/chat/state").then(setState); }, []);
  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [state, busy]);

  function customBody() {
    return {
      scenario_id: null,
      name: cfg.name || "Morgan",
      personality: cfg.personality,
      reactivity: parseFloat(cfg.reactivity),
      persona: cfg.persona,
      seed_emotion: cfg.seed && cfg.seed !== "None" ? cfg.seed : null,
      seed_intensity: parseFloat(cfg.seedInt),
    };
  }

  // One reset that respects the active mode (scenario preset vs custom).
  async function resetAgent({ scenario_id, custom }) {
    if (busy || !state) return;
    setBusy(true);
    try {
      const body = { model_id: state.model_id };
      if (scenario_id) body.scenario_id = scenario_id;
      else if (custom) Object.assign(body, customBody());
      else if (state.scenario_id) body.scenario_id = state.scenario_id;
      else Object.assign(body, customBody());
      const s = await api("/api/chat/reset", body);
      if (s.error) { alert(s.error); return; }
      setState(s);
    } catch (e) { alert("Request failed: " + e); }
    finally { setBusy(false); }
  }

  async function changeModel(model_id) {
    if (busy || !state) return;
    setBusy(true);
    try {
      const body = { model_id };
      if (state.scenario_id) body.scenario_id = state.scenario_id;
      else Object.assign(body, customBody());
      const s = await api("/api/chat/reset", body);
      if (s.error) { alert(s.error); return; }
      setState(s);
    } catch (e) { alert("Request failed: " + e); }
    finally { setBusy(false); }
  }

  async function setLanguage(lang) {
    if (busy || !state || state.language === lang) return;
    setBusy(true);
    try {
      const s = await api("/api/chat/language", { language: lang });
      if (s.error) { alert(s.error); return; }
      setState(s);
    } catch (e) { alert("Request failed: " + e); }
    finally { setBusy(false); }
  }

  async function sendMessage() {
    const v = msg.trim();
    if (!v || busy) return;
    setMsg(""); setBusy(true);
    try {
      const s = await api("/api/chat/send", { message: v });
      if (s.error) { alert(s.error); return; }
      setState(s);
    } catch (e) { alert("Request failed: " + e); }
    finally { setBusy(false); }
  }

  if (!state) return <section className="stage chat-stage"><div className="empty">Loading…</div></section>;

  const a = state.agent;
  const rx = state.reactivity_ref;
  const md = state.models.find((m) => m.id === state.model_id);

  return (
    <section className="stage chat-stage">
      {/* Config */}
      <aside className="panel">
        <div className="micro-label">Practice Scenario</div>
        <div className="scenario-cards">
          {state.scenarios.map((s) => (
            <button key={s.id} type="button" disabled={busy}
              className={"scn-card" + (state.scenario_id === s.id ? " active" : "")}
              onClick={() => resetAgent({ scenario_id: s.id })}>
              <span className="scn-cat">{s.category.replace(/_/g, " ")}</span>
              <span className="scn-name">{s.display_name}</span>
              <span className="scn-sit">{s.situation}</span>
            </button>
          ))}
          <button type="button" disabled={busy}
            className={"scn-card scn-custom" + (!state.scenario_id ? " active" : "")}
            onClick={() => resetAgent({ custom: true })}>
            <span className="scn-cat">custom</span>
            <span className="scn-name">Custom agent</span>
            <span className="scn-sit">Build your own counterpart below.</span>
          </button>
        </div>

        <div className="micro-label">Model</div>
        <label className="field"><span className="micro">LLM backend</span>
          <select value={state.model_id} disabled={busy} onChange={(e) => changeModel(e.target.value)}>
            {state.models.map((m) => (
              <option key={m.id} value={m.id} disabled={!m.available}>
                {m.available ? m.label : `${m.label} (no key)`}
              </option>
            ))}
          </select>
          <span className="hint">{md ? md.note : ""}</span>
        </label>

        <div className="micro-label">Response Language</div>
        <div className="lang-toggle">
          <button type="button" disabled={busy}
            className={"lang-btn" + (state.language === "hu" ? " active" : "")}
            onClick={() => setLanguage("hu")}>Magyar</button>
          <button type="button" disabled={busy}
            className={"lang-btn" + (state.language === "en" ? " active" : "")}
            onClick={() => setLanguage("en")}>English</button>
        </div>
        <span className="hint">Switches mid-conversation — use English to show the local model at its best.</span>

        <div className="micro-label">Custom Agent <span className="micro" style={{ opacity: 0.6 }}>(advanced)</span></div>
        <label className="field"><span className="micro">Name</span>
          <input type="text" value={cfg.name} autoComplete="off"
                 onChange={(e) => setCfg({ ...cfg, name: e.target.value })} />
        </label>
        <label className="field"><span className="micro">Personality</span>
          <select value={cfg.personality} onChange={(e) => setCfg({ ...cfg, personality: e.target.value })}>
            {state.personalities.map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </label>
        <label className="field"><span className="micro">Reactivity <em>{parseFloat(cfg.reactivity).toFixed(2)}</em></span>
          <input type="range" min="0.3" max="2.0" step="0.05" value={cfg.reactivity}
                 onChange={(e) => setCfg({ ...cfg, reactivity: e.target.value })} />
          <span className="hint">resilient {rx.resilient} · average {rx.average} · neurotic {rx.neurotic}</span>
        </label>
        <label className="field"><span className="micro">Persona</span>
          <textarea rows="3" value={cfg.persona} onChange={(e) => setCfg({ ...cfg, persona: e.target.value })} />
        </label>

        <div className="micro-label">Pre-seed Emotion</div>
        <div className="seed-row">
          <select value={cfg.seed} onChange={(e) => setCfg({ ...cfg, seed: e.target.value })}>
            <option value="None">None</option>
            {state.seed_options.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>
          <input type="range" min="0.1" max="1.0" step="0.05" value={cfg.seedInt}
                 onChange={(e) => setCfg({ ...cfg, seedInt: e.target.value })} />
        </div>

        <button className="btn btn-primary apply-btn" disabled={busy}
                onClick={() => resetAgent({ custom: true })}>Apply Custom Agent</button>
      </aside>

      {/* Conversation */}
      <div className="conv">
        <div className="conv-head">
          <span className="micro">Conversation</span>
          <span className="pill">{a.name}</span>
        </div>
        <div className="chat" ref={chatRef}>
          {(!state.messages || !state.messages.length) && !busy ? (
            <div className="empty">Start the conversation — say the first thing you'd say to them.</div>
          ) : (
            state.messages.map((m, i) =>
              m.role === "user" ? (
                <div className="msg sam" key={i}>
                  <div className="bubble">{m.text}</div>
                  <div className="meta">You</div>
                </div>
              ) : (
                <div className="msg alex" key={i}>
                  <div className="bubble">{m.text}</div>
                  <div className="meta">Counterpart</div>
                  <EventBadge ev={m.event} />
                </div>
              )
            )
          )}
          {busy && (
            <div className="msg alex">
              <div className="bubble"><span className="thinking"><span></span><span></span><span></span></span></div>
              <div className="meta">Counterpart · thinking</div>
            </div>
          )}
        </div>
        <div className="inject">
          <input type="text" placeholder="Say something to the agent…" value={msg} disabled={busy}
                 autoComplete="off" onChange={(e) => setMsg(e.target.value)}
                 onKeyDown={(e) => { if (e.key === "Enter") sendMessage(); }} />
          <button className="btn btn-primary" disabled={busy} onClick={sendMessage}>Send</button>
        </div>
      </div>

      {/* Live state */}
      <aside className="panel">
        <div className="panel-head">
          <div className="agent-name">{a.name}</div>
          <span className={"badge badge-" + a.personality}>{a.personality}</span>
        </div>
        <div className="micro-label">Active Emotions</div>
        <div className="emotions"><EmotionBars emotions={a.emotions} /></div>
        <hr />
        <div className="micro-label">Behavioral Profile</div>
        <div className="params"><ParamChips params={a.params} /></div>
        <hr />
        <div className="sysprompt-head">
          <span className="micro-label" style={{ margin: 0 }}>Live System Prompt</span>
          <button className="mini-btn" onClick={() => setSpOpen(!spOpen)}>{spOpen ? "hide" : "show"}</button>
        </div>
        {spOpen && <pre className="sysprompt">{a.system_prompt}</pre>}
        <hr />
        <div className="micro-label">
          Retrieved Context (RAG) <span className="micro" style={{ opacity: 0.6 }}>
            {state.retrieval_backend ? "· " + state.retrieval_backend : ""}</span>
        </div>
        <div className="retrieved">
          {!state.retrieved || !state.retrieved.length ? (
            <div className="calm">— nothing retrieved yet —</div>
          ) : (
            state.retrieved.map((h, i) => (
              <div className="rag-row" key={i}><span className="rag-score">{h.score}</span>{h.text}</div>
            ))
          )}
        </div>
        <div className="decay">decay λ {a.decay} · reactivity {a.reactivity}</div>
      </aside>
    </section>
  );
}

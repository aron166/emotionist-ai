// ── Practice-partner chat view ──────────────────────────────────────────────
// Shared helpers come from common.js.

let busy = false;
let spOpen = false;
let selectsReady = false;

function renderMessages(messages) {
  const el = $("chat");
  if (!messages || !messages.length) {
    el.innerHTML = '<div class="empty">Start the conversation — say the first thing you\'d say to them.</div>';
    return;
  }
  el.innerHTML = messages
    .map((m) => {
      if (m.role === "user") {
        return `<div class="msg sam"><div class="bubble">${escapeHtml(m.text)}</div><div class="meta">You</div></div>`;
      }
      return `<div class="msg alex">
        <div class="bubble">${escapeHtml(m.text)}</div>
        <div class="meta">Counterpart</div>
        ${eventBadge(m.event)}
      </div>`;
    })
    .join("");
  el.scrollTop = el.scrollHeight;
}

function renderRetrieved(hits, backend) {
  $("rag-backend").textContent = backend ? `· ${backend}` : "";
  const el = $("retrieved");
  if (!hits || !hits.length) {
    el.innerHTML = '<div class="calm">— nothing retrieved yet —</div>';
    return;
  }
  el.innerHTML = hits
    .map((h) => `<div class="rag-row"><span class="rag-score">${h.score}</span>${escapeHtml(h.text)}</div>`)
    .join("");
}

function render(state) {
  const a = state.agent;

  if (!selectsReady) {
    // personality + seed selects
    const psel = $("cfg-personality");
    state.personalities.forEach((p) => psel.add(new Option(p, p)));
    const seed = $("cfg-seed");
    seed.add(new Option("None", "None"));
    state.seed_options.forEach((s) => seed.add(new Option(s, s)));

    // scenario picker (#14): "— Custom —" + presets
    const ssel = $("cfg-scenario");
    ssel.add(new Option("— Custom agent —", ""));
    state.scenarios.forEach((s) => ssel.add(new Option(s.display_name, s.id)));

    // model picker (#45): disable unavailable (Groq w/o key)
    const msel = $("cfg-model");
    state.models.forEach((m) => {
      const opt = new Option(m.available ? m.label : `${m.label} (no key)`, m.id);
      opt.disabled = !m.available;
      msel.add(opt);
    });
    selectsReady = true;
  }

  // reflect current backend state into the selects
  $("cfg-scenario").value = state.scenario_id || "";
  $("cfg-model").value = state.model_id;
  const sc = state.scenarios.find((s) => s.id === state.scenario_id);
  $("cfg-scenario-sit").textContent = sc ? sc.situation : "Build your own counterpart below.";
  const md = state.models.find((m) => m.id === state.model_id);
  $("cfg-model-note").textContent = md ? md.note : "";

  $("cfg-rx-ref").textContent =
    `resilient ${state.reactivity_ref.resilient} · average ${state.reactivity_ref.average} · neurotic ${state.reactivity_ref.neurotic}`;

  // live state panel
  $("agent-pill").textContent = a.name;
  $("state-name").textContent = a.name;
  const badge = $("state-badge");
  badge.textContent = a.personality;
  badge.className = "badge badge-" + a.personality;
  renderEmotions($("emo"), a.emotions);
  renderParams($("par"), a.params);
  $("decay").textContent = `decay λ ${a.decay} · reactivity ${a.reactivity}`;
  $("sysprompt").textContent = a.system_prompt;
  renderRetrieved(state.retrieved, state.retrieval_backend);

  renderMessages(state.messages);
}

function setBusy(on) {
  busy = on;
  document.body.classList.toggle("busy", on);
  ["send", "apply", "cfg-scenario", "cfg-model"].forEach((id) => ($(id).disabled = on));
  if (on) {
    const chat = $("chat");
    const node = document.createElement("div");
    node.className = "msg alex";
    node.id = "thinking-node";
    node.innerHTML = `<div class="bubble"><span class="thinking"><span></span><span></span><span></span></span></div><div class="meta">Counterpart · thinking</div>`;
    chat.appendChild(node);
    chat.scrollTop = chat.scrollHeight;
  } else {
    const t = document.getElementById("thinking-node");
    if (t) t.remove();
  }
}

// ── Actions ─────────────────────────────────────────────────────────────────
// One reset call that respects whichever mode is active: a scenario id (preset)
// or the custom fields. `model_id` always comes from the model picker.
async function resetAgent({ scenario_id, custom }) {
  if (busy) return;
  setBusy(true);
  try {
    const body = { model_id: $("cfg-model").value };
    if (scenario_id) {
      body.scenario_id = scenario_id;
    } else if (custom) {
      const seed = $("cfg-seed").value;
      Object.assign(body, {
        scenario_id: null,
        name: $("cfg-name").value || "Morgan",
        personality: $("cfg-personality").value,
        reactivity: parseFloat($("cfg-rx").value),
        persona: $("cfg-persona").value,
        seed_emotion: seed && seed !== "None" ? seed : null,
        seed_intensity: parseFloat($("cfg-seed-int").value),
      });
    } else {
      // model-only change: keep current scenario (or custom) as the server has it
      const cur = $("cfg-scenario").value;
      if (cur) body.scenario_id = cur;
      else {
        const seed = $("cfg-seed").value;
        Object.assign(body, {
          name: $("cfg-name").value || "Morgan",
          personality: $("cfg-personality").value,
          reactivity: parseFloat($("cfg-rx").value),
          persona: $("cfg-persona").value,
          seed_emotion: seed && seed !== "None" ? seed : null,
          seed_intensity: parseFloat($("cfg-seed-int").value),
        });
      }
    }
    const state = await api("/api/chat/reset", body);
    if (state.error) { alert(state.error); return; }
    render(state);
  } catch (e) {
    alert("Request failed: " + e);
  } finally {
    setBusy(false);
  }
}

async function sendMessage() {
  const v = $("msg").value.trim();
  if (!v || busy) return;
  $("msg").value = "";
  setBusy(true);
  try {
    const state = await api("/api/chat/send", { message: v });
    if (state.error) { alert(state.error); return; }
    render(state);
  } catch (e) {
    alert("Request failed: " + e);
  } finally {
    setBusy(false);
  }
}

// ── Wire up ───────────────────────────────────────────────────────────────────
$("apply").addEventListener("click", () => resetAgent({ custom: true }));
$("cfg-scenario").addEventListener("change", (e) => resetAgent({ scenario_id: e.target.value || null }));
$("cfg-model").addEventListener("change", () => resetAgent({}));
$("send").addEventListener("click", sendMessage);
$("msg").addEventListener("keydown", (e) => { if (e.key === "Enter") sendMessage(); });
$("cfg-rx").addEventListener("input", (e) => { $("cfg-rx-val").textContent = parseFloat(e.target.value).toFixed(2); });
$("sp-toggle").addEventListener("click", () => {
  spOpen = !spOpen;
  $("sysprompt").hidden = !spOpen;
  $("sp-toggle").textContent = spOpen ? "hide" : "show";
});

// ── Boot ──────────────────────────────────────────────────────────────────────
(async () => {
  const state = await api("/api/chat/state");
  render(state);
})();

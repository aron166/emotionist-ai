// ── Single-agent chat view ──────────────────────────────────────────────────
// Shared helpers come from common.js.

let busy = false;
let spOpen = false;

function renderMessages(messages) {
  const el = $("chat");
  if (!messages || !messages.length) {
    el.innerHTML = '<div class="empty">Say something to start the conversation.</div>';
    return;
  }
  el.innerHTML = messages
    .map((m) => {
      if (m.role === "user") {
        return `<div class="msg sam"><div class="bubble">${escapeHtml(m.text)}</div><div class="meta">You</div></div>`;
      }
      return `<div class="msg alex">
        <div class="bubble">${escapeHtml(m.text)}</div>
        <div class="meta">Agent</div>
        ${eventBadge(m.event)}
      </div>`;
    })
    .join("");
  el.scrollTop = el.scrollHeight;
}

function render(state) {
  const a = state.agent;

  // populate selects once
  const psel = $("cfg-personality");
  if (psel.options.length === 0) {
    state.personalities.forEach((p) => psel.add(new Option(p, p)));
    const seed = $("cfg-seed");
    seed.add(new Option("None", "None"));
    state.seed_options.forEach((s) => seed.add(new Option(s, s)));
  }
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

  renderMessages(state.messages);
}

function setBusy(on) {
  busy = on;
  document.body.classList.toggle("busy", on);
  ["send", "apply"].forEach((id) => ($(id).disabled = on));
  if (on) {
    const chat = $("chat");
    const node = document.createElement("div");
    node.className = "msg alex";
    node.innerHTML = `<div class="bubble"><span class="thinking"><span></span><span></span><span></span></span></div><div class="meta">Agent · thinking</div>`;
    chat.appendChild(node);
    chat.scrollTop = chat.scrollHeight;
  }
}

// ── Actions ─────────────────────────────────────────────────────────────────
async function applyConfig() {
  if (busy) return;
  setBusy(true);
  const state = await api("/api/chat/reset", {
    name: $("cfg-name").value || "Morgan",
    personality: $("cfg-personality").value,
    reactivity: parseFloat($("cfg-rx").value),
    persona: $("cfg-persona").value,
    seed_emotion: $("cfg-seed").value,
    seed_intensity: parseFloat($("cfg-seed-int").value),
  });
  render(state);
  setBusy(false);
}

async function sendMessage() {
  const v = $("msg").value.trim();
  if (!v || busy) return;
  $("msg").value = "";
  setBusy(true);
  const state = await api("/api/chat/send", { message: v });
  render(state);
  setBusy(false);
  if (state.error) alert(state.error);
}

// ── Wire up ───────────────────────────────────────────────────────────────────
$("apply").addEventListener("click", applyConfig);
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

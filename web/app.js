// ── Two-agent view (Alex vs Sam) ────────────────────────────────────────────
// Shared helpers ($, api, escapeHtml, renderEmotions, renderParams, eventBadge,
// EMOTION_COLORS, EVENT_COLORS) come from common.js.

function renderChat(messages) {
  const el = $("chat");
  if (!messages || !messages.length) {
    el.innerHTML = '<div class="empty">Press <b>Next Turn</b> to start the conversation.</div>';
    return;
  }
  el.innerHTML = messages
    .map((m) => {
      const cls = m.speaker === "Alex" ? "alex" : "sam";
      return `<div class="msg ${cls}">
        <div class="bubble">${escapeHtml(m.text)}</div>
        <div class="meta">${escapeHtml(m.speaker)} · turn ${m.turn}</div>
        ${eventBadge(m.event)}
      </div>`;
    })
    .join("");
  el.scrollTop = el.scrollHeight;
}

function render(state) {
  const sel = $("topic");
  if (sel.options.length === 0) {
    state.topics.forEach((t) => {
      const o = document.createElement("option");
      o.value = t; o.textContent = t;
      sel.appendChild(o);
    });
  }
  sel.value = state.topic;

  $("opener").innerHTML = `<b>${escapeHtml(state.opening.speaker)}</b> · opening — “${escapeHtml(state.opening.text)}”`;
  $("turnpill").textContent = "Turn " + state.turn;

  renderEmotions($("emo-alex"), state.alex.emotions);
  renderEmotions($("emo-sam"), state.sam.emotions);
  renderParams($("par-alex"), state.alex.params);
  renderParams($("par-sam"), state.sam.params);
  $("decay-alex").textContent = `decay λ ${state.alex.decay} · emotions linger long`;
  $("decay-sam").textContent = `decay λ ${state.sam.decay} · emotions fade quickly`;

  renderChat(state.messages);
}

// ── Busy / loading ────────────────────────────────────────────────────────────
let busy = false;
function setBusy(on, thinkingFor) {
  busy = on;
  document.body.classList.toggle("busy", on);
  ["reset", "next", "run6", "send"].forEach((id) => ($(id).disabled = on));
  if (on && thinkingFor) {
    const cls = thinkingFor === "Sam" ? "sam" : "alex";
    const chat = $("chat");
    const node = document.createElement("div");
    node.className = "msg " + cls;
    node.id = "thinking-node";
    node.innerHTML = `<div class="bubble"><span class="thinking"><span></span><span></span><span></span></span></div><div class="meta">${escapeHtml(thinkingFor)} · thinking</div>`;
    chat.appendChild(node);
    chat.scrollTop = chat.scrollHeight;
  } else if (!on) {
    const t = document.getElementById("thinking-node");
    if (t) t.remove();
  }
}

// ── Actions ─────────────────────────────────────────────────────────────────
async function doReset() {
  if (busy) return;
  setBusy(true);
  const state = await api("/api/reset", { topic: $("topic").value });
  window.__state = state;
  render(state);
  setBusy(false);
}

async function doTurn(message) {
  if (busy) return false;
  const cur = window.__state;
  setBusy(true, cur ? cur.next_speaker : null);
  try {
    const state = await api("/api/turn", { message: message || null });
    if (state.error) { alert(state.error); return false; }
    window.__state = state;
    render(state);
    return true;
  } catch (e) {
    alert("Request failed: " + e);
    return false;
  } finally {
    setBusy(false);
  }
}

async function doRun(n) {
  if (busy) return;
  for (let i = 0; i < n; i++) {
    const ok = await doTurn();
    if (!ok) break;  // stop the batch if a turn fails
  }
}

// ── Wire up ───────────────────────────────────────────────────────────────────
$("reset").addEventListener("click", doReset);
$("next").addEventListener("click", () => doTurn());
$("run6").addEventListener("click", () => doRun(6));
$("send").addEventListener("click", () => {
  const v = $("inject").value.trim();
  if (v) { $("inject").value = ""; doTurn(v); }
});
$("inject").addEventListener("keydown", (e) => { if (e.key === "Enter") $("send").click(); });
$("topic").addEventListener("change", doReset);

// ── Boot ──────────────────────────────────────────────────────────────────────
(async () => {
  const state = await api("/api/state");
  window.__state = state;
  render(state);
})();

import { EVENT_COLORS } from "../api.js";

export default function EventBadge({ ev }) {
  if (!ev || !ev.event_type) return null;
  const color = EVENT_COLORS[ev.event_type] || "#94a3b8";
  const flags = [];
  if (ev.directed_at_self) flags.push("self");
  if (ev.intentional) flags.push("intentional");
  const flagStr = flags.length ? " · " + flags.join(" · ") : "";
  const sev = (ev.severity ?? 0).toFixed(2);
  return (
    <span className="ev">
      <span className="ev-dot" style={{ background: color }} />
      {ev.event_type} · sev {sev}{flagStr}
    </span>
  );
}

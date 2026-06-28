// Shared API client + color maps (ported from web/common.js).

export async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

export const EMOTION_COLORS = {
  Joy: "#f59e0b", Hope: "#10b981", Satisfaction: "#84cc16", Relief: "#06b6d4",
  HappyFor: "#f97316", Pride: "#d97706", Admiration: "#0891b2", Love: "#ec4899",
  Gratification: "#f59e0b", Gratitude: "#059669", Trust: "#14b8a6", Surprise: "#a78bfa",
  Anticipation: "#8b5cf6", Distress: "#ef4444", Fear: "#6366f1", FearsConfirmed: "#dc2626",
  Disappointment: "#8b5cf6", Pity: "#94a3b8", Gloating: "#a16207", Resentment: "#b91c1c",
  Shame: "#7c3aed", Reproach: "#9f1239", Hate: "#94a3b8", Remorse: "#6d28d9",
  Anger: "#dc2626", Sadness: "#64748b", Disgust: "#a8a29e", Envy: "#4d7c0f",
  Guilt: "#64748b", Contempt: "#818cf8",
};

export const EVENT_COLORS = {
  compliment: "#10b981", achievement: "#f59e0b", good_news: "#84cc16",
  agreement: "#06b6d4", praise_of_other: "#0891b2", insult: "#dc2626",
  threat: "#6366f1", bad_news: "#ef4444", failure: "#7c3aed",
  disagreement: "#f97316", blame_of_other: "#b91c1c", neutral: "#94a3b8",
};

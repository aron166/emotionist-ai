#!/usr/bin/env bash
# Expose the running app via an ephemeral cloudflared quick-tunnel (#35).
# Start the app first (./run.sh in another terminal), then run this.
set -euo pipefail
PORT="${PORT:-8000}"

command -v cloudflared >/dev/null || {
  echo "✗ cloudflared not installed. Get it: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/" >&2
  exit 1
}

curl -fsS "http://127.0.0.1:$PORT/api/chat/state" >/dev/null 2>&1 || {
  echo "✗ App not responding on http://127.0.0.1:$PORT — start it first: ./run.sh" >&2
  exit 1
}

echo "▸ Opening public tunnel to http://127.0.0.1:$PORT (Ctrl-C to stop)…"
exec cloudflared tunnel --url "http://127.0.0.1:$PORT"

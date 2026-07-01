#!/usr/bin/env bash
# One command: clone -> running app. (#16: #17 venv+deps+start, #18 preflight, #19 ollama bootstrap)
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-8000}"
PY="${PYTHON:-python3}"

say()  { printf '\033[1;35m> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31mx %s\033[0m\n' "$*" >&2; exit 1; }

# -- Preflight (#18) -----------------------------------------------------------
command -v "$PY" >/dev/null || die "Python 3 not found. Install Python 3.10+ and retry."
"$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' \
  || die "Python 3.10+ required (found $($PY -V))."

# Port free? (best-effort: skip the check if no probe tool exists)
if command -v ss >/dev/null && ss -ltn "sport = :$PORT" 2>/dev/null | grep -q LISTEN; then
  die "Port $PORT is busy. Set PORT=<other> ./run.sh"
fi

# -- venv + deps (#17) ---------------------------------------------------------
[ -d .venv ] || { say "Creating .venv"; "$PY" -m venv .venv; }
# shellcheck disable=SC1091
source .venv/bin/activate
say "Installing dependencies"
pip install -q -r requirements.txt

# -- Frontend build (#44) ------------------------------------------------------
# Build the React app so server.py serves web-dist/. If Node is absent or the
# build fails, the server falls back to the legacy web/ frontend - demo still runs.
if [ -d frontend ] && command -v npm >/dev/null; then
  if [ ! -d web-dist ] || [ "${REBUILD:-0}" = "1" ] || [ ! -d frontend/node_modules ]; then
    say "Building frontend (React)"
    [ -d frontend/node_modules ] || (cd frontend && npm install)
    (cd frontend && npm run build) || warn "Frontend build failed - falling back to legacy web/ UI."
  fi
elif [ ! -d web-dist ]; then
  warn "Node/npm not found - serving the legacy web/ UI (React build skipped)."
fi

# -- Provider config (#18) -----------------------------------------------------
[ -f .env ] || { warn ".env missing - copying .env.example (edit it to add a key/model)"; cp .env.example .env; }
PROVIDER="$(grep -E '^LLM_PROVIDER=' .env | tail -1 | cut -d= -f2 | tr -d ' \r' || true)"
PROVIDER="${PROVIDER:-groq}"

if [ "$PROVIDER" = "groq" ]; then
  grep -qE '^GROQ_API_KEY=.+' .env && ! grep -qE '^GROQ_API_KEY=your_key_here' .env \
    || warn "LLM_PROVIDER=groq but GROQ_API_KEY looks unset in .env. Cloud models will be disabled; local models still work if Ollama is up."
fi

# -- Ollama bootstrap (#19, opt-in) --------------------------------------------
if [ "$PROVIDER" = "ollama" ]; then
  command -v ollama >/dev/null || die "LLM_PROVIDER=ollama but 'ollama' isn't installed. See https://ollama.com"
  MODEL="$(grep -E '^OLLAMA_MODEL=' .env | tail -1 | cut -d= -f2 | tr -d ' \r' || true)"
  MODEL="${MODEL:-qwen2.5:3b}"
  if ! ollama list 2>/dev/null | grep -q "$MODEL"; then
    warn "Ollama model '$MODEL' not pulled."
    read -r -p "Pull it now (~2GB)? [y/N] " ans
    [ "${ans:-N}" = "y" ] && ollama pull "$MODEL" || warn "Skipped - pull it later with: ollama pull $MODEL"
  fi
fi

# -- Start ---------------------------------------------------------------------
say "Starting Emotionist.ai -> http://127.0.0.1:$PORT"
exec uvicorn server:app --host "${HOST:-127.0.0.1}" --port "$PORT"

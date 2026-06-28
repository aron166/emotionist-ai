# Go-live runbook (#39)

Checklist to put the demo live from your laptop. Follow top to bottom.

## Local-only demo (in-house, default)

1. **Start it:** `./run.sh` → http://127.0.0.1:8000
2. Open **/chat**, pick a scenario (e.g. *Dühös ügyfél*), pick a model.
3. Sanity: send one message, confirm a reply + emotion bars move.

## Live demo over a tunnel (interviewer hits your URL)

Pre-warm everything **before** they're watching — first Ollama call is slow (~40s cold).

1. **Pick the backend for visitors (#37):**
   - Offline/free: in `.env` set `LLM_PROVIDER=ollama`, then `ollama serve` and pre-pull: `ollama pull qwen2.5:3b`.
   - Cloud HU quality: leave `LLM_PROVIDER=groq` with a valid `GROQ_API_KEY`.
   - Either way, visitors can switch models in the UI dropdown — your machine serves them all.
2. **Start the app:** `./run.sh`
3. **Pre-warm the model:** in /chat, send one throwaway message and wait for the reply.
4. **Open the tunnel (new terminal):** `./tunnel.sh` → copy the printed `https://….trycloudflare.com` URL.
5. **Share the URL.** It maps to your local app + local model.

## Safety while exposed (#36, #38)

- App binds `127.0.0.1`; only cloudflared reaches in. No secrets are sent to the browser (the API exposes only a `has_key` boolean, never the key).
- Mutating calls are rate-limited to `RATE_LIMIT_PER_MIN` (default 30/min/IP). Tune via env if needed.
- **Shared state caveat:** this is a single-session demo — all tunnel visitors share the *same* agent/conversation. Fine for a guided demo; don't hand the URL to a crowd.

## If something breaks

| Symptom | Fix |
|---|---|
| Port busy | `PORT=8001 ./run.sh` (and `PORT=8001 ./tunnel.sh`) |
| Groq model greyed out | `GROQ_API_KEY` missing/invalid in `.env` → use a local model |
| Local model errors | `ollama serve` not running, or model not pulled (`ollama pull qwen2.5:3b`) |
| Hungarian looks broken | switch to **Groq Llama 3.3 70B** in the model dropdown |
| Tunnel won't start | app not running, or `cloudflared` not installed |

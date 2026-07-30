# AquaShield — Grounded water-risk decisions with Gemma 4

Built for the Gemma 4 Hackathon Sprint (GDG VIT Chennai). Track: **AI Shield**.

## What this is
A guardrail framework for Gemma 4: drop a pin on a map, get a water-risk
explanation and a standards-cited recommendation — where every claim is
either traced to real satellite data / a real standards document, or
explicitly marked "not available." Nothing is invented.

## Read these in order before writing any code
1. `docs/MVP_SCOPE.md` — what we're building and what we're explicitly not
2. `docs/BLUEPRINT.md` — architecture, API contracts, and who owns what
3. `docs/AI_AGENT_RULES.md` — binding rules for any AI coding agent working in this repo
4. `docs/SUBMISSION_GUIDE.md` — exactly how to satisfy the Kaggle Writeup / repo / demo requirements

## Quickstart
```bash
cp .env.example .env   # fill in keys
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

cd frontend && npm install
npm run dev
```

## Team / lanes
| Dev | Owns | Branch |
|---|---|---|
| A | Earth Engine + `/api/risk` | `dev-a/gee` |
| B | Gemma 4 client + RAG | `dev-b/gemma-rag` |
| C | Guardrail verifier (core deliverable) | `dev-c/guardrail` |
| D | Frontend + integration | `dev-d/frontend` |

All PRs target `main` and must pass CI (`.github/workflows/ci.yml`) before merge.

## Model
Gemma 4, served via `GEMMA_PROVIDER` in `.env` — either local Ollama or
Google AI Studio API. Decision locked at hour 1; see `docs/BLUEPRINT.md`.

## Submission checklist (Kaggle)
- [ ] Writeup ≤1500 words, track selected: AI Shield
- [ ] Public code repo linked, well-documented
- [ ] Live demo linked (hosted or notebook), no login wall
- [ ] Demo shows: pin drop → grounded explanation → a live guardrail rejection → cited recommendation → a genuine "no data" state

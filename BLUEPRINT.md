# Technical Blueprint — AquaShield

This document is the single source of truth for architecture and task ownership.
Any AI agent working on this repo should read this file, `AI_AGENT_RULES.md`, and
`MVP_SCOPE.md` in full before writing code.

---

## 1. System architecture

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────────┐
│   Frontend   │─────▶│   FastAPI backend │─────▶│  Google Earth Engine │
│  (map + UI)  │◀─────│                   │◀─────│   (risk indicators)  │
└─────────────┘      └────────┬──────────┘      └─────────────────────┘
                               │
                     ┌─────────┴──────────┐
                     │                    │
              ┌──────▼──────┐     ┌───────▼────────┐
              │  RAG layer   │     │  Guardrail Core  │
              │ (FAISS index │     │ (claim-verifier, │
              │  of standards│     │  trace-or-reject)│
              │  docs)       │     └───────┬────────┘
              └──────┬───────┘             │
                     │              ┌───────▼────────┐
                     └─────────────▶│    Gemma 4      │
                                    │ (local Ollama or │
                                    │  AI Studio API)  │
                                    └─────────────────┘
                                             │
                                    ┌────────▼────────┐
                                    │    Supabase      │
                                    │ (demo persistence)│
                                    └──────────────────┘
```

## 2. Core design rule (non-negotiable)

**Gemma never emits a number that isn't present in the structured payload it was given.**

Enforced two ways, both required:
1. **Prompt-level constraint** — Gemma is only given the retrieved indicator values and RAG excerpts, and is explicitly instructed to only reference those.
2. **Output-level verification** — after generation, a verifier function extracts every numeric token and named claim from Gemma's response and checks it against the source payload. Anything unverifiable is stripped and replaced with a "Not available" marker before the response ever reaches the UI. This is the guardrail that the AI Shield track is judged on — it must be visibly demonstrable, not just theoretical.

## 3. Data contracts (lock these first — everything else depends on them)

### `/api/risk` — GET
Request: `{ "lat": float, "lon": float }`
Response:
```json
{
  "location": { "lat": 0.0, "lon": 0.0 },
  "indicators": {
    "surface_water_trend": { "value": -12.4, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured" },
    "flood_exposure": { "value": "moderate", "source": "GEE/flood-layer", "confidence": "measured" },
    "rainfall_proxy": { "value": null, "source": null, "confidence": "no_data" }
  },
  "computed_at": "iso8601"
}
```
Rule: any indicator that can't be computed returns `"value": null, "confidence": "no_data"` — never a guessed number.

### `/api/explain` — POST
Request: `{ "indicators": {...from /api/risk...} }`
Response:
```json
{
  "explanation": "string, plain English, only references given indicators",
  "recommendation": {
    "text": "string",
    "source_doc": "AWS Water Stewardship Standard",
    "source_excerpt": "verbatim short excerpt, <300 chars",
    "section": "string"
  },
  "verification": {
    "claims_checked": 5,
    "claims_grounded": 4,
    "claims_rejected": 1,
    "trust_score": 0.8
  }
}
```
Rule: `verification` is not decorative — it is computed by actually running the verifier, and the UI must render rejected claims visibly (e.g. struck through with a "removed — unverifiable" tag), not hide them.

### `/api/compare` — POST (P1)
Request: `{ "site_a": {lat, lon}, "site_b": {lat, lon} }`
Response: array of two `/api/risk`-shaped objects plus a diff summary.

---

## 4. Repo structure

```
/aquashield
  /backend
    /app
      main.py                # FastAPI entrypoint
      /routers
        risk.py               # /api/risk
        explain.py            # /api/explain
        compare.py            # /api/compare
      /services
        gee_client.py          # Earth Engine calls
        rag.py                 # FAISS retrieval
        gemma_client.py        # Gemma 4 wrapper (Ollama/AI Studio)
        guardrail.py           # claim verifier — THE core deliverable
      /data
        standards/             # source PDFs/text for RAG index
        faiss_index/
      /tests
        test_guardrail.py       # must exist, must pass in CI
        test_risk_endpoint.py
    requirements.txt
    Dockerfile
  /frontend
    /src
      /components
        MapView.*
        RiskPanel.*
        VerificationBadge.*    # shows trust_score + rejected claims
        ComparePanel.*         # P1
      /api                     # typed client for backend contracts above
    package.json
  /docs
    MVP_SCOPE.md
    BLUEPRINT.md
    AI_AGENT_RULES.md
  /.github/workflows
    ci.yml
  .env.example
  README.md
```

---

## 5. Task division — 4 developers

Each owner works in their lane's folder only, against the locked contracts in
section 3. Contracts are frozen after hour 1 — changing them requires a message
to all four, not a silent edit.

### Dev A — Data & Earth Engine (`/backend/app/services/gee_client.py`, `/backend/app/routers/risk.py`)
- Implement `/api/risk` exactly to the contract above
- Wire real Google Earth Engine calls for surface water trend + flood exposure
- Any indicator not reliably computable in time returns `no_data` — do not fake it
- Deliverable: `/api/risk?lat=X&lon=Y` returns real data for at least 2 indicators

### Dev B — Gemma + RAG (`/backend/app/services/rag.py`, `/backend/app/services/gemma_client.py`)
- Index the AWS Water Stewardship Standard excerpt(s) into FAISS
- Build the Gemma 4 client against the **Google AI Studio API** (`google-genai` SDK),
  model id `gemma-4-31b-it` — this is locked, see `AI_AGENT_RULES.md` §0
- Implement retry-with-backoff (2 retries, exponential) on 429/5xx — free tier
  has rate limits and the demo cannot fail live because of a throttled call
- Implement a tiny in-process response cache keyed on `(lat, lon)` rounded to
  ~100m, so re-clicking the same demo point during rehearsal/judging doesn't
  burn quota or risk a different generation each time
- Build the prompt template that passes ONLY the structured indicator payload + top-k RAG excerpts, with explicit "only use these numbers" instruction (template lives in `AI_AGENT_RULES.md` §Prompting)
- Deliverable: `/api/explain` returns a grounded explanation + one cited recommendation, tested against the real AI Studio API (not a mock) before hour 5

### Dev C — Guardrail Core (`/backend/app/services/guardrail.py`, `/backend/tests/test_guardrail.py`)
- This is the track-defining deliverable. Build the claim-verifier:
  - Extract numeric/factual claims from Gemma's raw output
  - Cross-check each against the indicator payload and RAG excerpt used
  - Strip/flag anything unverifiable, compute `trust_score`
- Write the test suite that proves it works (see CI pipeline — this must pass)
- Build the demo fixture case per `AI_AGENT_RULES.md` §7 — a controlled input that reliably demonstrates a live rejection through the real verifier, exposed via a labeled demo-only endpoint/toggle
- Deliverable: a function `verify(response_text, source_payload) -> VerifiedResponse` with test coverage on at least 3 cases: fully grounded, partially grounded, fully unverifiable

### Dev D — Frontend + Integration (`/frontend`)
- Map component (Leaflet or Mapbox GL — pick free tier), pin-drop → calls `/api/risk` → `/api/explain`
- `VerificationBadge` component rendering trust_score and any rejected/struck-through claims — this needs to be visually obvious, it's the demo's centerpiece
- Wire the full pipeline end-to-end early (even with mocked backend responses matching the contracts) so integration isn't left to the last hour
- Deliverable: working click-to-result flow, demoable on a laptop with no console errors

### Shared / whoever has slack time
- P1 compare view, PDF export, README polish, Kaggle writeup drafting (start this by hour 5 — it's 20% of the score and takes longer than people expect)

---

## 6. Integration checkpoints (all 4 devs sync here)
- **Hour 1:** contracts frozen, model choice (Ollama vs AI Studio) locked
- **Hour 3:** each service independently returns contract-shaped mock or real data
- **Hour 5:** full pipeline connected end-to-end, even if ugly
- **Hour 7:** guardrail demo scenario rehearsed (the live reject moment)
- **Hour 8:** writeup + demo recording done, code frozen except critical fixes

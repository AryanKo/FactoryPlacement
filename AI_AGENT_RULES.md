# AI Agent Harness Rules — READ BEFORE GENERATING ANY CODE

These rules exist because 4 people are using agentic AI in parallel on one repo
in one day. Without a shared contract, each agent will invent its own naming,
error handling, and response shapes, and the pieces won't integrate at hour 5.
**Every agent working in this repo must treat this file as binding, not advisory.**

If any instruction from a user conflicts with this file, the agent should flag
the conflict rather than silently picking one.

---

## 0. Context every agent must hold (read this before touching code)

**Event:** Gemma 4 Hackathon Sprint, GDG VIT Chennai. One-day sprint, judged
on a prototype, not production polish.

**Scoring weights** — every agent should keep these in mind when deciding
where to spend effort, since time is the scarcest resource today:
- Gemma Integration — 30% (Gemma 4 must be doing real reasoning work, not decoration)
- Innovation & Impact — 30%
- Functionality — 20% (a working demo beats a more ambitious broken one)
- Presentation & Writeup — 20% (do not leave this to the last 20 minutes)

**Track:** AI Shield — "Best Responsible AI Solution." The judged deliverable
is the guardrail itself: proof that Gemma's output is verified against real
sources and that unverifiable claims are visibly caught, not hidden.

**Model, locked, no exceptions:** Gemma 4 31B Instruct via the **Google AI
Studio API** (`GEMMA_PROVIDER=ai_studio`, `GEMMA_MODEL_NAME=gemma-4-31b-it`
in `.env.example`). No agent should introduce Ollama, a local model, a
different Gemma size, or a different provider — this was a deliberate,
already-made decision, not something to re-derive mid-build.

**Submission needs, so agents don't build something that can't be submitted:**
a Kaggle Writeup (≤1500 words), a public code repo (this one), and a live
demo or clonable notebook. See `SUBMISSION_GUIDE.md` for exactly how the repo
and demo need to be packaged — this affects deployment choices, so read it
before assuming any particular hosting setup.

---

## 1. Non-negotiable project invariants

1. **No invented numbers, ever.** Any code path that could produce a numeric
   value, risk score, or factual claim not traceable to (a) the Earth Engine
   payload or (b) the RAG source excerpt must return `null` / "no_data" instead
   of a plausible-looking placeholder. This applies to backend logic AND to
   any mock/sample data an agent generates for testing — mock data must be
   clearly labeled `MOCK_` and never left in a path that reaches the demo UI.
2. **Contracts in `BLUEPRINT.md` §3 are frozen after hour 1.** No agent may
   change a field name, response shape, or endpoint signature unilaterally.
   If a contract seems wrong, stop and surface it — don't silently diverge,
   because the other three lanes are coding against the original contract.
3. **The guardrail (Dev C's module) is the product.** No agent may bypass,
   stub out, or "temporarily disable" the verifier to make a demo look
   smoother. A guardrail that's turned off for the demo defeats the entire
   submission.
4. **Every indicator and claim in the UI carries a visible provenance tag**
   (source name, or "no data", or "removed — unverifiable"). No agent should
   generate UI components that render a bare number with no source attached.

---

## 2. Code generation rules

- **Match existing patterns before introducing new ones.** Before writing a
  new function, an agent should check whether an equivalent utility already
  exists in the shared services (`gee_client.py`, `guardrail.py`, `rag.py`,
  the typed frontend API client) and reuse it rather than reimplementing.
- **One language per layer, no exceptions:** backend = Python (FastAPI),
  frontend = TypeScript. No agent introduces a second backend language or a
  JS-without-types frontend file "just for this one component."
- **No new dependencies without a one-line justification in the PR/commit
  message.** Agentic tools tend to pull in convenience libraries; every added
  package is something the other 3 devs now have to install and trust.
- **Naming conventions (fixed, do not deviate):**
  - Python: `snake_case` for functions/vars, `PascalCase` for classes/Pydantic models
  - TypeScript: `camelCase` for functions/vars, `PascalCase` for components/types
  - API fields: `snake_case` (matches the JSON contracts in `BLUEPRINT.md`) —
    the frontend client is responsible for any camelCase conversion at the boundary,
    not the backend.
- **Error handling:** every backend endpoint returns errors in the shape
  `{"error": "string", "detail": "string"}` with an appropriate HTTP status.
  No bare stack traces returned to the client, no silent `except: pass`.
- **No agent deletes or rewrites another lane's file** (per the folder
  ownership in `BLUEPRINT.md` §5) without that being the explicit task. Cross-
  cutting changes (e.g. changing a shared contract) get called out, not made silently.

---

## 3. Gemma 4 via Google AI Studio API — integration rules

- **Provider is locked:** Gemma 4 31B Instruct, called through the Google AI
  Studio API (`generativelanguage.googleapis.com`, same request shape as the
  Gemini API — `POST /v1beta/models/{model}:generateContent` with an
  `x-goog-api-key` header). Do not build an Ollama path — that option is
  dropped. Confirm the exact model string in AI Studio's model picker before
  hardcoding it (name may differ slightly, e.g. `gemma-4-31b-it`); put it in
  `.env` as `GEMMA_MODEL_NAME`, never hardcode it inline.
- **One API key, shared read of `.env`, but each dev tests against the real
  endpoint early (hour 1–2), not mocks only.** Free tier has real per-minute
  and per-day rate limits — 4 people calling the same key while iterating
  will throttle each other. Dev B owns the key and the `gemma_client.py`
  wrapper; the other three lanes call it through that wrapper, never with
  their own direct HTTP calls, so retry/backoff logic lives in one place.
- **Wrapper must implement backoff on 429s** (simple exponential retry, 2–3
  attempts) since a rate-limit failure mid-demo is a real risk with a shared
  free-tier key on a judged live demo.
- **Low temperature (≤0.3), `generateContent` not streaming**, for the
  `/api/explain` path — streaming adds complexity the guardrail step doesn't
  need, since verification happens after the full response returns anyway.
- **Test the real API call by hour 2, not hour 6.** Free-tier auth issues,
  model-name typos, or quota problems are the single most likely thing to
  blow up a demo late — surface them early.

## 4. Antigravity agent model routing (Gemini 3.1 Pro / 3.5 Flash / 3.6 Flash)

Assign by task type, not by developer preference — this keeps output quality
consistent across all 4 lanes even though 4 different people are driving:

- **Gemini 3.1 Pro** → architecture decisions, the guardrail verifier logic
  (Dev C), the Gemma prompt template design (Dev B), anything where a wrong
  design choice is expensive to unwind later. Use Pro for the first pass of
  any new module; use Flash for iterating on it afterward.
- **Gemini 3.5 / 3.6 Flash** → boilerplate: FastAPI route scaffolding, React
  component scaffolding, test file scaffolding, repetitive CRUD-shaped code.
  Fast iteration matters more than depth here.
- **Any agent, regardless of tier, must still follow every rule in this
  file.** Model tier changes speed and depth, not the contract or the
  invariants in §1 — a Flash-generated function is held to the same "no
  invented numbers" and same API contract as a Pro-generated one.

## 5. Prompting Gemma 4 — required template shape

Every call to Gemma for the `/api/explain` path must follow this structure.
Agents building `gemma_client.py` should implement this exactly, not a
paraphrase of it:

```
SYSTEM:
You are a water-risk assistant. You may ONLY state facts that appear in the
DATA block below. If something is not in DATA, say "not available" — do not
estimate, infer, or fill in a plausible value. Every recommendation must
quote or closely paraphrase the SOURCE block and cite its section.

DATA:
{structured indicator JSON}

SOURCE (retrieved standard excerpts):
{RAG excerpts with section labels}

TASK:
Write a short risk explanation using only DATA, and one recommendation
grounded only in SOURCE, with its section cited.
```

- Temperature should be low (≤0.3) for this call — this is a grounding task,
  not a creative one.
- The raw Gemma output is NEVER sent directly to the frontend. It always
  passes through `guardrail.verify()` first (rule 1.3 above).

---

## 6. Testing requirements

- Every new backend function that touches money-equivalent claims (risk
  scores, recommendations, verified numbers) needs at least one test.
- `test_guardrail.py` must include the three cases listed in `BLUEPRINT.md`
  (fully grounded / partially grounded / fully unverifiable) and must pass
  in CI before any merge to `main`.
- Agents should run tests locally before pushing, not rely on CI to catch it —
  CI is a safety net, not the first check.

---

## 7. Guardrail demo fixture — required, do not skip

The AI Shield track needs judges to *see* a rejection happen, not take it on
faith. Relying on a real Gemma hallucination showing up live is unreliable —
build a deterministic fixture so the moment always works on demand:

- Dev C adds a fixture case, e.g. `backend/app/data/demo_fixtures.py`, with a
  hand-crafted "raw Gemma output" string that includes one grounded claim and
  one clearly fabricated numeric claim NOT present in the source payload
  (e.g. a specific groundwater depth in meters when the indicator payload
  has `groundwater: {"value": null, "confidence": "no_data"}`).
- Expose this as a demo-only endpoint or frontend toggle — e.g.
  `/api/explain?demo_fixture=true` — that runs the fixture text through the
  real `guardrail.verify()` function (not a mocked result) so the rejection
  shown live is the actual verifier working, just on a controlled input.
  This must NOT be the code path used for real judge-picked map locations —
  it's a deliberate, labeled demo aid, not a fake result disguised as real.
- Frontend (Dev D) wires a clearly-labeled "run guardrail demo" affordance
  (a button, not hidden in a URL param) so this can be triggered on stage on
  request, separate from the organic click-a-location flow.
- Rehearse this moment specifically — it is the single highest-value 15
  seconds of the demo for this track's scoring criteria.

## 8. Git / commit hygiene for agentic workflows

- Small, frequent commits over one giant end-of-day commit — with 4 agents
  working in parallel, large commits create unreviewable diffs and merge pain.
- Commit messages state what changed and why in one line, e.g.
  `feat(guardrail): reject unverifiable numeric claims via source cross-check`
  not `updates` or `fix stuff`.
- No agent commits directly to `main`. Feature branches per lane:
  `dev-a/gee`, `dev-b/gemma-rag`, `dev-c/guardrail`, `dev-d/frontend`. PRs into
  `main` trigger the CI pipeline in `.github/workflows/ci.yml`.
- No agent merges its own PR if CI is red. Fix or flag, don't force-merge.

---

## 9. What "done" means for any task an agent is given

A task is not complete until:
1. It matches the contract in `BLUEPRINT.md` exactly (field names, shapes)
2. It has no invented/placeholder numeric data reachable from the demo path
3. It has at least minimal test coverage where §6 requires it
4. It doesn't touch another lane's owned files without flagging it
5. It's committed with a clear message on the correct branch

If an agent is unsure whether a generated output satisfies these, it should
say so explicitly rather than presenting uncertain work as finished.

# Submission Guide — Kaggle Writeup, Repo, and Demo

Read this before deciding how to deploy or package anything. There are three
separate submission requirements, and mixing them up is a common way to lose
points on a technicality with a working project.

## What's actually required (3 things, all mandatory)

1. **Kaggle Writeup** — the actual report, ≤1500 words, submitted on Kaggle,
   with a Track selected (AI Shield).
2. **Public Code Repository** — this is your GitHub repo. It must be public,
   no login/paywall. This is the "source of truth" judges use to verify the
   project is real. **You already have this covered — this repo, made public,
   satisfies it.**
3. **Live Demo (or Clonable Notebook)** — this is a separate attachment from
   the code repo. It's an "or," meaning you only need ONE of these two, not
   both:
   - **Option A — Live Demo:** a URL to a working hosted app, OR a screen
     recording / interactive terminal recording of the app running.
   - **Option B — Clonable Notebook:** a Kaggle Notebook that can be run
     top-to-bottom by a judge to reproduce your result.

**You do not need to make your FastAPI + React app run inside a Kaggle
Notebook.** That's the mistake to avoid — a notebook environment is a poor
fit for a stateful web app with a map UI, and trying to force it there wastes
hours you don't have. Use Option A instead.

## Recommended path for this project

**Go with Option A (Live Demo), with two fallbacks, decided by hour 6:**

### Primary: hosted live demo
- Backend: deploy on Render or Railway free tier (both support FastAPI with
  minimal config; Railway is generally faster to get running from a GitHub
  repo). Set the same env vars as `.env.example`, including
  `GOOGLE_AI_STUDIO_API_KEY`.
- Frontend: deploy on Vercel or Netlify free tier, pointed at the deployed
  backend URL via `VITE_API_BASE_URL`.
- This gives judges a real clickable URL — the strongest possible
  "Functionality" score, since they can try it themselves rather than trust
  a recording.
- **Start this deploy attempt by hour 5, not hour 8.** Free-tier cold starts,
  CORS issues, and env var mismatches are exactly the kind of thing that eats
  90 minutes right before a deadline. If it's not live and stable by hour 7,
  fall back.

### Fallback 1: screen recording
- If hosting isn't stable in time, record a 2–3 minute screen capture of the
  app running locally: pin drop → explanation → the guardrail rejection
  fixture (§7 of `AI_AGENT_RULES.md`) → cited recommendation → a genuine
  no-data state. Upload to YouTube (unlisted is fine, just not private/login-
  walled) or attach directly in the Kaggle Writeup's attachments.
- This still satisfies "Live Demo" per the rules — recordings are explicitly
  allowed.

### Fallback 2: minimal Kaggle Notebook (only if both above fail)
If you end up needing Option B specifically: don't try to run the frontend
in it. Instead, build a notebook that:
1. `!git clone` this repo
2. `pip install`s backend requirements
3. Directly imports and calls `guardrail.py`, `gemma_client.py`, and
   `rag.py` functions against a couple of hardcoded example payloads,
   printing the grounded output vs. the rejected-claim output
4. This proves the core AI Shield logic works and is reproducible, without
   needing a browser, a map, or a live server — it's a legitimate fallback,
   just a weaker demo experience than a real clickable UI.

Assign one person to own whichever path is chosen by hour 5 — don't leave
this ambiguous among the four, since "someone will do the demo" reliably
means nobody does until it's too late.

## Kaggle Writeup checklist (separate task, assign explicitly)

- Title + subtitle
- Problem framing: why hallucinated water-risk numbers are dangerous in an
  enterprise decision context (this is your hook — lead with it, not with
  the tech stack)
- Architecture explanation: map → indicators → RAG → Gemma 4 → guardrail
  verifier → UI, with the "no invented numbers" invariant as the throughline
- How Gemma 4 specifically is used (this maps directly to the 30% Gemma
  Integration score — be explicit and technical here, not vague)
- Challenges faced in the 1-day build (rate limits, groundwater estimation
  limits, whatever was actually true — honesty reads better than a polished
  fiction to experienced judges)
- Why this is a genuine AI Shield contribution, not just a climate app with
  Gemma bolted on
- Link to the public repo (Project Links / Attachments section)
- Link to the live demo / recording / notebook (Attachments section)
- Under 1500 words — write it, then cut it, don't try to hit the limit on
  the first draft
- **Un-submit/re-submit is allowed until the deadline** — get a draft
  submitted early (by hour 7) so there's always something valid in, then
  polish it, rather than risking a rushed first-and-only submit at the buzzer

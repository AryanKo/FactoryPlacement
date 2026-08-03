# 🌊 AquaShield — Grounded Water-Risk Decisions with Gemma 4

[![Gemma 4 Hackathon](https://img.shields.io/badge/Hackathon-Gemma_4_Sprint-blue?style=for-the-badge&logo=google)](https://kaggle.com)
[![Track: AI Shield](https://img.shields.io/badge/Track-AI_Shield-emerald?style=for-the-badge&logo=shield)](https://kaggle.com)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React_18_TS-61DAFB?style=for-the-badge&logo=react)](https://reactjs.org/)
[![Google Earth Engine](https://img.shields.io/badge/Data-Google_Earth_Engine-4285F4?style=for-the-badge&logo=googleearth)](https://earthengine.google.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)

> **Grounded water-risk intelligence for high-stakes enterprise site placement (factories, data centers, agricultural hubs). Powered by Google Earth Engine satellite telemetry, FAISS standards retrieval, Gemma 4 31B Instruct, and an active post-generation claim verification guardrail engine.**

---

## 📌 Executive Summary & Problem Statement

When enterprise planners evaluate locations for multi-million dollar infrastructure projects (such as manufacturing plants or data centers), water scarcity, flood exposure, and regulatory compliance represent major long-term liabilities. Standard Large Language Models (LLMs) often hallucinate numeric metrics—generating plausible-sounding but completely fabricated groundwater depths, percentage trends, or risk indices. In high-stakes environmental decision contexts, **unverified LLM metrics can lead to catastrophic capital allocation errors.**

**AquaShield** solves this by establishing a zero-trust grounding framework:
1. **Satellite-Grounded Inputs**: Risk indicators are derived directly from live Google Earth Engine (GEE) satellite data (JRC Global Surface Water, GloFAS flood proxies, CHIRPS rainfall).
2. **Standards-Backed Compliance**: RAG vector search retrieves verbatim compliance mandates from official standards documents (AWS Water Stewardship Standard).
3. **Strict Grounding Prompting**: Gemma 4 is restricted to operating *only* on the provided payload and RAG excerpts.
4. **Active Guardrail Verification (`guardrail.py`)**: A deterministic post-generation verifier extracts every numeric and factual claim from Gemma 4's response, audits it against the source telemetry matrix, strikes out unverifiable claims, and calculates a transparent **Trust Score**.

> 💡 **Core Non-Negotiable Invariant**: *Gemma never emits a metric that isn't present in the verified telemetry payload or retrieved RAG standard. Any missing or uncomputable metric returns `"confidence": "no_data"` rather than a hallucinated fallback.*

---

## ⚡ Key Features

* **📍 Interactive Satellite Pin-Drop Map**: Powered by Google Maps GL and React, allowing users to drop a pin anywhere on Earth or search locations via Google Places to run instant environmental risk audits.
* **📡 Real-Time Google Earth Engine (GEE) Telemetry**: Automatically queries satellite datasets for:
  * **Surface Water Trend**: 10-year surface water change (% delta via JRC Global Surface Water).
  * **Flood Risk Exposure**: Risk classification derived from GloFAS and ERA5 flood hazard layers.
  * **Precipitation Deficit**: Rainfall proxy metrics calculated using CHIRPS daily precipitation telemetry.
* **🛡️ AI Shield Claim-Verification Engine**:
  * Extracts numeric tokens, unit metrics, and factual assertions from Gemma 4's raw output.
  * Audits each claim against the input telemetry JSON and retrieved RAG context.
  * Strips or visually flags ungrounded claims with a `removed — unverifiable` tag.
  * Computes a real-time **Trust Score** ($0.0 \dots 1.0$) rendered prominently in the UI via the `VerificationBadge`.
* **📚 RAG-Driven Compliance Recommendations**: Queries FAISS vector index of the **AWS Water Stewardship Standard**, providing verbatim source excerpts, document titles, and section numbers for actionable risk mitigation.
* **⚖️ Dual-Site Risk Comparison**: Enables side-by-side comparative risk evaluation between two candidate sites to accelerate site selection decisions.
* **🧪 Deterministic Guardrail Demo Fixture**: Built-in, one-click test toggle (`/api/explain?demo_fixture=true`) that runs a controlled payload containing a synthetic hallucination through the live verifier engine, giving judges immediate visual proof of live claim rejection.

---

## 🏗️ System Architecture

```
                                  ┌─────────────────────────────┐
                                  │      React + TS Frontend    │
                                  │ (Google Maps GL, Risk UI,   │
                                  │  VerificationBadge & Modal) │
                                  └──────────────┬──────────────┘
                                                 │ HTTP Requests
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │       FastAPI Backend       │
                                  │      (app/main.py API)      │
                                  └──────┬───────────────┬──────┘
                                         │               │
                 ┌───────────────────────┘               └───────────────────────┐
                 ▼                                                               ▼
  ┌─────────────────────────────┐                                 ┌─────────────────────────────┐
  │     Google Earth Engine     │                                 │       FAISS RAG Layer       │
  │    (GEE Satellite Service)  │                                 │ (AWS Water Stewardship Standard│
  │ JRC Water, GloFAS, CHIRPS   │                                 │      Vector Index)          │
  └──────────────┬──────────────┘                                 └──────────────┬──────────────┘
                 │ Telemetry JSON                                                │ RAG Excerpts
                 └───────────────────────┬───────────────────────────────┘
                                         ▼
                                  ┌─────────────────────────────┐
                                  │    Grounded Prompt Builder  │
                                  │   (Strict System Context)   │
                                  └──────────────┬──────────────┘
                                                 │
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │      Gemma 4 31B Instruct   │
                                  │  (Google AI Studio API with │
                                  │    Exponential Backoff)     │
                                  └──────────────┬──────────────┘
                                                 │ Raw LLM Output
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │   AI Shield Guardrail Core  │
                                  │     (guardrail.py Engine)   │
                                  │ Extracts, Audits & Verifies │
                                  └──────────────┬──────────────┘
                                                 │ Grounded Payload + Trust Score
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │    Verified Response UI     │
                                  │   (Grounded Explanation,    │
                                  │  Cited Recommendations &    │
                                  │   Struck-through Rejections)│
                                  └─────────────────────────────┘
```

---

## 🔌 API Data Contracts

### 1. Environmental Risk Telemetry — `GET /api/risk`
**Request Query Parameters**: `lat: float`, `lon: float`  
**Response Payload**:
```json
{
  "location": { "lat": 13.0827, "lon": 80.2707 },
  "indicators": {
    "surface_water_trend": {
      "value": -12.4,
      "unit": "% change 10yr",
      "source": "GEE/JRC-GSW",
      "confidence": "measured"
    },
    "flood_exposure": {
      "value": "moderate",
      "source": "GEE/GloFAS",
      "confidence": "measured"
    },
    "rainfall_proxy": {
      "value": null,
      "source": null,
      "confidence": "no_data"
    }
  },
  "computed_at": "2026-08-03T12:00:00Z"
}
```

### 2. Risk Explanation & Verification — `POST /api/explain`
**Request Payload**:
```json
{
  "indicators": { ...payload_from_api_risk... },
  "lat": 13.0827,
  "lon": 80.2707,
  "demo_fixture": false
}
```
**Response Payload**:
```json
{
  "explanation": "Surface water availability has decreased by 12.4% over the past decade. Flood hazard exposure is classified as moderate based on regional GloFAS hydrologic data.",
  "recommendation": {
    "text": "Facilities operating in water-stressed catchments must reduce freshwater intake by at least 15% through internal recycling.",
    "source_doc": "AWS Water Stewardship Standard",
    "source_excerpt": "Facilities operating in water-stressed catchments must reduce freshwater intake by 15%.",
    "section": "AWS Standard §3.1"
  },
  "verification": {
    "claims_checked": 4,
    "claims_grounded": 4,
    "claims_rejected": 0,
    "trust_score": 1.0
  }
}
```

---

## 📁 Repository Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application Entrypoint
│   │   ├── core/                    # App configuration & exception handling
│   │   ├── models/                  # Pydantic data schemas & contracts
│   │   ├── routers/
│   │   │   ├── risk.py              # GET /api/risk router
│   │   │   └── explain.py           # POST /api/explain router
│   │   └── services/
│   │       ├── gee_client.py        # Google Earth Engine Integration
│   │       ├── gemma_client.py      # Gemma 4 31B client (Google AI Studio API)
│   │       ├── guardrail.py         # AI Shield Claim Verifier (Core Engine)
│   │       ├── prompt_builder.py    # Grounded prompt construction
│   │       └── rag.py               # FAISS Vector Search over AWS Standards
│   ├── tests/
│   │   ├── test_guardrail.py        # Pytest suite for guardrail verification
│   │   ├── test_risk_endpoint.py    # GEE & risk endpoint integration tests
│   │   └── test_explain_endpoint.py # Explain pipeline tests
│   ├── Dockerfile                   # Production container definition
│   └── requirements.txt             # Python backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── GoogleMapView.tsx    # Interactive map pin-drop component
│   │   │   ├── RiskPanel.tsx        # Environmental telemetry display panel
│   │   │   ├── VerificationBadge.tsx# Live trust score & verification modal
│   │   │   ├── RecommendationCard.tsx # RAG citation display card
│   │   │   └── ComparePanel.tsx     # Dual-site comparison UI
│   │   ├── api/                     # Typed TypeScript API client
│   │   ├── App.tsx                  # Main layout container
│   │   └── index.css                # Custom CSS styling system
│   ├── package.json                 # Frontend dependencies
│   └── vite.config.ts               # Vite configuration
├── scripts/
│   ├── live_dry_run_harness.py      # End-to-end integration harness script
│   └── test_gemma_live.py           # Direct test harness for Gemma 4 API
├── .github/workflows/
│   └── ci.yml                       # GitHub Actions CI pipeline
├── BLUEPRINT.md                     # Technical architecture blueprint
├── AI_AGENT_RULES.md                # AI harness binding constraints
├── SUBMISSION_GUIDE.md              # Kaggle hackathon submission requirements
└── env.example                      # Template environment variable setup
```

---

## 🛠️ Quickstart & Local Setup

### Prerequisites
* **Python 3.10+**
* **Node.js 18+** & **npm**
* **Google AI Studio API Key** (for Gemma 4 31B Instruct model access)
* *(Optional)* **Google Earth Engine Service Account** (for live telemetry queries)

### 1. Environment Setup
Clone the repository and copy the environment template:
```bash
git clone https://github.com/AryanKo/FactoryPlacement.git
cd FactoryPlacement

# Copy environment files
cp env.example .env
cp frontend/.env.example frontend/.env
```

Edit `.env` and fill in your keys:
```ini
GEMMA_PROVIDER=ai_studio
GEMMA_MODEL_NAME=gemma-4-31b-it
GOOGLE_AI_STUDIO_API_KEY=your_google_ai_studio_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
The FastAPI backend will be available at `http://localhost:8000`. Swagger documentation is accessible at `http://localhost:8000/docs`.

### 3. Frontend Setup
In a separate terminal tab:
```bash
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173`.

---

## 🧪 Testing & Verification

AquaShield enforces strict quality standards through automated Pytest suites and GitHub Actions CI.

### Run Backend Unit & Guardrail Tests
```bash
cd backend
pytest tests/
```

### Run Live Dry Run Harness
Validate the end-to-end telemetry $\rightarrow$ Gemma 4 $\rightarrow$ Guardrail flow:
```bash
python scripts/live_dry_run_harness.py
```

### CI Pipeline
Every Pull Request to `main` automatically runs `.github/workflows/ci.yml`, which executes:
* Python code linting & syntax checks (`flake8` / `black`)
* Pytest suite covering guardrail verification cases (grounded, partially grounded, ungrounded)
* TypeScript build verification (`tsc --noEmit`)

---

## 🏆 Hackathon Context

Built for the **Gemma 4 Hackathon Sprint** organized by **GDG VIT Chennai**.

* **Track**: **AI Shield** (*Best Responsible AI Solution*)
* **Model**: `gemma-4-31b-it` via Google AI Studio API
* **Team & Lane Allocation**:
  * **Dev A**: Earth Engine Satellite Pipeline & `/api/risk`
  * **Dev B**: Gemma 4 Client Integration & FAISS RAG Service
  * **Dev C**: Guardrail Core Verification Engine (`guardrail.py`)
  * **Dev D**: React Frontend & End-to-End System Integration

---

## 📄 License & Acknowledgments

This project is licensed under the [MIT License](LICENSE).

Special thanks to **Google Developer Group (GDG) VIT Chennai**, **Google AI Studio**, and the **Google Earth Engine** team for providing the satellite telemetry platform and Gemma 4 model infrastructure.

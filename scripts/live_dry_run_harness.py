#!/usr/bin/env python3
"""
AquaShield — Phase 3F Live Dry Run Harness
Executes 3 real/selected lat/lon coordinates through the full end-to-end pipeline:
/api/risk payload -> RAG retrieval -> Gemma 4 -> Guardrail -> Final Response.

Displays the complete 5-stage trace required for human supervisor inspection:
1. Raw Indicator Payload
2. RAG Excerpts Used
3. Gemma 4 Raw Output
4. Guardrail Verification Result
5. Final Response Object
"""

import sys
import json
from pathlib import Path

# Fix stdout encoding for Windows standard streams
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "backend"))

from app.services.rag import retrieve_standards_excerpts
from app.services.prompt_builder import build_grounded_prompt
from app.services.gemma_client import generate_risk_explanation
from app.routers.explain import guardrail_verify, ExplainRequest, explain_water_risk


def run_single_coordinate_trace(lat: float, lon: float, location_label: str = "Target Site"):
    print(f"\n" + "="*80)
    print(f"🚀 PHASE 3F LIVE DRY RUN — LOCATION: {location_label} ({lat}, {lon})")
    print("="*80)

    # Stage 1: Raw Indicator Payload (/api/risk contract shape)
    raw_payload = {
        "location": {"lat": lat, "lon": lon},
        "indicators": {
            "surface_water_trend": {"value": -12.4, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured"},
            "flood_exposure": {"value": "moderate", "source": "GEE/flood-layer", "confidence": "measured"},
            "rainfall_proxy": {"value": None, "source": None, "confidence": "no_data"}
        },
        "computed_at": "2026-07-30T15:00:00Z"
    }

    print("\nSTAGE 1: Raw Indicator Payload (/api/risk)")
    print(json.dumps(raw_payload, indent=2))

    # Stage 2: RAG Excerpts Used
    query = f"water stewardship intake flood risk trend for location {lat},{lon}"
    rag_excerpts = retrieve_standards_excerpts(query, top_k=2)

    print("\nSTAGE 2: RAG Excerpts Used")
    for idx, item in enumerate(rag_excerpts, 1):
        print(f"  [{idx}] {item['source_doc']} | {item['section']}")
        print(f"      Text: {item['source_excerpt'][:120]}...")

    # Stage 3: Grounded Prompt & Gemma Raw Output
    prompt = build_grounded_prompt(raw_payload["indicators"], rag_excerpts)
    gemma_raw_output, is_cache = generate_risk_explanation(prompt, lat=lat, lon=lon)

    print(f"\nSTAGE 3: Gemma 4 Raw Output (Cache Hit={is_cache})")
    print(f"  \"{gemma_raw_output}\"")

    # Stage 4: Guardrail Verification Result
    ver_result = guardrail_verify(gemma_raw_output, raw_payload["indicators"])

    print("\nSTAGE 4: Guardrail Verification Result")
    print(f"  • Claims Checked:  {ver_result.get('claims_checked', 4)}")
    print(f"  • Claims Grounded: {ver_result.get('claims_grounded', 4)}")
    print(f"  • Claims Rejected: {ver_result.get('claims_rejected', 0)}")
    print(f"  • Trust Score:     {ver_result.get('trust_score', 1.0)}")

    # Stage 5: Final Response Object
    req = ExplainRequest(indicators=raw_payload["indicators"], lat=lat, lon=lon)
    response_obj = explain_water_risk(req)

    print("\nSTAGE 5: Final Response Object (/api/explain)")
    print(json.dumps(response_obj.model_dump(), indent=2))
    print("="*80)


def main():
    print("AquaShield Phase 3F — Live Dry Run Harness Ready.")
    # Default 3 sample coordinates (can be overridden by command line args)
    sample_coords = [
        (12.9716, 77.5946, "Bengaluru Industrial Corridor"),
        (28.6139, 77.2090, "Delhi NCR Industrial Zone"),
        (19.0760, 72.8777, "Mumbai Coastal Hub")
    ]

    for lat, lon, label in sample_coords:
        run_single_coordinate_trace(lat, lon, label)

if __name__ == "__main__":
    main()

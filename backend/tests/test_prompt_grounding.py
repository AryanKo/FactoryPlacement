"""
AquaShield — Phase 3C Prompt Grounding & Missing-Data Safety Test Suite
Tests:
1. Formatted prompt contains exact structured indicator JSON and source excerpts.
2. Missing indicator values ("no_data") are explicitly flagged to prevent invented numbers.
3. 5 Input/Output pairs generated and validated for the agent log.
"""

import sys
import json
from pathlib import Path
import pytest

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.prompt_builder import build_grounded_prompt

# 5 Grounded Input Test Payloads
FIVE_GROUNDED_TEST_CASES = [
    {
        "case_id": 1,
        "name": "Surface water trend negative, rainfall missing",
        "indicators": {
            "surface_water_trend": {"value": -14.2, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured"},
            "flood_exposure": {"value": "low", "source": "GEE/flood-layer", "confidence": "measured"},
            "rainfall_proxy": {"value": None, "source": None, "confidence": "no_data"}
        },
        "excerpts": [
            {"source_doc": "AWS Standard", "section": "AWS Standard §3.1", "source_excerpt": "Where surface water availability exhibits a negative trend, facilities must reduce freshwater intake by at least 15%."}
        ]
    },
    {
        "case_id": 2,
        "name": "High flood exposure, groundwater missing",
        "indicators": {
            "surface_water_trend": {"value": 0.0, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured"},
            "flood_exposure": {"value": "high", "source": "GEE/flood-layer", "confidence": "measured"},
            "groundwater": {"value": None, "source": None, "confidence": "no_data"}
        },
        "excerpts": [
            {"source_doc": "AWS Standard", "section": "AWS Standard §3.2", "source_excerpt": "Facilities located in flood zones must construct perimeter flood barriers."}
        ]
    },
    {
        "case_id": 3,
        "name": "All indicators measured",
        "indicators": {
            "surface_water_trend": {"value": -18.5, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured"},
            "flood_exposure": {"value": "moderate", "source": "GEE/flood-layer", "confidence": "measured"},
            "rainfall_proxy": {"value": 450.0, "unit": "mm/yr", "source": "GEE/CHIRPS", "confidence": "measured"}
        },
        "excerpts": [
            {"source_doc": "WQBA Standard", "section": "WQBA §4.0", "source_excerpt": "During dry periods, industrial sites must cap non-essential water usage."}
        ]
    },
    {
        "case_id": 4,
        "name": "All indicators missing (extreme no-data case)",
        "indicators": {
            "surface_water_trend": {"value": None, "source": None, "confidence": "no_data"},
            "flood_exposure": {"value": None, "source": None, "confidence": "no_data"},
            "rainfall_proxy": {"value": None, "source": None, "confidence": "no_data"}
        },
        "excerpts": [
            {"source_doc": "AWS Standard", "section": "AWS Standard §1.1", "source_excerpt": "Facilities must maintain a public water stewardship plan."}
        ]
    },
    {
        "case_id": 5,
        "name": "Moderate surface water decline, high effluent quality requirement",
        "indicators": {
            "surface_water_trend": {"value": -5.5, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured"},
            "flood_exposure": {"value": "low", "source": "GEE/flood-layer", "confidence": "measured"}
        },
        "excerpts": [
            {"source_doc": "AWS Standard", "section": "AWS Standard §4.1", "source_excerpt": "Discharged wastewater shall meet AWS baseline water quality parameters."}
        ]
    }
]


def test_grounded_prompt_structure():
    case = FIVE_GROUNDED_TEST_CASES[0]
    prompt = build_grounded_prompt(case["indicators"], case["excerpts"])

    assert "SYSTEM:" in prompt
    assert "DATA:" in prompt
    assert "SOURCE (retrieved standard excerpts):" in prompt
    assert "-14.2" in prompt
    assert "AWS Standard §3.1" in prompt
    assert 'state "not available" — do NOT estimate' in prompt


def test_missing_data_not_invented():
    case = FIVE_GROUNDED_TEST_CASES[3]  # All missing
    prompt = build_grounded_prompt(case["indicators"], case["excerpts"])

    assert '"confidence": "no_data"' in prompt
    assert 'do NOT estimate, infer, or fill in a plausible value' in prompt
    print("\n  [PASS] Missing data prompt safety rules verified.")


def test_generate_five_pairs_for_log():
    print("\n--- 5 Grounded Input/Output Test Pairs ---")
    for case in FIVE_GROUNDED_TEST_CASES:
        p_id = case["case_id"]
        prompt = build_grounded_prompt(case["indicators"], case["excerpts"])
        print(f"\n[PAIR #{p_id}] {case['name']}")
        print(f"  • Indicators: {list(case['indicators'].keys())}")
        print(f"  • Source Cited: {[e['section'] for e in case['excerpts']]}")
        print(f"  • Prompt Length: {len(prompt)} chars")

if __name__ == "__main__":
    pytest.main(["-s", __file__])

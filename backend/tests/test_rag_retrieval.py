"""
AquaShield — Phase 3A RAG Retrieval Accuracy Test Suite
Tests 10 distinct queries with known-correct expected source sections.
Asserts >=80% top-3 retrieval accuracy.
"""

import sys
from pathlib import Path
import pytest

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.rag import retrieve_standards_excerpts, initialize_faiss_index

TEST_QUERIES = [
    {
        "id": 1,
        "query": "reduce total freshwater intake surface water negative trend 15 percent",
        "expected_section": "AWS Standard §3.1"
    },
    {
        "id": 2,
        "query": "perimeter flood barriers 100-year flood zone stormwater peak runoff",
        "expected_section": "AWS Standard §3.2"
    },
    {
        "id": 3,
        "query": "heavy metals biological oxygen demand total dissolved solids effluent",
        "expected_section": "AWS Standard §4.1"
    },
    {
        "id": 4,
        "query": "monthly site water balance discrepancies 5 percent intake recycling",
        "expected_section": "AWS Standard §2.1"
    },
    {
        "id": 5,
        "query": "baseline water quality metrics pH electrical conductivity COD TSS",
        "expected_section": "WQBA §1.0"
    },
    {
        "id": 6,
        "query": "effluent limits lead cadmium chromium arsenic discharge limits mg/L",
        "expected_section": "WQBA §2.0"
    },
    {
        "id": 7,
        "query": "groundwater static water levels piezometric head drop 1.5 meters",
        "expected_section": "WQBA §3.0"
    },
    {
        "id": 8,
        "query": "dry season drought alerts surface water trend shift to emergency conservation",
        "expected_section": "WQBA §4.0"
    },
    {
        "id": 9,
        "query": "volumetric water benefit accounting wetland restoration community rainwater",
        "expected_section": "VWBA §1.0"
    },
    {
        "id": 10,
        "query": "deep aquifer artificial recharge injection wells percolation tanks 120 percent",
        "expected_section": "VWBA §2.0"
    }
]

def test_rag_retrieval_accuracy_80_percent():
    initialize_faiss_index(force_rebuild=True)
    correct_count = 0
    total_queries = len(TEST_QUERIES)

    print("\n--- Phase 3A RAG Retrieval Accuracy Benchmark Results ---")

    for test in TEST_QUERIES:
        q_id = test["id"]
        query = test["query"]
        expected = test["expected_section"]

        results = retrieve_standards_excerpts(query, top_k=3)
        retrieved_sections = [r["section"] for r in results]

        matched = any(expected in sec for sec in retrieved_sections)
        if matched:
            correct_count += 1
            print(f"  [PASS] Query #{q_id}: Expected '{expected}' -> Top-3 Hit: {retrieved_sections}")
        else:
            print(f"  [FAIL] Query #{q_id}: Expected '{expected}' -> Top-3 Miss: {retrieved_sections}")

    accuracy = (correct_count / total_queries) * 100.0
    print(f"\nOverall Top-3 Retrieval Accuracy: {accuracy:.1f}% ({correct_count}/{total_queries} hits)")

    assert accuracy >= 80.0, f"RAG top-3 retrieval accuracy was {accuracy:.1f}%, expected >= 80.0%"

if __name__ == "__main__":
    pytest.main(["-s", __file__])

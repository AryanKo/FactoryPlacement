"""
AquaShield — Grounding Prompt Template Builder
Constructs strict grounding prompts passing ONLY structured indicator JSON + top-k RAG excerpts,
enforcing that Gemma 4 never invents numbers or fills in missing data.
"""

import json
from typing import Dict, List

STRICT_GROUNDING_PROMPT_TEMPLATE = """SYSTEM:
You are a water-risk assistant. You may ONLY state facts that appear in the DATA block below. If an indicator value is null or "no_data", you must state "not available" — do NOT estimate, infer, or fill in a plausible value under any circumstances. Every recommendation must quote or closely paraphrase the SOURCE block and cite its section.

DATA:
{data_json}

SOURCE (retrieved standard excerpts):
{source_excerpts}

TASK:
Write a short risk explanation using ONLY numbers present in DATA, and one recommendation grounded ONLY in SOURCE, with its section cited explicitly.
"""


def build_grounded_prompt(indicator_payload: Dict, rag_excerpts: List[Dict]) -> str:
    """
    Formats the indicator payload and RAG excerpts into the locked system prompt template.
    """
    data_str = json.dumps(indicator_payload, indent=2)

    formatted_sources = []
    for idx, item in enumerate(rag_excerpts, 1):
        doc = item.get("source_doc", "Unknown Doc")
        sec = item.get("section", "General")
        excerpt = item.get("source_excerpt", "")
        formatted_sources.append(f"Excerpt #{idx} [{doc} | {sec}]:\n{excerpt}")

    sources_str = "\n\n".join(formatted_sources) if formatted_sources else "No RAG excerpts available."

    return STRICT_GROUNDING_PROMPT_TEMPLATE.format(
        data_json=data_str,
        source_excerpts=sources_str
    )

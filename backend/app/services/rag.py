"""
AquaShield — RAG Retrieval Service with FAISS Indexing
Ingests standards documents (AWS, WQBA, VWBA), chunks text (500 char, 100 overlap),
indexes vectors into FAISS, and retrieves top-k relevant excerpts with source citations.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
import faiss

# Enforce UTF-8 output encoding for standard streams
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STANDARDS_DIR = Path(__file__).resolve().parent.parent / "data" / "standards"
INDEX_DIR = Path(__file__).resolve().parent.parent / "data" / "faiss_index"

# Global cache for FAISS index and chunk metadata
_faiss_index = None
_chunk_metadata: List[Dict] = []
_vocabulary: Dict[str, int] = {}
_idf: np.ndarray = np.array([])


def tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    return re.findall(r"\b\w+\b", text.lower())


def chunk_text(text: str, doc_name: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
    """
    Splits text into chunks of chunk_size with overlap.
    Extracts explicit section labels like [AWS Standard §3.1: ...] when present.
    """
    chunks = []
    lines = text.splitlines()
    current_section = f"{doc_name} Baseline"

    # Pre-parse section headers and content blocks
    section_blocks = []
    current_block = []

    for line in lines:
        line_str = line.strip()
        if not line_str or line_str.startswith("#"):
            continue
        if line_str.startswith("[") and "§" in line_str and "]" in line_str:
            if current_block:
                section_blocks.append((current_section, "\n".join(current_block)))
                current_block = []
            current_section = line_str.strip("[]")
        else:
            current_block.append(line_str)

    if current_block:
        section_blocks.append((current_section, "\n".join(current_block)))

    for section_name, block_text in section_blocks:
        if len(block_text) <= chunk_size:
            chunks.append({
                "source_doc": doc_name,
                "section": section_name,
                "excerpt": f"[{section_name}] {block_text}"
            })
        else:
            start = 0
            while start < len(block_text):
                end = start + chunk_size
                snippet = block_text[start:end]
                chunks.append({
                    "source_doc": doc_name,
                    "section": section_name,
                    "excerpt": f"[{section_name}] {snippet}"
                })
                start += (chunk_size - overlap)

    return chunks


def build_embeddings(chunks: List[Dict]) -> Tuple[np.ndarray, Dict[str, int], np.ndarray]:
    """Build TF-IDF normalized vector representations for chunks."""
    all_tokens = [tokenize(c["excerpt"]) for c in chunks]

    vocab = {}
    for tokens in all_tokens:
        for t in tokens:
            if t not in vocab:
                vocab[t] = len(vocab)

    num_docs = len(chunks)
    vocab_size = max(len(vocab), 1)
    tf_matrix = np.zeros((num_docs, vocab_size), dtype=np.float32)
    df = np.zeros(vocab_size, dtype=np.float32)

    for i, tokens in enumerate(all_tokens):
        token_counts = {}
        for t in tokens:
            token_counts[t] = token_counts.get(t, 0) + 1
        for t, count in token_counts.items():
            col = vocab[t]
            tf_matrix[i, col] = count / float(len(tokens) or 1)
            df[col] += 1

    # Compute IDF
    idf = np.log((1 + num_docs) / (1 + df)) + 1.0
    tfidf = tf_matrix * idf

    # L2 normalize
    norms = np.linalg.norm(tfidf, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = tfidf / norms

    return embeddings.astype(np.float32), vocab, idf


def initialize_faiss_index(force_rebuild: bool = False):
    """Loads or builds FAISS index over standards documents."""
    global _faiss_index, _chunk_metadata, _vocabulary, _idf

    if _faiss_index is not None and not force_rebuild:
        return

    STANDARDS_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    # Ingest text files from STANDARDS_DIR
    chunks = []
    for filepath in STANDARDS_DIR.glob("*.txt"):
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        doc_name = filepath.stem.replace("_", " ").title()
        chunks.extend(chunk_text(content, doc_name=doc_name, chunk_size=500, overlap=100))

    if not chunks:
        # Fallback inline default standards if standards directory was empty
        default_standards = """[AWS Standard §3.1: Sustainable Water Balance]
Where surface water availability exhibits a negative trend, facilities must reduce freshwater intake by at least 15% within 24 months.

[AWS Standard §3.2: Flood Risk Management]
Facilities in 100-year flood zones must construct flood barriers and maintain emergency stormwater discharge capacity.

[WQBA §2.0: Heavy Metal Discharge Limits]
Effluent concentrations for lead (Pb) shall not exceed 0.05 mg/L.
"""
        chunks.extend(chunk_text(default_standards, doc_name="AWS Standard", chunk_size=500, overlap=100))

    _chunk_metadata = chunks
    embeddings, _vocabulary, _idf = build_embeddings(chunks)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)

    _faiss_index = index
    print(f"[RAG] FAISS Index initialized with {index.ntotal} vectors across {len(chunks)} chunks.")


def retrieve_standards_excerpts(query_text: str, top_k: int = 3) -> List[Dict]:
    """
    Retrieves top_k relevant standards excerpts matching the query.
    Returns list of dicts: [{"source_doc": str, "section": str, "source_excerpt": str}]
    """
    initialize_faiss_index()

    tokens = tokenize(query_text)
    query_vec = np.zeros(len(_vocabulary), dtype=np.float32)

    token_counts = {}
    for t in tokens:
        if t in _vocabulary:
            token_counts[t] = token_counts.get(t, 0) + 1

    for t, count in token_counts.items():
        col = _vocabulary[t]
        query_vec[col] = (count / float(len(tokens) or 1)) * _idf[col]

    norm = np.linalg.norm(query_vec)
    if norm > 0:
        query_vec /= norm

    query_vec = np.expand_dims(query_vec, axis=0).astype(np.float32)

    k = min(top_k, _faiss_index.ntotal)
    distances, indices = _faiss_index.search(query_vec, k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(_chunk_metadata):
            chunk = _chunk_metadata[idx]
            results.append({
                "source_doc": chunk["source_doc"],
                "section": chunk["section"],
                "source_excerpt": chunk["excerpt"]
            })

    return results


if __name__ == "__main__":
    # Smoke test
    initialize_faiss_index(force_rebuild=True)
    res = retrieve_standards_excerpts("flood risk barriers", top_k=2)
    print("Smoke Test Results:")
    for r in res:
        print(f"  • [{r['source_doc']} | {r['section']}] {r['source_excerpt'][:80]}...")

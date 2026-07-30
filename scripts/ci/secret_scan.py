#!/usr/bin/env python3
"""
AquaShield CI/CD — Secret & Credential Leak Scanner
Scans repository files for committed API keys, private credentials, and tokens.
Exits with 0 if clean, 1 if secret leaks are detected.
"""

import sys
import re
from pathlib import Path

# Fix stdout encoding for Windows standard streams
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Regex patterns for detecting credentials and API keys
SECRET_PATTERNS = [
    (re.compile(r'(?i)AIzaSy[A-Za-z0-9_-]{33}'), "Google API Key"),
    (re.compile(r'(?i)GOOGLE_AI_STUDIO_API_KEY\s*=\s*["\']?[A-Za-z0-9_-]{20,}["\']?'), "Hardcoded Google AI Studio Key"),
    (re.compile(r'(?i)SUPABASE_(?:ANON|SERVICE_ROLE)_KEY\s*=\s*["\']?eyJ[A-Za-z0-9._-]{50,}["\']?'), "Hardcoded Supabase JWT Key"),
    (re.compile(r'(?i)ghp_[A-Za-z0-9]{36}'), "GitHub Personal Access Token"),
    (re.compile(r'(?i)gho_[A-Za-z0-9]{36}'), "GitHub OAuth Access Token"),
    (re.compile(r'(?i)AKIA[0-9A-Z]{16}'), "AWS Access Key ID"),
    (re.compile(r'-----BEGIN (?:RSA|OPENSSH|EC|PGP) PRIVATE KEY-----'), "Private Key Header"),
    (re.compile(r'(?i)bearer\s+eyJ[A-Za-z0-9._-]{50,}'), "Hardcoded Bearer Token"),
]

# File paths / directories to ignore during secret scan
IGNORED_PATHS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "env.example",
    "scripts/ci/secret_scan.py"
}

def scan_file(filepath: Path) -> list:
    findings = []
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        for idx, line in enumerate(lines, 1):
            # Skip comments mentioning example/placeholder keys
            if "example" in line.lower() or "your_" in line.lower() or "placeholder" in line.lower():
                continue
            for pattern, desc in SECRET_PATTERNS:
                matches = pattern.findall(line)
                if matches:
                    findings.append((filepath, idx, desc, line.strip()))
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
    return findings

def main():
    root = Path(__file__).resolve().parent.parent.parent
    findings = []

    print(f"[SCAN] Starting Secret Leak Scan in: {root}")

    for path in root.rglob("*"):
        if path.is_file():
            rel_path = path.relative_to(root)
            parts = set(rel_path.parts)
            if parts.intersection(IGNORED_PATHS):
                continue
            if str(rel_path) in IGNORED_PATHS:
                continue

            findings.extend(scan_file(path))

    if findings:
        print("\n[FAIL] SECURITY VIOLATION: Potential secret/credential leak(s) detected!\n")
        for filepath, line_num, desc, line_content in findings:
            masked = line_content[:15] + "..." if len(line_content) > 15 else line_content
            print(f"  * [{desc}] {filepath}:{line_num}")
            print(f"    Content snippet: {masked}\n")
        sys.exit(1)
    else:
        print("[OK] Secret Leak Scan Passed: No hardcoded secrets or API keys detected.")
        sys.exit(0)

if __name__ == "__main__":
    main()

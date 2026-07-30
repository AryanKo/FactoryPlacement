#!/usr/bin/env python3
"""
AquaShield — Live Gemma 4 Model Verification Script
Reads GOOGLE_AI_STUDIO_API_KEY from .env, calls Google AI Studio API,
and verifies live query execution against gemma-4-31b-it.
"""

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Load environment variables from .env
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMMA_MODEL_NAME = os.getenv("GEMMA_MODEL_NAME", "gemma-4-31b-it")
API_KEY = os.getenv("GOOGLE_AI_STUDIO_API_KEY") or os.getenv("GEMINI_API_KEY")


def verify_gemma_live_connection():
    print("=" * 70)
    print("🔍 AquaShield — Live Gemma 4 API Connection Diagnostic")
    print("=" * 70)
    print(f"• Target Model: {GEMMA_MODEL_NAME}")
    print(f"• Environment File: {env_path}")

    if not API_KEY or API_KEY.strip() == "":
        print("\n❌ STATUS: NO API KEY FOUND IN .env!")
        print("   To fix this:")
        print("   1. Create or open the .env file in project root.")
        print("   2. Add line: GOOGLE_AI_STUDIO_API_KEY=your_actual_key_here")
        print("   3. Run this script again: python scripts/test_gemma_live.py\n")
        print("=" * 70)
        return False

    masked_key = API_KEY[:6] + "..." + API_KEY[-4:] if len(API_KEY) > 10 else "***"
    print(f"• API Key Detected: {masked_key}")
    print("\n⏳ Sending live test query to Google AI Studio API...")

    try:
        from google import genai
        from google.genai import types

        start_time = time.time()
        client = genai.Client(api_key=API_KEY)

        response = client.models.generate_content(
            model=GEMMA_MODEL_NAME,
            contents="Say 'AquaShield Gemma 4 Live Connection Verified' in one sentence.",
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=100
            )
        )
        elapsed = time.time() - start_time

        if response and response.text:
            print("\n✅ SUCCESS: Gemma 4 Live Model Responded!")
            print(f"• Response Time: {elapsed:.2f} seconds")
            print(f"• Raw Response:\n  \"{response.text.strip()}\"\n")
            print("=" * 70)
            return True
        else:
            print("\n⚠️ WARNING: Model returned empty response.")
            print("=" * 70)
            return False

    except Exception as e:
        print(f"\n❌ ERROR: Live API Call Failed!")
        print(f"   Details: {e}\n")
        print("=" * 70)
        return False


if __name__ == "__main__":
    verify_gemma_live_connection()

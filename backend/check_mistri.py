"""Run `python check_mistri.py` in the backend folder to see exactly why Mistri is (not) answering."""
import os
import sys
import requests

from app import config  # loads backend/.env


def main():
    gemini_key = config.Config.GEMINI_API_KEY
    anthropic_key = config.Config.ANTHROPIC_API_KEY

    print("=== Ask Mistri Diagnostics ===")
    print("Gemini Model     :", config.Config.GEMINI_MODEL)
    print("Gemini API key   :", ("yes (%d chars, starts with %s...)" % (len(gemini_key), gemini_key[:6])) if gemini_key else "NOT SET - add GEMINI_API_KEY to backend/.env")
    print("Anthropic API key:", ("yes (%d chars, starts with %s...)" % (len(anthropic_key), anthropic_key[:7])) if anthropic_key else "none")

    if gemini_key:
        print("\nTesting Google Gemini API...")
        models = [config.Config.GEMINI_MODEL, *config.Config.GEMINI_FALLBACK_MODELS]
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": "Reply with 'OK'"}]}],
                "generationConfig": {"maxOutputTokens": 20}
            }
            try:
                r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
                if r.status_code == 200:
                    data = r.json()
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])
                    print(f"[{model}] SUCCESS -> {parts[0].get('text', '').strip()}")
                    return 0
                else:
                    print(f"[{model}] FAILED (HTTP {r.status_code}): {r.text[:150]}")
            except Exception as e:
                print(f"[{model}] ERROR: {e}")
        return 1

    if not anthropic_key:
        print("\nPlease add GEMINI_API_KEY to civora-platform/backend/.env to enable Mistri.")
        return 1

    print("\nFalling back to Anthropic testing...")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key, timeout=20.0, max_retries=0)
        for model in [config.Config.ANTHROPIC_MODEL, *config.Config.ANTHROPIC_FALLBACK_MODELS]:
            try:
                r = client.messages.create(model=model, max_tokens=20, messages=[{"role": "user", "content": "Say OK"}])
                print(f"[{model}] works ->", "".join(b.text for b in r.content if b.type == "text").strip())
                return 0
            except Exception as e:
                print(f"[{model}] FAILED: {type(e).__name__}: {e}")
    except Exception as e:
        print("Anthropic test error:", e)
    return 1


if __name__ == "__main__":
    sys.exit(main())

import json
import re

from flask import current_app, jsonify, request
import requests

from .routes import api, fail, get_db, model_json

SYSTEM = (
    "You are Mistri (Hindi for a skilled builder), the assistant inside CIVORA AI, a civil plan analyzer for Indian homes. "
    "Flow: create a project, upload a plan, then use the Structure Plan Analyzer (floors and plan area read from the drawing; code checks stay Not Evaluated), the Cost Estimation Analyzer (floors and area times a user-entered "
    "rate per sq ft, shown as a total with a range; no rate is assumed) or the Vastu Plan Analyzer (eight directional zones, "
    "user-confirmed north, traditional rules). Missing data is shown as Not provided, never guessed. Outputs are preliminary and "
    "not certified. You may explain civil terms and Indian codes (IS 456, 875, 1893, 13920, NBC 2016) simply. Never invent prices "
    "or say a building is safe or approved; send real decisions to a licensed engineer. Politely decline unrelated topics. "
    "Reply in the language the user writes in. Plain text only, under 120 words."
)


def clean_messages(raw):
    if not isinstance(raw, list):
        return []
    msgs = []
    for m in raw[-10:]:
        if isinstance(m, dict) and m.get("role") in ("user", "assistant", "model") and isinstance(m.get("content"), str):
            text = m["content"].strip()[:1000]
            if text:
                role = "user" if m.get("role") == "user" else "assistant"
                msgs.append({"role": role, "content": text})
    while msgs and msgs[0]["role"] != "user":
        msgs.pop(0)
    return msgs if msgs and msgs[-1]["role"] == "user" else []


class AssistantError(Exception):
    """A failure with a message that is safe and useful to show in the chat."""

    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def explain_anthropic(exc):
    """Map an Anthropic SDK error to what the person should do about it."""
    try:
        import anthropic
        text = str(exc).lower()
        if isinstance(exc, anthropic.AuthenticationError):
            return "Mistri's API key was rejected. Check API key in backend/.env and restart the backend."
        if isinstance(exc, anthropic.PermissionDeniedError):
            return "This API key is not allowed to use the selected model. Check key permissions."
        if isinstance(exc, anthropic.NotFoundError):
            return "The selected model was not found for this API key."
        if isinstance(exc, anthropic.RateLimitError):
            return "Mistri is getting too many requests right now. Try again in a minute."
        if isinstance(exc, anthropic.APIConnectionError):
            return "The server cannot reach the AI service. Check internet connection, proxy or firewall."
        if "credit balance" in text or "billing" in text:
            return "The account behind this key has no credit left."
    except Exception:
        pass
    return "AI service returned an error. See the backend log for details."


def call_gemini(messages, system=None):
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise AssistantError("Mistri is not configured. Add GEMINI_API_KEY to backend/.env and restart the backend.", 503)

    models = [
        current_app.config.get("GEMINI_MODEL") or "gemini-2.5-flash",
        *current_app.config.get("GEMINI_FALLBACK_MODELS", []),
    ]
    unique_models = []
    seen = set()
    for m in models:
        m = (m or "").strip()
        if m and m not in seen:
            seen.add(m)
            unique_models.append(m)

    # Format contents for Gemini: [{"role": "user"|"model", "parts": [{"text": ...}]}]
    contents = []
    last_role = None
    for m in messages:
        role = "user" if m.get("role") == "user" else "model"
        text = (m.get("content") or "").strip()
        if not text:
            continue
        if role == last_role and contents:
            contents[-1]["parts"][0]["text"] += "\n" + text
        else:
            contents.append({"role": role, "parts": [{"text": text}]})
            last_role = role

    if not contents or contents[0]["role"] != "user":
        raise AssistantError("No valid user question was provided.", 400)

    payload = {
        "contents": contents,
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 600,
        },
    }
    sys_instruction = (system or SYSTEM).strip()
    if sys_instruction:
        payload["system_instruction"] = {
            "parts": [{"text": sys_instruction}]
        }

    last_error = None
    for model in unique_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=35)
        except requests.exceptions.Timeout:
            last_error = AssistantError("Connection to Google Gemini timed out. Please try again.", 504)
            continue
        except requests.exceptions.RequestException as e:
            current_app.logger.warning("Gemini network error: %s", e)
            last_error = AssistantError("Cannot reach Google Gemini API. Check your internet connection.", 502)
            continue

        if resp.status_code == 200:
            try:
                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    block_reason = data.get("promptFeedback", {}).get("blockReason")
                    if block_reason:
                        raise AssistantError(f"Gemini response was blocked by safety policy ({block_reason}). Please rephrase.", 400)
                    raise AssistantError("Mistri sent an empty answer. Please ask again.")
                parts = candidates[0].get("content", {}).get("parts") or []
                reply_text = "".join(p.get("text", "") for p in parts).strip()
                if not reply_text:
                    raise AssistantError("Mistri sent an empty answer. Please ask again.")
                return reply_text
            except AssistantError:
                raise
            except Exception as e:
                current_app.logger.exception("Failed parsing Gemini JSON response: %s", resp.text[:200])
                last_error = AssistantError("Unexpected response format from Gemini.", 502)
                continue
        elif resp.status_code == 404:
            current_app.logger.warning("Gemini model %s not found (404), trying fallback", model)
            last_error = AssistantError(f"Gemini model '{model}' was not found. Check GEMINI_MODEL in backend/.env.", 502)
            continue
        elif resp.status_code in (401, 403):
            err_msg = "Mistri's Gemini API key was rejected or invalid. Check GEMINI_API_KEY in backend/.env and restart the backend."
            try:
                detail = resp.json().get("error", {}).get("message", "")
                if "quota" in detail.lower() or "limit" in detail.lower():
                    err_msg = "Gemini API quota exceeded or disabled. Check your Google AI Studio quota."
            except Exception:
                pass
            raise AssistantError(err_msg, 502)
        elif resp.status_code == 429:
            raise AssistantError("Gemini rate limit reached or quota exhausted. Please try again in a minute.", 429)
        else:
            try:
                detail = resp.json().get("error", {}).get("message", "")
            except Exception:
                detail = resp.text[:120]
            current_app.logger.warning("Gemini API error (%d): %s", resp.status_code, detail)
            last_error = AssistantError(f"Gemini API returned error: {detail or resp.status_code}", 502)

    if last_error:
        raise last_error
    raise AssistantError("Failed to get response from Gemini API.", 502)


def call_anthropic(messages, system=None):
    try:
        import anthropic
    except ImportError as e:
        raise AssistantError("The 'anthropic' Python package is not installed.") from e

    client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"], timeout=40.0, max_retries=1)
    models = [current_app.config["ANTHROPIC_MODEL"], *current_app.config.get("ANTHROPIC_FALLBACK_MODELS", [])]
    last = None
    for model in models:
        try:
            resp = client.messages.create(model=model, max_tokens=500, system=system or SYSTEM, messages=messages)
        except anthropic.NotFoundError as e:
            current_app.logger.warning("Assistant model %s not found: %s", model, e)
            last = e
            continue
        except Exception as e:
            current_app.logger.exception("Assistant call failed (model %s)", model)
            raise AssistantError(explain_anthropic(e)) from e
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not text:
            raise AssistantError("Mistri sent an empty answer. Please ask again.")
        return text
    raise AssistantError(explain_anthropic(last)) from last


def call_model(messages, system=None):
    if current_app.config.get("GEMINI_API_KEY"):
        return call_gemini(messages, system=system)
    elif current_app.config.get("ANTHROPIC_API_KEY"):
        return call_anthropic(messages, system=system)
    else:
        raise AssistantError("Mistri is not configured. Add GEMINI_API_KEY to backend/.env and restart the backend.", 503)


_PAGES = {
    "structure": "Structure Plan Analyzer",
    "cost": "Cost Estimation Analyzer",
    "vastu": "Vastu Plan Analyzer",
    "home": "Project home",
}


def context_for(project_id, page):
    """A short, factual description of the open project so Mistri can answer 'this analyzer' questions."""
    if not project_id or not re.fullmatch(r"[0-9a-f]{12}", str(project_id)):
        return ""
    if get_db().execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone() is None:
        return ""
    m = model_json(project_id)
    eff, rd = m["effective"], m["reading"]
    bits = []
    for key, label in (
        ("floors", "floors"),
        ("area", "plan area per floor (sq ft)"),
        ("zone", "seismic zone"),
        ("soil", "soil"),
        ("grade", "concrete grade"),
        ("rate", "rate per sq ft"),
        ("north", "north points"),
    ):
        if eff.get(key) not in (None, ""):
            origin = m["sources"]["fields"].get(key)
            bits.append(f"{label}: {eff[key]}" + (" (read from the drawing)" if origin == "drawing" else ""))
    if eff.get("rooms"):
        bits.append("vastu rooms: " + ", ".join(f"{r} in {z}" for r, z in eff["rooms"].items()))
    page_name = _PAGES.get(page, "")
    out = "\n\nThe user is looking at: " + (page_name or "a project") + "."
    out += f" Drawing reading: {rd['state']}" + (f" ({rd['status']})" if rd.get("status") else "") + "."
    if bits:
        out += " Current project values: " + "; ".join(bits) + "."
    if rd.get("warnings"):
        out += " Reader warnings: " + " ".join(rd["warnings"][:3])
    return out


@api.post("/assistant")
def assistant():
    if not (current_app.config.get("GEMINI_API_KEY") or current_app.config.get("ANTHROPIC_API_KEY")):
        return fail("Mistri is not configured. Add GEMINI_API_KEY to backend/.env and restart the backend.", 503)
    body = request.get_json(silent=True) or {}
    msgs = clean_messages(body.get("messages"))
    if not msgs:
        return fail("messages must be a non-empty array of {role, content}", 400)
    system = SYSTEM
    try:
        system += context_for(body.get("project_id"), body.get("page"))
    except Exception:
        current_app.logger.exception("Could not build assistant context")
    try:
        reply = call_model(msgs, system)
    except AssistantError as e:
        return fail(str(e), e.status)
    except Exception:
        current_app.logger.exception("Assistant failed")
        return fail("Mistri could not answer right now. See the backend log for details.", 502)
    return jsonify({"reply": reply})

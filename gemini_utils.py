"""
gemini_utils.py — Gemini API wrapper for News Bias Analyzer.

Uses the current google-genai SDK (not the deprecated google-generativeai).
Model: gemini-2.0-flash

Design contract:
  - call_json() NEVER returns a fallback — it raises GeminiError on any failure.
  - Error messages are human-readable and never expose the API key value.
  - get_debug_info() gives the UI safe diagnostics for the debug expander.
"""

import json
import os
import re
import time
from typing import Any, Dict, Optional

from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
_MODEL_NAME: str = "gemini-2.0-flash"

# Module-level state
_client = None          # google.genai.Client, lazily created
_model_init_error: str = ""
_last_call_error: str = ""
_last_raw_response: str = ""


# ── Custom exception ──────────────────────────────────────────────────────────

class GeminiError(Exception):
    """
    Raised whenever a Gemini API operation fails for any reason.

    Attributes
    ----------
    raw_response : The raw text the model returned (if any), used in the
                   debug expander so the user can see what went wrong.
    """
    def __init__(self, message: str, raw_response: str = ""):
        super().__init__(message)
        self.raw_response = raw_response


# ── Client initialisation ─────────────────────────────────────────────────────

def _get_client():
    """
    Lazily create and cache the google.genai.Client.

    Raises GeminiError if:
    - GEMINI_API_KEY is missing from .env
    - The client cannot be created
    """
    global _client, _model_init_error

    if _client is not None:
        return _client

    if not _API_KEY:
        _model_init_error = "GEMINI_API_KEY not found in environment"
        raise GeminiError(
            "GEMINI_API_KEY is missing. "
            "Add it to your .env file:  GEMINI_API_KEY=your_key_here"
        )

    try:
        from google import genai
        _client = genai.Client(api_key=_API_KEY)
        return _client
    except Exception as exc:
        _model_init_error = str(exc)
        raise GeminiError(f"Failed to create Gemini client: {exc}")


# ── JSON parsing helpers ──────────────────────────────────────────────────────

def _parse_json(text: str) -> Optional[Dict]:
    """
    Try three strategies to extract a JSON object from text.
    Returns the parsed dict, or None if all strategies fail.
    """
    # 1 — direct parse (works when JSON mode is active)
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    # 2 — strip markdown code fences and retry
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    # 3 — extract the first top-level { … } block
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return None


# ── Error classification ──────────────────────────────────────────────────────

def _friendly_error(exc: Exception) -> str:
    """
    Return a human-readable error string.
    Never includes the API key value.
    """
    s = str(exc).lower()

    if "429" in s or "resource_exhausted" in s or "quota" in s:
        # UI requirement: show one exact, beginner-friendly message.
        return "Gemini rate limit reached. Wait about 1 minute and try again."

    if "401" in s or "permission_denied" in s or "invalid api key" in s or "api_key_invalid" in s:
        return (
            "Invalid or unauthorised API key (HTTP 401 / PERMISSION_DENIED). "
            "Check that GEMINI_API_KEY in your .env file is correct."
        )

    if "404" in s or "not found" in s:
        return (
            f"Model '{_MODEL_NAME}' not found (HTTP 404). "
            "Run `pip install --upgrade google-genai` and try again."
        )

    # Generic fallback — truncate to avoid leaking key fragments
    return f"Gemini API error: {str(exc)[:200]}"


# ── Public API ────────────────────────────────────────────────────────────────

def call_json(prompt: str, retries: int = 2) -> Dict[str, Any]:
    """
    Send a prompt to Gemini and return a parsed JSON dict.

    Uses response_mime_type="application/json" so the model is forced to
    return valid JSON at the API level — no markdown, no preamble.

    Raises GeminiError on any failure (never returns a fallback dict).

    Parameters
    ----------
    prompt  : Prompt text.  JSON-structure instructions are already in
              the prompts in analyzer.py; this function appends a short
              hard reminder as an extra safety net.
    retries : Extra attempts after the first before giving up.
    """
    global _last_call_error, _last_raw_response

    client = _get_client()  # raises GeminiError if init failed

    from google.genai import types

    # Append a hard JSON constraint so even without JSON mode
    # the model knows what we want
    full_prompt = (
        prompt.rstrip()
        + "\n\nREQUIRED: Return ONLY a valid JSON object. "
        "Start with { and end with }. No markdown, no explanation, no extra text."
    )

    raw = ""
    for attempt in range(retries + 1):
        try:
            response = client.models.generate_content(
                model=_MODEL_NAME,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            raw = response.text or ""
            _last_raw_response = raw[:500]

            parsed = _parse_json(raw)
            if parsed is not None:
                return parsed

            # Got a response but couldn't parse it as JSON
            # Retry once with a stricter re-prompt
            if attempt < retries:
                full_prompt = (
                    "Your previous response could not be parsed as JSON.\n"
                    "Return ONLY the JSON object. Start with { end with }.\n\n"
                    + prompt
                )
                time.sleep(0.5)
                continue

            _last_call_error = f"JSON parse failed. Response: {raw[:300]}"
            raise GeminiError(
                f"Gemini returned an invalid JSON response after "
                f"{retries + 1} attempt(s).\n\n"
                "Expand the API Debug section below for the raw response.",
                raw_response=raw[:500],
            )

        except GeminiError:
            raise  # already a clean error — pass through

        except Exception as exc:
            err_msg = _friendly_error(exc)
            _last_call_error = err_msg
            if attempt < retries and "429" not in str(exc) and "quota" not in str(exc).lower():
                time.sleep(1.5 * (attempt + 1))
                continue
            raise GeminiError(err_msg, raw_response=raw[:500])

    raise GeminiError("Unexpected failure in call_json.")  # should not reach here


def test_connection() -> str:
    """
    Minimal test call to verify the API key and model are reachable.
    Returns "ok" on success, raises GeminiError on failure.
    """
    result = call_json(
        f'Return this exact JSON (do not change it): {{"status": "ok", "model": "{_MODEL_NAME}"}}'
    )
    if isinstance(result, dict) and result.get("status") == "ok":
        return "ok"
    raise GeminiError(f"Unexpected response from test call: {result}")


def get_debug_info() -> Dict[str, Any]:
    """
    Return safe diagnostic information for the debug expander.
    Never reveals the API key value — only its presence and length.
    """
    key = _API_KEY or ""
    return {
        "key_present":       bool(key),
        "key_length":        len(key),
        "key_preview":       f"…{key[-4:]}" if len(key) >= 8 else "(too short to be valid)",
        "model_name":        _MODEL_NAME,
        "sdk_package":       "google-genai (current)",
        "client_ready":      _client is not None,
        "model_init_error":  _model_init_error,
        "last_call_error":   _last_call_error,
        "last_raw_response": _last_raw_response,
    }

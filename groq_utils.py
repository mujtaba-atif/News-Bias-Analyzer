"""
groq_utils.py — Groq API wrapper for News Bias Analyzer.

Model calls are made through the official `groq` Python package.

Design contract:
  - call_json() NEVER returns a fallback — it raises GroqError on any failure.
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
_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
# Single source of truth for model selection.
# Override by setting GROQ_MODEL in your `.env` (recommended for easy experimentation).
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Module-level state
_client = None
_client_init_error: str = ""
_last_call_error: str = ""
_last_raw_response: str = ""


class GroqError(Exception):
    """
    Raised whenever a Groq API operation fails for any reason.

    Attributes
    ----------
    raw_response : Raw model text returned (if any), used in debug UI.
    """

    def __init__(self, message: str, raw_response: str = ""):
        super().__init__(message)
        self.raw_response = raw_response


def _get_client():
    global _client, _client_init_error

    if _client is not None:
        return _client

    if not _API_KEY:
        _client_init_error = "GROQ_API_KEY not found in environment"
        raise GroqError(
            "GROQ_API_KEY is missing. Add it to your `.env` file:  GROQ_API_KEY=your_key_here"
        )

    try:
        from groq import Groq

        _client = Groq(api_key=_API_KEY)
        return _client
    except Exception as exc:
        _client_init_error = str(exc)
        raise GroqError(f"Failed to create Groq client: {exc}")


def _parse_json(text: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        pass

    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def _friendly_error(exc: Exception) -> str:
    s = str(exc).lower()
    if "429" in s or "rate limit" in s:
        return "Groq rate limit reached. Wait about 1 minute and try again."
    if "401" in s or "unauthorized" in s or "invalid api key" in s:
        return "Invalid or unauthorised API key (HTTP 401). Check that GROQ_API_KEY in your .env file is correct."
    return f"Groq API error: {str(exc)[:200]}"


def call_json(prompt: str, retries: int = 1) -> Dict[str, Any]:
    """
    Send a prompt and return a parsed JSON dict.

    Uses response_format={"type":"json_object"} when supported by the API.
    Raises GroqError on any failure (never returns a fallback dict).
    """
    global _last_call_error, _last_raw_response

    client = _get_client()

    full_prompt = (
        prompt.rstrip()
        + "\n\nREQUIRED: Return ONLY a valid JSON object. Start with { and end with }. No markdown, no extra text."
    )

    raw = ""
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a careful assistant that outputs strict JSON only."},
                    {"role": "user", "content": full_prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            raw = (resp.choices[0].message.content or "").strip()
            _last_raw_response = raw[:500]

            parsed = _parse_json(raw)
            if parsed is not None:
                return parsed

            _last_call_error = f"JSON parse failed. Response: {raw[:300]}"
            raise GroqError(
                "Groq returned an invalid JSON response. Expand the debug section for the raw response.",
                raw_response=raw[:500],
            )

        except GroqError:
            raise
        except Exception as exc:
            msg = _friendly_error(exc)
            _last_call_error = msg
            if attempt < retries and "429" not in str(exc):
                time.sleep(1.25 * (attempt + 1))
                continue
            raise GroqError(msg, raw_response=raw[:500])

    raise GroqError("Unexpected failure in call_json().")


def test_connection() -> str:
    result = call_json('Return this exact JSON: {"status":"ok"}', retries=0)
    if isinstance(result, dict) and result.get("status") == "ok":
        return "ok"
    raise GroqError(f"Unexpected response from test call: {result}")


def get_debug_info() -> Dict[str, Any]:
    key = _API_KEY or ""
    return {
        "key_present": bool(key),
        "key_length": len(key),
        "key_preview": f"…{key[-4:]}" if len(key) >= 8 else "(too short to be valid)",
        "model_name": GROQ_MODEL,
        "sdk_package": "groq",
        "client_ready": _client is not None,
        "client_init_error": _client_init_error,
        "last_call_error": _last_call_error,
        "last_raw_response": _last_raw_response,
    }


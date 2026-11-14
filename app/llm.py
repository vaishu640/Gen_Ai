import json
import os
import requests
from dotenv import load_dotenv

load_dotenv()


class LLMError(Exception):
    pass


def _groq(system, user):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is missing in .env")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    try:
        r = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": "Bearer " + key},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.2,
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as error:
        raise LLMError("Groq request failed: " + str(error))
    except (KeyError, IndexError, ValueError):
        raise LLMError("Groq sent an unexpected reply")


def _gemini(system, user):
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is missing in .env")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + model + ":generateContent")
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.2},
    }
    try:
        r = requests.post(url, headers={"x-goog-api-key": key},
                          json=body, timeout=30)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except requests.exceptions.RequestException as error:
        raise LLMError("Gemini request failed: " + str(error))
    except (KeyError, IndexError, ValueError):
        raise LLMError("Gemini sent an unexpected reply")


PROVIDERS = {"groq": _groq, "gemini": _gemini}


def ask_llm(system, user, provider=None):
    provider = provider or os.getenv("LLM_PROVIDER", "groq")
    if provider not in PROVIDERS:
        raise LLMError("Unknown provider: " + provider)
    return PROVIDERS[provider](system, user)


def parse_json_reply(text):
    data = {}
    json_ok = False
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(text[start:end + 1])
            json_ok = True
        except ValueError:
            data = {}

    confidence = str(data.get("confidence") or "low").lower()
    if confidence not in ("high", "medium", "low"):
        confidence = "low"

    return {
        "answer": str(data.get("answer") or text.strip()),
        "confidence": confidence,
        "follow_up": str(data.get("follow_up") or ""),
        "json_ok": json_ok,
    }
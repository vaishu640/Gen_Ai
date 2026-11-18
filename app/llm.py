import json
import os
import time
from pathlib import Path
import requests
from dotenv import load_dotenv

# always use the .env at the main level (next to requirements.txt)
load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)


class LLMError(Exception):
    pass


def _groq(system, user):
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise LLMError("GROQ_API_KEY is missing in .env")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    last_error = None
    for attempt in range(4):
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
                timeout=60,
            )
            if r.status_code == 429:                  # rate limit: wait, then try again
                last_error = "429 Too Many Requests (free tier rate limit)"
                try:
                    wait = float(r.headers.get("retry-after", 15))
                except ValueError:
                    wait = 15
                time.sleep(min(max(wait, 5), 30))
                continue
            if r.status_code != 200:                  # show Groq's own explanation
                raise LLMError("Groq error " + str(r.status_code) + ": " + r.text[:600])
            return r.json()["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError as error:
            last_error = error                        # connection was cut: wait, then try again
            time.sleep(3)
        except requests.exceptions.RequestException as error:
            raise LLMError("Groq request failed: " + str(error))
        except (KeyError, IndexError, ValueError):
            raise LLMError("Groq sent an unexpected reply")
    raise LLMError("Groq request failed: " + str(last_error))


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
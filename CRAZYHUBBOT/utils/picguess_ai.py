"""
Optional AI-generated word content for the picture-guess game.

This is entirely optional and safe-by-default: if GEMINI_API_KEY isn't
set, or the API call fails for any reason, or the response doesn't
pass validation, this returns an empty list and picguess_bank.py
silently falls back to its curated word list. Nothing here can ever
break the game or send unvalidated content to a group — every word is
checked (letters only, sane length) before it's ever used.

Get a free key at https://aistudio.google.com/apikey and set it as
the GEMINI_API_KEY environment variable to turn this on.
"""

import json
import logging
import os
import re

import aiohttp

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-3.6-flash:generateContent"
)

_WORD_RE = re.compile(r"^[a-z]{3,15}$")


async def ai_generate_words(count: int = 15, avoid: list = None) -> list:
    """Asks Gemini for a batch of single-word names (movies, actors,
    cricketers, animals, cities, etc.) for the scramble-and-guess game.
    Returns a list of validated lowercase words, or [] on any failure —
    callers must always have a non-AI fallback ready."""
    if not GEMINI_API_KEY:
        logger.info("[picguess AI] GEMINI_API_KEY not set — using curated word list only.")
        return []

    avoid = avoid or []
    avoid_text = ", ".join(avoid[:30]) if avoid else "none"
    prompt = (
        f"Give me {count} different single-word names suitable for a "
        f"word-scramble guessing game in a Telegram group — mix categories: "
        f"movies, actors, cricketers, animals, fruits, cities, festivals. "
        f"Rules: each must be ONE word only, letters only (no spaces, "
        f"numbers, hyphens, or punctuation), 3 to 15 letters long, and a "
        f"real recognizable word or name — nothing offensive or obscure. "
        f"Do not repeat any of these: {avoid_text}."
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 1024,
            # Forces Gemini to return only a valid JSON array of strings —
            # no markdown fences, no extra prose to accidentally break
            # parsing. This is the officially supported structured-output
            # mode, not just a prompt instruction.
            "responseMimeType": "application/json",
            "responseSchema": {"type": "ARRAY", "items": {"type": "STRING"}},
        },
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(
                        f"[picguess AI] Gemini API returned {resp.status}: {body[:200]}"
                    )
                    return []
                data = await resp.json()
    except Exception as e:
        logger.warning(
            f"[picguess AI] Gemini API call failed: {type(e).__name__}: {e}"
        )
        return []

    try:
        candidate = data["candidates"][0]
        # Concatenate all parts' text, in case the response is split
        # across multiple parts (some models include extra parts).
        text = "".join(
            p.get("text", "") for p in candidate["content"]["parts"]
        ).strip()
        if not text:
            finish_reason = candidate.get("finishReason", "unknown")
            logger.warning(
                f"[picguess AI] Gemini returned no text (finishReason={finish_reason})."
            )
            return []
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        try:
            raw_words = json.loads(text)
        except Exception:
            # Last-resort fallback: pull out the first [...] block in
            # case there's stray text around the JSON despite the
            # structured-output config.
            match = re.search(r"\[.*\]", text, flags=re.DOTALL)
            if not match:
                raise
            raw_words = json.loads(match.group(0))
    except Exception as e:
        finish_reason = None
        try:
            finish_reason = data["candidates"][0].get("finishReason")
        except Exception:
            pass
        logger.warning(
            f"[picguess AI] Couldn't parse Gemini's response: {type(e).__name__}: {e} "
            f"(finishReason={finish_reason})"
        )
        return []

    if not isinstance(raw_words, list):
        logger.warning("[picguess AI] Gemini's response wasn't a JSON list — ignoring it.")
        return []

    validated = []
    for w in raw_words:
        if not isinstance(w, str):
            continue
        w = w.strip().lower()
        if _WORD_RE.match(w) and w not in validated:
            validated.append(w)

    if validated:
        logger.info(f"[picguess AI] Got {len(validated)} AI-generated words from Gemini.")
    else:
        logger.warning("[picguess AI] Gemini responded but no words passed validation.")
    return validated

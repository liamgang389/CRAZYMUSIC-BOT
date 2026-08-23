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
    "gemini-2.0-flash:generateContent"
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
        f"Do not repeat any of these: {avoid_text}. "
        f"Reply with ONLY a JSON array of lowercase strings, nothing else, "
        f'no markdown. Example: ["pushpa","kohli","mumbai"]'
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.9, "maxOutputTokens": 400},
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    logger.warning(
                        f"[picguess AI] Gemini API returned {resp.status}: {body[:200]}"
                    )
                    return []
                data = await resp.json()
    except Exception as e:
        logger.warning(f"[picguess AI] Gemini API call failed: {e}")
        return []

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
        raw_words = json.loads(text)
    except Exception as e:
        logger.warning(f"[picguess AI] Couldn't parse Gemini's response: {e}")
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

"""
Server-side text-to-speech through ElevenLabs.

The API key never reaches the browser: the frontend posts text here and gets MP3 audio
back. Without ELEVENLABS_API_KEY the frontend falls back to the browser's own voices.

Note: the text (assistant answers) is sent to ElevenLabs. That is fine for this demo's
fictional data; a real deployment needs a data-processing agreement first.
"""

import os
import re
import logging
from collections import OrderedDict
from typing import Optional

import httpx

logger = logging.getLogger("swasthyasetu.tts")

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
DEFAULT_VOICE_ID = "NOpBlnGInO9m6vDvFkFC"
DEFAULT_MODEL_ID = "eleven_v4"  # supports Hindi and Marathi
MAX_CHARS = 1500

_cache: "OrderedDict[tuple, bytes]" = OrderedDict()
_CACHE_SIZE = 64


class TTSError(Exception):
    pass


def enabled() -> bool:
    return bool(os.getenv("ELEVENLABS_API_KEY"))


def clean_text(text: str) -> str:
    """Drop the English 'Sources:' line and reference titles so the voice reads the answer itself."""
    lines = [l for l in text.splitlines() if not re.match(r"^\s*(Sources|स्रोत):", l)]
    text = " ".join(lines)
    text = re.sub(r"\([A-Za-z0-9 :,&'/-]+\)", "", text)
    return re.sub(r"\s+", " ", text).strip()[:MAX_CHARS]


def synthesize(text: str, language: str) -> bytes:
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise TTSError("ElevenLabs is not configured")
    text = clean_text(text)
    if not text:
        raise TTSError("Nothing to read")
    lang = language if language in ("hi", "mr", "en") else "en"
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID)
    model_id = os.getenv("ELEVENLABS_MODEL_ID", DEFAULT_MODEL_ID)

    cache_key = (voice_id, model_id, lang, text)
    if cache_key in _cache:
        _cache.move_to_end(cache_key)
        return _cache[cache_key]

    try:
        res = httpx.post(
            API_URL.format(voice_id=voice_id),
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": key, "accept": "audio/mpeg"},
            json={"text": text, "model_id": model_id, "language_code": lang},
            timeout=45.0,
        )
    except httpx.HTTPError as e:
        logger.warning("ElevenLabs unreachable: %s", e)
        raise TTSError("Could not reach ElevenLabs")

    if res.status_code != 200:
        detail: Optional[str] = None
        try:
            body = res.json()
            detail = body.get("detail", {}).get("message") if isinstance(body.get("detail"), dict) else str(body.get("detail"))
        except ValueError:
            pass
        logger.warning("ElevenLabs error %s: %s", res.status_code, detail)
        raise TTSError(f"ElevenLabs error {res.status_code}" + (f": {detail}" if detail else ""))

    _cache[cache_key] = res.content
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)
    return res.content

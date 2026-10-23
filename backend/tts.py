"""
Server-side text-to-speech through ElevenLabs.

The API key never reaches the browser: the frontend posts text here and gets MP3 audio
back. Without ELEVENLABS_API_KEY the frontend falls back to the browser's own voices.

Note: the text (assistant answers) is sent to ElevenLabs. That is fine for this demo's
fictional data; a real deployment needs a data-processing agreement first.
"""

import os
import re
import time
import uuid
import logging
from collections import OrderedDict
from typing import Optional, Iterator

import httpx

logger = logging.getLogger("swasthyasetu.tts")

API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"  # "Sarah", a built-in voice free accounts can use
DEFAULT_MODEL_ID = "eleven_v4_turbo"  # supports Hindi and Marathi; ~40% faster than eleven_v4
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


def _settings(language: str):
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        raise TTSError("ElevenLabs is not configured")
    lang = language if language in ("hi", "mr", "en") else "en"
    return key, lang, os.getenv("ELEVENLABS_VOICE_ID", DEFAULT_VOICE_ID), os.getenv("ELEVENLABS_MODEL_ID", DEFAULT_MODEL_ID)


def _error_from(res: httpx.Response) -> TTSError:
    detail: Optional[str] = None
    try:
        body = res.json()
        detail = body.get("detail", {}).get("message") if isinstance(body.get("detail"), dict) else str(body.get("detail"))
    except ValueError:
        pass
    logger.warning("ElevenLabs error %s: %s", res.status_code, detail)
    return TTSError(f"ElevenLabs error {res.status_code}" + (f": {detail}" if detail else ""))


def _remember(cache_key: tuple, audio: bytes):
    _cache[cache_key] = audio
    if len(_cache) > _CACHE_SIZE:
        _cache.popitem(last=False)


def synthesize(text: str, language: str) -> bytes:
    """Whole MP3 in one response."""
    key, lang, voice_id, model_id = _settings(language)
    text = clean_text(text)
    if not text:
        raise TTSError("Nothing to read")
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
        raise _error_from(res)
    _remember(cache_key, res.content)
    return res.content


# Streaming: the browser's <audio> element can start playing while ElevenLabs is still
# generating, but it cannot send our auth header. So a signed-in POST registers the text
# and returns a short-lived, single-use id that the audio element then fetches.
_pending: "OrderedDict[str, tuple]" = OrderedDict()
_PENDING_TTL = 300


def prepare(text: str, language: str) -> str:
    _settings(language)  # fail early if not configured
    text = clean_text(text)
    if not text:
        raise TTSError("Nothing to read")
    now = time.time()
    for k in [k for k, v in _pending.items() if now - v[2] > _PENDING_TTL]:
        _pending.pop(k, None)
    clip_id = uuid.uuid4().hex
    _pending[clip_id] = (text, language, now)
    return clip_id


def open_stream(clip_id: str) -> Iterator[bytes]:
    """Start the ElevenLabs stream (raising TTSError before any audio is sent) and return a chunk iterator."""
    item = _pending.pop(clip_id, None)
    if not item or time.time() - item[2] > _PENDING_TTL:
        raise TTSError("Audio link expired")
    text, language, _ = item
    key, lang, voice_id, model_id = _settings(language)
    cache_key = (voice_id, model_id, lang, text)
    if cache_key in _cache:
        return iter([_cache[cache_key]])

    client = httpx.Client(timeout=httpx.Timeout(60.0, connect=10.0))
    try:
        request = client.build_request(
            "POST", API_URL.format(voice_id=voice_id) + "/stream",
            params={"output_format": "mp3_44100_128"},
            headers={"xi-api-key": key, "accept": "audio/mpeg"},
            json={"text": text, "model_id": model_id, "language_code": lang},
        )
        res = client.send(request, stream=True)
    except httpx.HTTPError as e:
        client.close()
        logger.warning("ElevenLabs unreachable: %s", e)
        raise TTSError("Could not reach ElevenLabs")
    if res.status_code != 200:
        res.read()
        err = _error_from(res)
        res.close()
        client.close()
        raise err

    def chunks() -> Iterator[bytes]:
        audio = bytearray()
        complete = False
        try:
            for chunk in res.iter_bytes():
                audio.extend(chunk)
                yield chunk
            complete = True
        finally:
            res.close()
            client.close()
            if complete:
                _remember(cache_key, bytes(audio))

    return chunks()


# ----------------- Speech-to-text (ElevenLabs Scribe) -----------------
STT_URL = "https://api.elevenlabs.io/v1/speech-to-text"
STT_MODEL_ID = "scribe_v2"
MAX_AUDIO_BYTES = 10 * 1024 * 1024
_stt_denied = False  # set when the key lacks the speech_to_text permission
_stt_denied_at = 0.0
STT_RECHECK_SECONDS = 120  # permission changes on the ElevenLabs site apply without a restart


def stt_enabled() -> bool:
    global _stt_denied, _stt_probed
    if _stt_denied and time.time() - _stt_denied_at > STT_RECHECK_SECONDS:
        _stt_denied = False
        _stt_probed = False
    return enabled() and not _stt_denied and os.getenv("ELEVENLABS_STT", "on").lower() != "off"


def transcribe(audio: bytes, content_type: str, language: str) -> str:
    """Turn a short recording into text. Raises TTSError on any failure."""
    global _stt_denied, _stt_denied_at
    key, lang, _, _ = _settings(language)
    if not audio or len(audio) < 1000:
        raise TTSError("The recording was too short")
    if len(audio) > MAX_AUDIO_BYTES:
        raise TTSError("The recording is too long")
    ext = "webm" if "webm" in content_type else "ogg" if "ogg" in content_type else "mp4" if "mp4" in content_type else "wav" if "wav" in content_type else "audio"
    try:
        res = httpx.post(
            STT_URL,
            headers={"xi-api-key": key},
            data={"model_id": os.getenv("ELEVENLABS_STT_MODEL_ID", STT_MODEL_ID), "language_code": lang},
            files={"file": (f"recording.{ext}", audio, content_type or "application/octet-stream")},
            timeout=60.0,
        )
    except httpx.HTTPError as e:
        logger.warning("ElevenLabs STT unreachable: %s", e)
        raise TTSError("Could not reach ElevenLabs")
    if res.status_code != 200:
        err = _error_from(res)
        if res.status_code in (401, 403) and "speech_to_text" in str(err):
            _stt_denied = True
            _stt_denied_at = time.time()
        raise err
    return (res.json().get("text") or "").strip()


_stt_probed = False


def probe_stt() -> None:
    """Check once whether the key may use speech-to-text, using 0.3 s of silence."""
    global _stt_probed
    stt_enabled()  # lets an expired denial be re-checked
    if _stt_probed or not enabled() or _stt_denied:
        return
    _stt_probed = True
    import io
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 4800)
    try:
        transcribe(buf.getvalue(), "audio/wav", "en")
    except TTSError as e:
        logger.info("Speech-to-text probe: %s", e)

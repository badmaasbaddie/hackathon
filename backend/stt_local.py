"""
Offline speech-to-text with Whisper (faster-whisper), used when ElevenLabs speech-to-text
is not available. Runs on this computer: no internet or API key needed once the model
has been downloaded (about 480 MB for "small", fetched automatically on first start).
"""

import io
import os
import logging
import threading
import warnings
from typing import Optional

logger = logging.getLogger("swasthyasetu.stt")

os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
warnings.filterwarnings("ignore", module="huggingface_hub")

MODEL_NAME = os.getenv("WHISPER_MODEL", "small")

# A short list of symptom words in each language nudges Whisper towards spelling them
# correctly - important because the emergency screen looks for exact phrases.
PROMPTS = {
    "hi": "मरीज़ अपने लक्षण बता रहा है: सीने में दर्द, सांस लेने में तकलीफ, बुखार, खांसी, दस्त, उल्टी, सिरदर्द, बेहोश, लकवा, बीपी, शुगर।",
    "mr": "रुग्ण आपली लक्षणे सांगत आहे: छातीत दुखत आहे, श्वास घ्यायला त्रास, ताप, खोकला, जुलाब, उलटी, डोकेदुखी, बेशुद्ध, अर्धांगवायू, रक्तदाब, मधुमेह.",
    "en": "The patient describes symptoms: chest pain, difficulty breathing, fever, cough, diarrhoea, vomiting, headache.",
}

_model = None
_lock = threading.Lock()
_load_error: Optional[str] = None


def available() -> bool:
    if os.getenv("LOCAL_STT", "on").lower() == "off" or _load_error:
        return False
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _get_model():
    global _model, _load_error
    with _lock:
        if _model is None:
            from faster_whisper import WhisperModel
            try:
                _model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")
            except Exception as e:  # download or load failure
                _load_error = str(e)
                logger.warning("Could not load Whisper model %s: %s", MODEL_NAME, e)
                raise
        return _model


def warm_up() -> None:
    """Load (and on first run, download) the model in the background so the first mic press is quick."""
    if not available():
        return
    def _load():
        try:
            _get_model()
            logger.info("Whisper model '%s' ready for offline voice input", MODEL_NAME)
        except Exception:
            pass
    threading.Thread(target=_load, daemon=True).start()


def transcribe(audio: bytes, language: str) -> str:
    lang = language if language in PROMPTS else "en"
    model = _get_model()
    segments, _ = model.transcribe(
        io.BytesIO(audio), language=lang, beam_size=1, vad_filter=True, initial_prompt=PROMPTS[lang]
    )
    return " ".join(s.text.strip() for s in segments).strip()

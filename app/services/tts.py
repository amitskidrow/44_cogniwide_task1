import os
from typing import Optional

from app.logging_config import logger

import requests


class TTSClient:
    """Text-to-speech client supporting ElevenLabs and Twilio."""

    def __init__(self, provider: Optional[str] = None) -> None:
        self.provider = (provider or os.getenv("TTS_PROVIDER", "elevenlabs")).lower()
        if self.provider == "elevenlabs":
            self._api_key = os.getenv("ELEVEN_API_KEY")
            if not self._api_key:
                raise ValueError("ELEVEN_API_KEY not set")
            self._voice_id = os.getenv("ELEVEN_VOICE_ID", "default")
            self._model_id = os.getenv("ELEVEN_MODEL_ID", "eleven_multilingual_v2")
        elif self.provider == "twilio":
            try:
                from twilio.twiml.voice_response import VoiceResponse
            except ImportError as e:
                raise ImportError("twilio package required for Twilio TTS") from e
            self._voice = os.getenv("TWILIO_TTS_VOICE", "Polly.Joanna")
            self._VoiceResponse = VoiceResponse
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")

    def synthesize(self, text: str, conversation_id: str | None = None) -> bytes:
        """Generate speech audio for ``text``. Returns bytes or TwiML XML."""
        ctx = {"conversation_id": conversation_id}
        logger.bind(**ctx).info("synthesize.start")

        if self.provider == "elevenlabs":
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}"
            headers = {"xi-api-key": self._api_key}
            payload = {"text": text, "model_id": self._model_id}
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            audio = response.content
        elif self.provider == "twilio":
            vr = self._VoiceResponse()
            vr.say(text, voice=self._voice)
            audio = str(vr).encode()
        else:
            raise RuntimeError("Unhandled TTS provider")

        logger.bind(**ctx).info("synthesize.end")
        return audio


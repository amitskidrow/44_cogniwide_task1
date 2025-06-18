from typing import Optional

from app.config import get_settings

import requests


class TTSClient:
    """Text-to-speech client supporting ElevenLabs and Twilio."""

    def __init__(self, provider: Optional[str] = None) -> None:
        settings = get_settings()
        self.provider = (provider or settings.tts_provider).lower()
        if self.provider == "elevenlabs":
            self._api_key = settings.eleven_api_key
            if not self._api_key:
                raise ValueError("ELEVEN_API_KEY not set")
            self._voice_id = settings.eleven_voice_id
            self._model_id = settings.eleven_model_id
        elif self.provider == "twilio":
            try:
                from twilio.twiml.voice_response import VoiceResponse
            except ImportError as e:
                raise ImportError("twilio package required for Twilio TTS") from e
            self._voice = settings.twilio_tts_voice
            self._VoiceResponse = VoiceResponse
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")

    def synthesize(self, text: str) -> bytes:
        """Generate speech audio for ``text``. Returns bytes or TwiML XML."""
        if self.provider == "elevenlabs":
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}"
            headers = {"xi-api-key": self._api_key}
            payload = {"text": text, "model_id": self._model_id}
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.content
        elif self.provider == "twilio":
            vr = self._VoiceResponse()
            vr.say(text, voice=self._voice)
            return str(vr).encode()
        raise RuntimeError("Unhandled TTS provider")


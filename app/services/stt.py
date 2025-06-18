from typing import Optional

from app.config import get_settings


class STTClient:
    """Speech-to-text client supporting OpenAI Whisper and Deepgram."""

    def __init__(self, provider: Optional[str] = None) -> None:
        settings = get_settings()
        self.provider = (provider or settings.stt_provider).lower()
        if self.provider == "openai":
            try:
                import openai
            except ImportError as e:
                raise ImportError("openai package required for Whisper STT") from e
            self._client = openai
            self._model = settings.openai_whisper_model
            self._api_key = settings.openai_api_key
            if self._api_key:
                self._client.api_key = self._api_key
        elif self.provider == "deepgram":
            try:
                from deepgram import Deepgram
            except ImportError as e:
                raise ImportError("deepgram-sdk package required for Deepgram STT") from e
            self._api_key = settings.deepgram_api_key
            if not self._api_key:
                raise ValueError("DEEPGRAM_API_KEY not set")
            self._client = Deepgram(self._api_key)
            self._model = settings.deepgram_model
        else:
            raise ValueError(f"Unsupported STT provider: {self.provider}")

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file located at ``audio_path`` and return text."""
        if self.provider == "openai":
            with open(audio_path, "rb") as fh:
                response = self._client.Audio.transcribe(self._model, fh)
            return response.get("text", "")
        elif self.provider == "deepgram":
            with open(audio_path, "rb") as fh:
                source = {"buffer": fh.read(), "mimetype": "audio/wav"}
            options = {"model": self._model}
            response = self._client.transcription.sync_prerecorded(source, options)
            return response["results"]["channels"][0]["alternatives"][0]["transcript"]
        raise RuntimeError("Unhandled STT provider")


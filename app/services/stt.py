import os
from typing import Optional


class STTClient:
    """Speech-to-text client supporting OpenAI Whisper and Deepgram, with optional locale."""

    def __init__(self, provider: Optional[str] = None, locale: Optional[str] = None) -> None:
        self.provider = (provider or os.getenv("STT_PROVIDER", "openai")).lower()
        self.locale = locale or os.getenv("DEFAULT_LOCALE", "en-US")
        if self.provider == "openai":
            try:
                import openai
            except ImportError as e:
                raise ImportError("openai package required for Whisper STT") from e
            self._client = openai
            self._model = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
            self._api_key = os.getenv("OPENAI_API_KEY")
            if self._api_key:
                self._client.api_key = self._api_key
        elif self.provider == "deepgram":
            try:
                from deepgram import Deepgram
            except ImportError as e:
                raise ImportError("deepgram-sdk package required for Deepgram STT") from e
            self._api_key = os.getenv("DEEPGRAM_API_KEY")
            if not self._api_key:
                raise ValueError("DEEPGRAM_API_KEY not set")
            self._client = Deepgram(self._api_key)
            self._model = os.getenv("DEEPGRAM_MODEL", "general")
        else:
            raise ValueError(f"Unsupported STT provider: {self.provider}")

    def transcribe(self, audio_path: str) -> str:
        """Transcribe audio file located at ``audio_path`` and return text."""
        if self.provider == "openai":
            with open(audio_path, "rb") as fh:
                # include locale for language-specific transcription
                response = self._client.Audio.transcribe(self._model, fh, language=self.locale)
            return response.get("text", "")
        elif self.provider == "deepgram":
            with open(audio_path, "rb") as fh:
                source = {"buffer": fh.read(), "mimetype": "audio/wav"}
            options = {"model": self._model, "language": self.locale}
            response = self._client.transcription.sync_prerecorded(source, options)
            return response["results"]["channels"][0]["alternatives"][0]["transcript"]
        raise RuntimeError("Unhandled STT provider")


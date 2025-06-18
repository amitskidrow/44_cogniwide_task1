from functools import lru_cache
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = 'sqlite:///./app.db'
    openai_api_key: str | None = None
    openai_model: str = 'gpt-3.5-turbo'
    openai_whisper_model: str = 'whisper-1'
    deepgram_api_key: str | None = None
    deepgram_model: str = 'general'
    eleven_api_key: str | None = None
    eleven_voice_id: str = 'default'
    eleven_model_id: str = 'eleven_multilingual_v2'
    stt_provider: str = 'openai'
    tts_provider: str = 'elevenlabs'
    twilio_tts_voice: str = 'Polly.Joanna'

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

def get_settings() -> Settings:
    return _get_settings()

@lru_cache()
def _get_settings() -> Settings:
    return Settings()

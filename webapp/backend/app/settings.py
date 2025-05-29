from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    GEMINI_API_KEY: Optional[str]
    GEMINI_MODEL: str = "gemini-2.5-flash-preview-05-20"
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: str = 'http://localhost:4318/v1/traces'

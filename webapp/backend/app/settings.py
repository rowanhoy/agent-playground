from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    GITHUB_MODELS_API_KEY: str
    GITHUB_MODELS_API_URL: str = "https://models.github.ai/inference"
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    OPENAI_MODEL_NAME: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://aibcc:aibcc@localhost:5432/aibcc"
    debug: bool = False

    model_config = {"env_file": ".env"}


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "DB Script Agent"
    DATABASE_URL: str = "sqlite+aiosqlite:///./db_script_agent.db"
    LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    DEFAULT_DIALECT: str = "mysql"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

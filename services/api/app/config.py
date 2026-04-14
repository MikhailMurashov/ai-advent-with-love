from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_model: str = "gigachat/GigaChat-2-Lite"
    api_key: str = ""
    gigachat_credentials: str = ""
    gigachat_scope: str = "GIGACHAT_API_PERSONAL"
    sqlite_path: str = "/app/data/db.sqlite"
    mcp_config_path: str = "mcp_config.yaml"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

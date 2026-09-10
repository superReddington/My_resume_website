from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    embedding_dim: int = 512

    database_url: str = "postgresql://postgres:postgres@127.0.0.1:5433/resume_agent"
    admin_token: str = "change-me"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://47.96.159.83,https://zhuzhimin.cn,http://zhuzhimin.cn"

    upload_dir: Path = ROOT_DIR / "data" / "uploads"
    max_upload_mb: int = 10
    chunk_size: int = 1200
    chunk_overlap: int = 150
    chat_rate_limit: str = "20/minute"
    max_history_messages: int = 12

    @property
    def origin_list(self) -> list[str]:
        return [item.strip() for item in self.allowed_origins.split(",") if item.strip()]


settings = Settings()

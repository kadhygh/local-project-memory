from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Static configuration for the MVP scaffold."""

    app_name: str = "local-project-memory"
    api_prefix: str = "/v1"
    data_dir: Path = Field(default=Path("data"))
    default_top_k: int = 8



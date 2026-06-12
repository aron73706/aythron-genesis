import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # API / Server Configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # LLM / Provider Configuration
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    default_model: str = Field(default="qwen2.5:7b", env="DEFAULT_MODEL")
    planner_model: str = Field(default="qwen2.5:7b", env="PLANNER_MODEL")
    worker_model: str = Field(default="qwen2.5:7b", env="WORKER_MODEL")
    reviewer_model: str = Field(default="qwen2.5:7b", env="REVIEWER_MODEL")
    
    # Workspace
    workspace_dir: str = Field(
        default_factory=lambda: os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        env="WORKSPACE_DIR"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

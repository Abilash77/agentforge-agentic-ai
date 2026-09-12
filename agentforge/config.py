"""
AgentForge Configuration System.

Loads settings from environment variables and agentforge.yaml.
Wraps MetaGPT's Config for seamless LLM provider access.
AES-256 encryption is applied to API keys stored in the database.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

# Root paths
AGENTFORGE_ROOT = Path(__file__).parent.parent

AGENTFORGE_PKG_ROOT = Path(__file__).parent
DATA_DIR = AGENTFORGE_PKG_ROOT / "data"
DB_DIR = DATA_DIR / "db"
CHROMA_DIR = DATA_DIR / "chroma"
LOGS_DIR = DATA_DIR / "logs"
OUTPUTS_DIR = DATA_DIR / "outputs"


class LLMSettings(BaseSettings):
    """LLM provider configuration."""
    api_type: str = "openai"
    model: str = "gpt-4o"
    base_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 120
    max_retries: int = 3

    model_config = {"env_prefix": "LLM_", "extra": "ignore"}


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    sqlite_url: str = f"sqlite+aiosqlite:///{DB_DIR}/agentforge.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10

    model_config = {"env_prefix": "DB_", "extra": "ignore"}


class ChromaSettings(BaseSettings):
    """ChromaDB vector store configuration."""
    persist_directory: str = str(CHROMA_DIR)
    collection_project_knowledge: str = "project_knowledge"
    collection_generated_code: str = "generated_code"
    collection_architecture: str = "architecture_docs"
    collection_tests: str = "test_cases"
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 5

    model_config = {"env_prefix": "CHROMA_", "extra": "ignore"}


class AuthSettings(BaseSettings):
    """Authentication and security configuration."""
    secret_key: str = "agentforge-dev-secret-change-in-production-32chars-minimum"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    encryption_key: str = ""  # Fernet key for API key encryption – auto-generated if empty
    enable_auth: bool = False  # Set True in production

    model_config = {"env_prefix": "AUTH_", "extra": "ignore"}


class AgentForgeConfig(BaseSettings):
    """
    Master AgentForge configuration.
    Priority: environment variables > .env file > defaults.
    """

    # Application
    app_name: str = "AgentForge"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    frontend_port: int = 8501
    workers: int = 1

    # Sub-configs (nested)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    chroma: ChromaSettings = Field(default_factory=ChromaSettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)

    # Budget
    default_budget_usd: float = 5.0
    max_budget_usd: float = 50.0

    # Pipeline
    max_pipeline_rounds: int = 10
    enable_rag_context: bool = True
    enable_persistent_memory: bool = True
    enable_cost_tracking: bool = True

    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_file: str = str(LOGS_DIR / "agentforge.log")

    # Directories (auto-created on startup)
    data_dir: str = str(DATA_DIR)
    outputs_dir: str = str(OUTPUTS_DIR)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False,
    }

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        valid = {"development", "staging", "production"}
        if v not in valid:
            raise ValueError(f"environment must be one of {valid}")
        return v

    def ensure_directories(self) -> None:
        """Create all required data directories."""
        for d in [DATA_DIR, DB_DIR, CHROMA_DIR, LOGS_DIR, OUTPUTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def to_metagpt_config_dict(self) -> dict:
        """Export LLM settings in MetaGPT-compatible format."""
        return {
            "llm": {
                "api_type": self.llm.api_type,
                "model": self.llm.model,
                "base_url": self.llm.base_url,
                "api_key": self.llm.api_key,
            }
        }

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_debug(self) -> bool:
        return self.debug or self.environment == "development"


@lru_cache(maxsize=1)
def get_config() -> AgentForgeConfig:
    """Return the singleton AgentForge configuration instance."""
    cfg = AgentForgeConfig()
    cfg.ensure_directories()
    return cfg

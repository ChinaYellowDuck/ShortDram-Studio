"""LLM configuration model."""
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LLMConfig(BaseModel):
    """LLM provider configuration model.

    Stores multiple LLM configurations that users can manage through the UI.
    Each config includes provider, model name, API key, and other settings.
    API keys are encrypted before storage.

    Attributes:
        name: Display name for this configuration.
        provider: LLM provider (openai, anthropic, deepseek, qwen, zhipu, ollama, etc.).
        model_name: Model identifier (e.g. "gpt-4o", "claude-3-5-sonnet").
        api_key: Encrypted API key.
        base_url: Optional custom API base URL.
        is_default: Whether this is the default configuration.
        description: Optional description of this configuration.
    """

    __tablename__ = "llm_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    model_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key: Mapped[str] = mapped_column(Text, nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<LLMConfig(id={self.id}, name='{self.name}', provider='{self.provider}')>"

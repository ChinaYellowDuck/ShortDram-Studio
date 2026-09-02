"""LLM configuration service - business logic for LLM config management."""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.llm_config import LLMConfig
from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigResponse,
    LLMConfigUpdate,
    LLMProviderInfo,
    LLMTestResult,
)
from app.utils.crypto import decrypt, encrypt


# Supported LLM providers
SUPPORTED_PROVIDERS: List[LLMProviderInfo] = [
    LLMProviderInfo(key="openai", name="OpenAI", default_model="gpt-4o", supports_base_url=True),
    LLMProviderInfo(
        key="anthropic",
        name="Anthropic (Claude)",
        default_model="claude-3-5-sonnet-20240620",
        supports_base_url=True,
    ),
    LLMProviderInfo(key="deepseek", name="DeepSeek", default_model="deepseek-chat", supports_base_url=True),
    LLMProviderInfo(key="qwen", name="通义千问 (Qwen)", default_model="qwen-plus", supports_base_url=True),
    LLMProviderInfo(key="zhipu", name="智谱 AI (GLM)", default_model="glm-4", supports_base_url=True),
    LLMProviderInfo(key="ollama", name="Ollama (本地模型)", default_model="llama3.1", supports_base_url=True),
    LLMProviderInfo(key="moonshot", name="月之暗面 (Kimi)", default_model="moonshot-v1-8k", supports_base_url=True),
]


class LLMConfigService:
    """Service for managing LLM configurations."""

    def __init__(self, db: Session):
        self.db = db

    def get_supported_providers(self) -> List[LLMProviderInfo]:
        """Get list of supported LLM providers.

        Returns:
            List of provider info objects.
        """
        return SUPPORTED_PROVIDERS

    def get_by_id(self, config_id: int) -> Optional[LLMConfig]:
        """Get an LLM config by ID.

        Args:
            config_id: Configuration ID.

        Returns:
            LLMConfig if found, None otherwise.
        """
        return self.db.query(LLMConfig).filter(LLMConfig.id == config_id).first()

    def get_by_id_or_404(self, config_id: int) -> LLMConfig:
        """Get an LLM config by ID, raising 404 if not found.

        Args:
            config_id: Configuration ID.

        Returns:
            LLMConfig if found.

        Raises:
            HTTPException: 404 if config not found.
        """
        config = self.get_by_id(config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"LLM configuration with id {config_id} not found",
            )
        return config

    def get_default(self) -> Optional[LLMConfig]:
        """Get the default LLM configuration.

        Returns:
            Default LLMConfig if one exists, None otherwise.
        """
        return self.db.query(LLMConfig).filter(LLMConfig.is_default == True).first()  # noqa: E712

    def get_default_or_404(self) -> LLMConfig:
        """Get the default LLM config, raising 404 if none exists.

        Returns:
            Default LLMConfig.

        Raises:
            HTTPException: 404 if no default config exists.
        """
        config = self.get_default()
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No default LLM configuration found. Please create one first.",
            )
        return config

    def list_configs(self, skip: int = 0, limit: int = 100) -> tuple[List[LLMConfig], int]:
        """List all LLM configurations with pagination.

        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.

        Returns:
            Tuple of (configs list, total count).
        """
        query = self.db.query(LLMConfig)
        total = query.count()
        configs = query.order_by(LLMConfig.is_default.desc(), LLMConfig.created_at.desc()).offset(skip).limit(limit).all()
        return configs, total

    def create(self, config_data: LLMConfigCreate) -> LLMConfig:
        """Create a new LLM configuration.

        Args:
            config_data: Configuration data.

        Returns:
            Created LLMConfig.

        Raises:
            HTTPException: If provider is not supported.
        """
        # Validate provider
        provider_keys = {p.key for p in SUPPORTED_PROVIDERS}
        if config_data.provider not in provider_keys:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported provider: {config_data.provider}. "
                f"Supported providers: {', '.join(provider_keys)}",
            )

        # Encrypt API key
        encrypted_api_key = encrypt(config_data.api_key)

        # If setting as default, unset existing default
        if config_data.is_default:
            self._unset_existing_default()

        db_config = LLMConfig(
            name=config_data.name,
            provider=config_data.provider,
            model_name=config_data.model_name,
            api_key=encrypted_api_key,
            base_url=config_data.base_url,
            is_default=config_data.is_default,
            description=config_data.description,
        )

        self.db.add(db_config)
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def update(self, config_id: int, config_data: LLMConfigUpdate) -> LLMConfig:
        """Update an existing LLM configuration.

        Args:
            config_id: Configuration ID to update.
            config_data: Update data.

        Returns:
            Updated LLMConfig.

        Raises:
            HTTPException: 404 if config not found.
        """
        db_config = self.get_by_id_or_404(config_id)

        update_data = config_data.model_dump(exclude_unset=True)

        # Encrypt API key if being updated
        if "api_key" in update_data:
            update_data["api_key"] = encrypt(update_data["api_key"])

        # If setting as default, unset existing default
        if update_data.get("is_default"):
            self._unset_existing_default(exclude_id=config_id)

        for field, value in update_data.items():
            setattr(db_config, field, value)

        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def delete(self, config_id: int) -> None:
        """Delete an LLM configuration.

        Args:
            config_id: Configuration ID to delete.

        Raises:
            HTTPException: 404 if config not found.
        """
        db_config = self.get_by_id_or_404(config_id)
        self.db.delete(db_config)
        self.db.commit()

    def set_default(self, config_id: int) -> LLMConfig:
        """Set a configuration as the default.

        Args:
            config_id: Configuration ID to set as default.

        Returns:
            Updated LLMConfig.

        Raises:
            HTTPException: 404 if config not found.
        """
        db_config = self.get_by_id_or_404(config_id)
        self._unset_existing_default(exclude_id=config_id)
        db_config.is_default = True
        self.db.commit()
        self.db.refresh(db_config)
        return db_config

    def decrypt_api_key(self, config: LLMConfig) -> str:
        """Get the decrypted API key for a configuration.

        Args:
            config: LLM configuration.

        Returns:
            Decrypted API key.
        """
        return decrypt(config.api_key)

    def _unset_existing_default(self, exclude_id: Optional[int] = None) -> None:
        """Unset the default flag on all configurations except optionally one.

        Args:
            exclude_id: Optional ID to exclude from unsetting.
        """
        query = self.db.query(LLMConfig).filter(LLMConfig.is_default == True)  # noqa: E712
        if exclude_id is not None:
            query = query.filter(LLMConfig.id != exclude_id)
        for config in query.all():
            config.is_default = False
        self.db.flush()

    async def test_config(self, config_id: int) -> LLMTestResult:
        """Test an LLM configuration by making a simple API call.

        Args:
            config_id: Configuration ID to test.

        Returns:
            Test result with success status and message.
        """
        import time

        from app.agents.llm import LLMFactory

        db_config = self.get_by_id_or_404(config_id)

        try:
            llm = LLMFactory.create_from_config(
                LLMConfigResponse.model_validate(db_config),
                decrypt(db_config.api_key),
            )

            start_time = time.time()
            response = await llm.ainvoke("Reply with exactly: OK")
            elapsed = (time.time() - start_time) * 1000

            return LLMTestResult(
                success=True,
                message="Configuration test successful",
                response_time_ms=round(elapsed, 2),
                model=db_config.model_name,
            )
        except Exception as e:
            return LLMTestResult(
                success=False,
                message=f"Test failed: {str(e)}",
            )

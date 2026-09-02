"""LLM Factory - creates ChatModel instances from database configurations.

This factory allows dynamic creation of LLM instances based on user-managed
configurations stored in the database, supporting multiple providers.
"""
from typing import Optional

from langchain_core.language_models import BaseChatModel
from loguru import logger

from app.schemas.llm_config import LLMConfigResponse


class LLMFactory:
    """Factory for creating LLM ChatModel instances from configuration."""

    @staticmethod
    def create_from_config(
        config: LLMConfigResponse,
        api_key: str,
        temperature: float = 0.7,
    ) -> BaseChatModel:
        """Create a ChatModel instance from an LLM configuration.

        Args:
            config: LLM configuration from the database.
            api_key: Decrypted API key.
            temperature: Model temperature (0.0 - 1.0).

        Returns:
            LangChain BaseChatModel instance.

        Raises:
            ValueError: If the provider is not supported.
        """
        provider = config.provider.lower()
        model_name = config.model_name
        base_url = config.base_url

        logger.debug(f"Creating LLM: provider={provider}, model={model_name}")

        if provider == "openai":
            return LLMFactory._create_openai(model_name, api_key, base_url, temperature)

        if provider == "anthropic":
            return LLMFactory._create_anthropic(model_name, api_key, base_url, temperature)

        # Providers compatible with OpenAI API format
        openai_compatible = [
            "deepseek",
            "qwen",
            "zhipu",
            "moonshot",
            "ollama",
        ]
        if provider in openai_compatible:
            return LLMFactory._create_openai_compatible(
                provider, model_name, api_key, base_url, temperature
            )

        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: openai, anthropic, deepseek, qwen, zhipu, ollama, moonshot"
        )

    @staticmethod
    def _create_openai(
        model_name: str,
        api_key: str,
        base_url: Optional[str],
        temperature: float,
    ) -> BaseChatModel:
        """Create an OpenAI ChatOpenAI instance."""
        from langchain_openai import ChatOpenAI

        kwargs = {
            "model": model_name,
            "api_key": api_key,
            "temperature": temperature,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatOpenAI(**kwargs)

    @staticmethod
    def _create_anthropic(
        model_name: str,
        api_key: str,
        base_url: Optional[str],
        temperature: float,
    ) -> BaseChatModel:
        """Create an Anthropic ChatAnthropic instance."""
        from langchain_anthropic import ChatAnthropic

        kwargs = {
            "model": model_name,
            "api_key": api_key,
            "temperature": temperature,
        }
        if base_url:
            kwargs["base_url"] = base_url

        return ChatAnthropic(**kwargs)

    @staticmethod
    def _create_openai_compatible(
        provider: str,
        model_name: str,
        api_key: str,
        base_url: Optional[str],
        temperature: float,
    ) -> BaseChatModel:
        """Create a ChatOpenAI instance compatible with OpenAI-formatted APIs.

        Many providers (DeepSeek, Qwen, Zhipu, Ollama, etc.) offer OpenAI-compatible APIs.
        """
        from langchain_openai import ChatOpenAI

        # Default base URLs for known providers
        default_base_urls = {
            "deepseek": "https://api.deepseek.com/v1",
            "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "zhipu": "https://open.bigmodel.cn/api/paas/v4",
            "moonshot": "https://api.moonshot.cn/v1",
            "ollama": "http://localhost:11434/v1",
        }

        resolved_base_url = base_url or default_base_urls.get(provider)
        if not resolved_base_url:
            raise ValueError(
                f"Base URL is required for provider '{provider}'. "
                f"Please set base_url in the LLM configuration."
            )

        return ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=resolved_base_url,
            temperature=temperature,
        )

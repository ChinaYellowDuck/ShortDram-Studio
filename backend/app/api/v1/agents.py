"""Agent execution endpoints."""
from fastapi import APIRouter, HTTPException, status

from app.api.deps import LLMConfigServiceDep
from app.schemas.llm_config import LLMConfigResponse

router = APIRouter()


class AgentChatRequest(LLMConfigResponse):
    pass


@router.get("/list", summary="获取可用智能体列表")
def list_agents():
    """List all available agents."""
    return [
        {
            "id": "hello_agent",
            "name": "Hello Agent",
            "description": "简单的问候智能体，用于测试智能体框架",
            "status": "available",
        },
    ]


@router.post("/hello/chat", summary="Hello Agent 对话（测试用）")
async def hello_agent_chat(
    service: LLMConfigServiceDep,
    message: str,
    llm_config_id: int | None = None,
):
    """
    Test the Hello Agent with a message.

    - **message**: 用户输入消息
    - **llm_config_id**: 可选，使用指定的 LLM 配置；不传则使用默认配置
    """
    try:
        from app.agents.hello_agent import HelloAgent
        from app.agents.llm import LLMFactory
        from app.utils.crypto import decrypt

        # Get LLM config
        if llm_config_id:
            config = service.get_by_id_or_404(llm_config_id)
        else:
            config = service.get_default_or_404()

        # Create LLM instance
        api_key = decrypt(config.api_key)
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            api_key,
        )

        # Create and invoke agent
        agent = HelloAgent(llm)
        response = await agent.achat(message)

        return {
            "agent": "hello_agent",
            "message": message,
            "response": response,
            "llm_config": {
                "id": config.id,
                "name": config.name,
                "provider": config.provider,
                "model": config.model_name,
            },
        }

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent dependencies not available: {e}",
        ) from e

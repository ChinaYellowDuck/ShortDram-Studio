"""Database seed data for initial agent metadata.

Seeds the agents table with default agents on application startup.
Idempotent — only inserts agents that don't already exist.
"""
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.schemas.agent import AgentCreate


# Default agents to seed
DEFAULT_AGENTS = [
    AgentCreate(
        agent_key="hello_agent",
        name="Hello Agent",
        description="简单的问候智能体，用于测试智能体框架是否正常工作",
        agent_type="测试",
        category="测试",
        is_enabled=True,
        version="1.0",
    ),
    AgentCreate(
        agent_key="screenwriter",
        name="编剧智能体",
        description="从创意生成完整短剧剧本，支持场景大纲、对白撰写、多轮打磨",
        agent_type="创作",
        category="创作",
        is_enabled=True,
        version="1.0",
    ),
    AgentCreate(
        agent_key="producer",
        name="制片人智能体",
        description="统筹短剧制作全流程，一键从创意生成完整剧本项目",
        agent_type="协调",
        category="协调",
        is_enabled=True,
        version="1.0",
    ),
]


def seed_agents(db: Session) -> int:
    """Seed the agents table with default agents if empty.

    Args:
        db: Database session.

    Returns:
        Number of agents created.
    """
    created_count = 0

    for agent_data in DEFAULT_AGENTS:
        existing = db.query(Agent).filter(Agent.agent_key == agent_data.agent_key).first()
        if existing:
            continue

        db_agent = Agent(
            agent_key=agent_data.agent_key,
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type,
            category=agent_data.category,
            is_enabled=agent_data.is_enabled,
            default_llm_config_id=agent_data.default_llm_config_id,
            default_params=agent_data.default_params,
            version=agent_data.version,
        )
        db.add(db_agent)
        created_count += 1

    if created_count > 0:
        db.commit()

    return created_count

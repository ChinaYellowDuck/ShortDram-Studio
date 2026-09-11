"""API layer dependencies."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.agent_service import AgentService
from app.services.asset_service import AssetService
from app.services.llm_config_service import LLMConfigService
from app.services.mcp_service import McpService
from app.services.project_service import ProjectService
from app.services.script_service import ScriptService
from app.services.skill_service import SkillService
from app.services.project_agent_service import ProjectAgentService
from app.services.storyboard_service import StoryboardService

DBSession = Annotated[Session, Depends(get_db)]


def get_llm_config_service(db: DBSession) -> LLMConfigService:
    """Dependency for LLMConfigService.

    Args:
        db: Database session.

    Returns:
        LLMConfigService instance.
    """
    return LLMConfigService(db)


def get_project_service(db: DBSession) -> ProjectService:
    """Dependency for ProjectService.

    Args:
        db: Database session.

    Returns:
        ProjectService instance.
    """
    return ProjectService(db)


def get_script_service(db: DBSession) -> ScriptService:
    """Dependency for ScriptService.

    Args:
        db: Database session.

    Returns:
        ScriptService instance.
    """
    return ScriptService(db)


def get_agent_service(db: DBSession) -> AgentService:
    """Dependency for AgentService.

    Args:
        db: Database session.

    Returns:
        AgentService instance.
    """
    return AgentService(db)


def get_mcp_service(db: DBSession) -> McpService:
    """Dependency for McpService."""
    return McpService(db)


def get_skill_service(db: DBSession) -> SkillService:
    """Dependency for SkillService."""
    return SkillService(db)


LLMConfigServiceDep = Annotated[LLMConfigService, Depends(get_llm_config_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]
ScriptServiceDep = Annotated[ScriptService, Depends(get_script_service)]
AgentServiceDep = Annotated[AgentService, Depends(get_agent_service)]
McpServiceDep = Annotated[McpService, Depends(get_mcp_service)]
SkillServiceDep = Annotated[SkillService, Depends(get_skill_service)]


def get_asset_service(db: DBSession) -> AssetService:
    """Dependency for AssetService."""
    return AssetService(db)


def get_storyboard_service(db: DBSession) -> StoryboardService:
    """Dependency for StoryboardService."""
    return StoryboardService(db)


def get_project_agent_service(db: DBSession) -> ProjectAgentService:
    """Dependency for ProjectAgentService."""
    return ProjectAgentService(db)


AssetServiceDep = Annotated[AssetService, Depends(get_asset_service)]
StoryboardServiceDep = Annotated[StoryboardService, Depends(get_storyboard_service)]
ProjectAgentServiceDep = Annotated[ProjectAgentService, Depends(get_project_agent_service)]

"""API layer dependencies."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.llm_config_service import LLMConfigService
from app.services.project_service import ProjectService

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


LLMConfigServiceDep = Annotated[LLMConfigService, Depends(get_llm_config_service)]
ProjectServiceDep = Annotated[ProjectService, Depends(get_project_service)]

"""Project Agent Service - business logic for project-agent configuration.

Handles per-project agent setup, enabling/disabling, director assignment,
and parameter overrides.
"""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.project import Project
from app.models.project_agent import ProjectAgentConfig
from app.schemas.project_agent import (
    ProjectAgentConfigCreate,
    ProjectAgentConfigUpdate,
    ProjectAgentSetupRequest,
)


class ProjectAgentService:
    """Service for managing project agent configurations."""

    def __init__(self, db: Session):
        self.db = db

    # ── Config CRUD ────────────────────────────────────────────────────────

    def list_configs(self, project_id: int) -> List[ProjectAgentConfig]:
        """List all agent configs for a project, joined with agent info."""
        return (
            self.db.query(ProjectAgentConfig)
            .filter(ProjectAgentConfig.project_id == project_id)
            .order_by(ProjectAgentConfig.priority.asc())
            .all()
        )

    def list_enabled(self, project_id: int) -> List[ProjectAgentConfig]:
        """List enabled agent configs for a project."""
        return (
            self.db.query(ProjectAgentConfig)
            .filter(
                ProjectAgentConfig.project_id == project_id,
                ProjectAgentConfig.is_enabled.is_(True),
            )
            .order_by(ProjectAgentConfig.priority.asc())
            .all()
        )

    def get_director(self, project_id: int) -> Optional[ProjectAgentConfig]:
        """Get the director agent config for a project."""
        return (
            self.db.query(ProjectAgentConfig)
            .filter(
                ProjectAgentConfig.project_id == project_id,
                ProjectAgentConfig.is_director.is_(True),
            )
            .first()
        )

    def get_config(self, project_id: int, agent_id: int) -> Optional[ProjectAgentConfig]:
        """Get a specific agent config."""
        return (
            self.db.query(ProjectAgentConfig)
            .filter(
                ProjectAgentConfig.project_id == project_id,
                ProjectAgentConfig.agent_id == agent_id,
            )
            .first()
        )

    def get_config_or_404(self, project_id: int, agent_id: int) -> ProjectAgentConfig:
        cfg = self.get_config(project_id, agent_id)
        if not cfg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent config not found (project={project_id}, agent={agent_id})",
            )
        return cfg

    def add_agent(
        self, project_id: int, data: ProjectAgentConfigCreate
    ) -> ProjectAgentConfig:
        """Add an agent to a project."""
        # Verify project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify agent exists
        agent = self.db.query(Agent).filter(Agent.id == data.agent_id).first()
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        # Check if already exists
        existing = self.get_config(project_id, data.agent_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent {agent.agent_key} already added to this project",
            )

        # If this is being set as director, clear any existing director
        if data.is_director:
            self._clear_director(project_id)

        cfg = ProjectAgentConfig(project_id=project_id, **data.model_dump())
        self.db.add(cfg)
        self.db.commit()
        self.db.refresh(cfg)
        return cfg

    def update_config(
        self, project_id: int, agent_id: int, data: ProjectAgentConfigUpdate
    ) -> ProjectAgentConfig:
        """Update an agent config."""
        cfg = self.get_config_or_404(project_id, agent_id)
        update_data = data.model_dump(exclude_unset=True)

        # If setting as director, clear existing
        if update_data.get("is_director"):
            self._clear_director(project_id)

        for field, value in update_data.items():
            setattr(cfg, field, value)

        self.db.commit()
        self.db.refresh(cfg)
        return cfg

    def remove_agent(self, project_id: int, agent_id: int) -> None:
        """Remove an agent from a project."""
        cfg = self.get_config_or_404(project_id, agent_id)
        self.db.delete(cfg)
        self.db.commit()

    def toggle_agent(self, project_id: int, agent_id: int) -> ProjectAgentConfig:
        """Toggle an agent's enabled status."""
        cfg = self.get_config_or_404(project_id, agent_id)
        cfg.is_enabled = not cfg.is_enabled
        self.db.commit()
        self.db.refresh(cfg)
        return cfg

    # ── Batch Setup ────────────────────────────────────────────────────────

    def setup_project_agents(
        self, project_id: int, data: ProjectAgentSetupRequest
    ) -> List[ProjectAgentConfig]:
        """Batch setup agents for a project.

        Sets the director agent and enables the selected set of agents.
        Agents not in the list are disabled (not deleted).
        """
        # Verify project
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify director agent exists
        director_agent = self.db.query(Agent).filter(Agent.id == data.director_agent_id).first()
        if not director_agent:
            raise HTTPException(status_code=404, detail="Director agent not found")

        # Clear existing director
        self._clear_director(project_id)

        # Ensure all enabled agents have config entries
        all_agent_ids = set(data.enabled_agent_ids) | {data.director_agent_id}
        for aid in all_agent_ids:
            agent = self.db.query(Agent).filter(Agent.id == aid).first()
            if not agent:
                continue
            cfg = self.get_config(project_id, aid)
            if not cfg:
                cfg = ProjectAgentConfig(
                    project_id=project_id,
                    agent_id=aid,
                    is_enabled=aid in data.enabled_agent_ids or aid == data.director_agent_id,
                    is_director=aid == data.director_agent_id,
                )
                self.db.add(cfg)
            else:
                cfg.is_enabled = aid in data.enabled_agent_ids or aid == data.director_agent_id
                cfg.is_director = aid == data.director_agent_id

        # Disable agents not in the list
        all_configs = self.list_configs(project_id)
        for cfg in all_configs:
            if cfg.agent_id not in all_agent_ids:
                cfg.is_enabled = False

        self.db.commit()
        return self.list_configs(project_id)

    # ── Agent Registry Queries ─────────────────────────────────────────────

    def list_available_agents(self) -> List[Agent]:
        """List all available (enabled) agents in the registry."""
        return (
            self.db.query(Agent)
            .filter(Agent.is_enabled.is_(True))
            .order_by(Agent.agent_type, Agent.id)
            .all()
        )

    # ── Internal helpers ───────────────────────────────────────────────────

    def _clear_director(self, project_id: int) -> None:
        """Clear the director flag from all agents in the project."""
        self.db.query(ProjectAgentConfig).filter(
            ProjectAgentConfig.project_id == project_id,
            ProjectAgentConfig.is_director.is_(True),
        ).update({ProjectAgentConfig.is_director: False})
        self.db.flush()

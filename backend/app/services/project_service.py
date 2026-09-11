"""Project service - business logic for project management."""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectPhase, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for managing short drama projects."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, project_id: int) -> Optional[Project]:
        """Get a project by ID.

        Args:
            project_id: Project ID.

        Returns:
            Project if found, None otherwise.
        """
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_by_id_or_404(self, project_id: int) -> Project:
        """Get a project by ID, raising 404 if not found.

        Args:
            project_id: Project ID.

        Returns:
            Project if found.

        Raises:
            HTTPException: 404 if project not found.
        """
        project = self.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {project_id} not found",
            )
        return project

    def list_projects(
        self,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[ProjectStatus] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Project], int]:
        """List projects with optional filtering and pagination.

        Args:
            skip: Number of items to skip.
            limit: Maximum number of items to return.
            status_filter: Optional status filter.
            search: Optional search term for project name.

        Returns:
            Tuple of (projects list, total count).
        """
        query = self.db.query(Project)

        if status_filter:
            query = query.filter(Project.status == status_filter)

        if search:
            query = query.filter(Project.name.ilike(f"%{search}%"))

        total = query.count()
        projects = query.order_by(Project.updated_at.desc()).offset(skip).limit(limit).all()
        return projects, total

    def create(self, project_data: ProjectCreate) -> Project:
        """Create a new project.

        Args:
            project_data: Project data.

        Returns:
            Created Project.
        """
        db_project = Project(
            name=project_data.name,
            description=project_data.description,
            status=project_data.status,
            cover_image=project_data.cover_image,
        )

        self.db.add(db_project)
        self.db.commit()
        self.db.refresh(db_project)
        return db_project

    def update(self, project_id: int, project_data: ProjectUpdate) -> Project:
        """Update an existing project.

        Args:
            project_id: Project ID to update.
            project_data: Update data.

        Returns:
            Updated Project.

        Raises:
            HTTPException: 404 if project not found.
        """
        db_project = self.get_by_id_or_404(project_id)

        update_data = project_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_project, field, value)

        self.db.commit()
        self.db.refresh(db_project)
        return db_project

    def delete(self, project_id: int) -> None:
        """Delete a project.

        Args:
            project_id: Project ID to delete.

        Raises:
            HTTPException: 404 if project not found.
        """
        db_project = self.get_by_id_or_404(project_id)
        self.db.delete(db_project)
        self.db.commit()

    def update_status(self, project_id: int, new_status: ProjectStatus) -> Project:
        """Update project status.

        Args:
            project_id: Project ID.
            new_status: New status value.

        Returns:
            Updated Project.

        Raises:
            HTTPException: 404 if project not found.
        """
        db_project = self.get_by_id_or_404(project_id)
        db_project.status = new_status
        self.db.commit()
        self.db.refresh(db_project)
        return db_project

    def advance_phase(self, project_id: int, target_phase: ProjectPhase) -> Project:
        """Transition project to target phase.

        Both forward and backward transitions are allowed.
        Auto-updates project status when entering completed phase.

        Args:
            project_id: Project ID.
            target_phase: Target phase to transition to.

        Returns:
            Updated Project.

        Raises:
            HTTPException: 404 if project not found, 400 if invalid phase.
        """
        project = self.get_by_id_or_404(project_id)

        valid_phases = [
            ProjectPhase.SETUP,
            ProjectPhase.SCRIPT,
            ProjectPhase.ASSET,
            ProjectPhase.STORYBOARD,
            ProjectPhase.VIDEO,
            ProjectPhase.COMPLETED,
        ]
        if target_phase not in valid_phases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phase: {target_phase}",
            )

        # Validate: advancing from setup to script requires agent configuration
        if (
            project.phase == ProjectPhase.SETUP
            and target_phase == ProjectPhase.SCRIPT
        ):
            self._validate_agent_configuration(project_id)

        project.phase = target_phase

        if target_phase == ProjectPhase.COMPLETED:
            project.status = ProjectStatus.COMPLETED
        elif project.status == ProjectStatus.COMPLETED:
            # Rolling back from completed, set back to in_progress
            project.status = ProjectStatus.IN_PROGRESS
        elif project.status == ProjectStatus.DRAFT and target_phase not in (
            ProjectPhase.SETUP,
            ProjectPhase.SCRIPT,
        ):
            project.status = ProjectStatus.IN_PROGRESS

        self.db.commit()
        self.db.refresh(project)
        return project

    def _validate_agent_configuration(self, project_id: int) -> None:
        """Validate that the project has proper agent configuration.

        Requires:
        - A director (总控) agent is set
        - At least one creative agent is enabled (script/asset/storyboard related)
        """
        from app.models.project_agent import ProjectAgentConfig

        configs = (
            self.db.query(ProjectAgentConfig)
            .filter(
                ProjectAgentConfig.project_id == project_id,
                ProjectAgentConfig.is_enabled == True,  # noqa: E712
            )
            .all()
        )

        if not configs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请先配置并启用至少一个智能体",
            )

        has_director = any(c.is_director for c in configs)
        if not has_director:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请设置总控智能体",
            )

        # At least one non-director creative agent should be enabled
        creative_count = sum(1 for c in configs if not c.is_director)
        if creative_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请至少启用一个创作类智能体",
            )

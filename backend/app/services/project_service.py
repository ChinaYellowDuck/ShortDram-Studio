"""Project service - business logic for project management."""
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStatus
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

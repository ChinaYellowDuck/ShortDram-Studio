"""Agent service - business logic for agent metadata and run records."""
from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.agent import Agent, AgentRun, AgentRunStep, RunStatus, StepStatus
from app.schemas.agent import (
    AgentCreate,
    AgentRunCreate,
    AgentRunStepCreate,
    AgentRunStepUpdate,
    AgentRunUpdate,
    AgentUpdate,
)


class AgentService:
    """Service for managing agent metadata and run records."""

    def __init__(self, db: Session):
        self.db = db

    # ── Agent Metadata CRUD ───────────────────────────────────────────────────

    def get_by_id(self, agent_id: int) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.db.query(Agent).filter(Agent.id == agent_id).first()

    def get_by_id_or_404(self, agent_id: int) -> Agent:
        """Get an agent by ID, raising 404 if not found."""
        agent = self.get_by_id(agent_id)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with id {agent_id} not found",
            )
        return agent

    def get_by_key(self, agent_key: str) -> Optional[Agent]:
        """Get an agent by its unique key."""
        return self.db.query(Agent).filter(Agent.agent_key == agent_key).first()

    def get_by_key_or_404(self, agent_key: str) -> Agent:
        """Get an agent by its unique key, raising 404 if not found."""
        agent = self.get_by_key(agent_key)
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent with key '{agent_key}' not found",
            )
        return agent

    def list_agents(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Agent], int]:
        """List agents with pagination and filters.

        Returns:
            Tuple of (agents list, total count).
        """
        query = self.db.query(Agent)

        if agent_type:
            query = query.filter(Agent.agent_type == agent_type)
        if is_enabled is not None:
            query = query.filter(Agent.is_enabled == is_enabled)  # noqa: E712
        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                Agent.name.ilike(search_pattern)
                | Agent.description.ilike(search_pattern)
                | Agent.agent_key.ilike(search_pattern)
            )

        total = query.count()
        agents = query.order_by(Agent.created_at.desc()).offset(skip).limit(limit).all()
        return agents, total

    def create(self, data: AgentCreate) -> Agent:
        """Create a new agent."""
        # Check agent_key uniqueness
        existing = self.get_by_key(data.agent_key)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent with key '{data.agent_key}' already exists",
            )

        db_agent = Agent(
            agent_key=data.agent_key,
            name=data.name,
            description=data.description,
            agent_type=data.agent_type,
            category=data.category,
            is_enabled=data.is_enabled,
            default_llm_config_id=data.default_llm_config_id,
            default_params=data.default_params,
            version=data.version,
        )
        self.db.add(db_agent)
        self.db.commit()
        self.db.refresh(db_agent)
        return db_agent

    def update(self, agent_id: int, data: AgentUpdate) -> Agent:
        """Update an existing agent."""
        agent = self.get_by_id_or_404(agent_id)
        update_data = data.model_dump(exclude_unset=True)

        # If changing agent_key, check uniqueness
        if "agent_key" in update_data and update_data["agent_key"] != agent.agent_key:
            existing = self.get_by_key(update_data["agent_key"])
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Agent with key '{update_data['agent_key']}' already exists",
                )

        for field, value in update_data.items():
            setattr(agent, field, value)

        self.db.commit()
        self.db.refresh(agent)
        return agent

    def delete(self, agent_id: int) -> None:
        """Delete an agent."""
        agent = self.get_by_id_or_404(agent_id)
        self.db.delete(agent)
        self.db.commit()

    def set_enabled(self, agent_id: int, enabled: bool) -> Agent:
        """Enable or disable an agent."""
        agent = self.get_by_id_or_404(agent_id)
        agent.is_enabled = enabled
        self.db.commit()
        self.db.refresh(agent)
        return agent

    # ── Agent Run CRUD ────────────────────────────────────────────────────────

    def get_run_by_id(self, run_id: int) -> Optional[AgentRun]:
        """Get an agent run by ID."""
        return self.db.query(AgentRun).filter(AgentRun.id == run_id).first()

    def get_run_by_id_or_404(self, run_id: int) -> AgentRun:
        """Get an agent run by ID, raising 404 if not found."""
        run = self.get_run_by_id(run_id)
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent run with id {run_id} not found",
            )
        return run

    def get_run_detail(self, run_id: int) -> AgentRun:
        """Get an agent run with its steps (ordered by step_index)."""
        from sqlalchemy.orm import joinedload

        run = (
            self.db.query(AgentRun)
            .options(joinedload(AgentRun.steps))
            .filter(AgentRun.id == run_id)
            .first()
        )
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent run with id {run_id} not found",
            )
        return run

    def list_runs(
        self,
        skip: int = 0,
        limit: int = 100,
        agent_id: Optional[int] = None,
        project_id: Optional[int] = None,
        status: Optional[str] = None,
    ) -> tuple[List[AgentRun], int]:
        """List agent runs with pagination and filters."""
        query = self.db.query(AgentRun)

        if agent_id:
            query = query.filter(AgentRun.agent_id == agent_id)
        if project_id:
            query = query.filter(AgentRun.project_id == project_id)
        if status:
            query = query.filter(AgentRun.status == status)

        total = query.count()
        runs = query.order_by(AgentRun.created_at.desc()).offset(skip).limit(limit).all()
        return runs, total

    def create_run(self, data: AgentRunCreate) -> AgentRun:
        """Create a new agent run (status defaults to pending)."""
        db_run = AgentRun(
            agent_id=data.agent_id,
            project_id=data.project_id,
            status=data.status or RunStatus.PENDING,
            llm_config_id=data.llm_config_id,
            llm_model_name=data.llm_model_name,
            input_summary=data.input_summary,
            output_summary=data.output_summary,
            error_message=data.error_message,
            duration_ms=data.duration_ms,
            total_tokens=data.total_tokens,
        )
        self.db.add(db_run)
        self.db.commit()
        self.db.refresh(db_run)
        return db_run

    def update_run(self, run_id: int, data: AgentRunUpdate) -> AgentRun:
        """Update an agent run."""
        run = self.get_run_by_id_or_404(run_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(run, field, value)
        self.db.commit()
        self.db.refresh(run)
        return run

    def start_run(self, run_id: int) -> AgentRun:
        """Mark a run as started (status=running, set started_at)."""
        run = self.get_run_by_id_or_404(run_id)
        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run

    def complete_run(
        self,
        run_id: int,
        output_summary: Optional[str] = None,
        total_tokens: Optional[int] = None,
        duration_ms: Optional[int] = None,
    ) -> AgentRun:
        """Mark a run as completed."""
        run = self.get_run_by_id_or_404(run_id)
        run.status = RunStatus.COMPLETED
        run.finished_at = datetime.utcnow()
        if output_summary:
            run.output_summary = output_summary
        if total_tokens is not None:
            run.total_tokens = total_tokens
        if duration_ms is not None:
            run.duration_ms = duration_ms
        if run.started_at and run.finished_at and duration_ms is None:
            run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
        self.db.commit()
        self.db.refresh(run)
        return run

    def fail_run(self, run_id: int, error_message: str) -> AgentRun:
        """Mark a run as failed."""
        run = self.get_run_by_id_or_404(run_id)
        run.status = RunStatus.FAILED
        run.finished_at = datetime.utcnow()
        run.error_message = error_message
        if run.started_at and run.finished_at and run.duration_ms is None:
            run.duration_ms = int((run.finished_at - run.started_at).total_seconds() * 1000)
        self.db.commit()
        self.db.refresh(run)
        return run

    def cancel_run(self, run_id: int) -> AgentRun:
        """Mark a run as cancelled."""
        run = self.get_run_by_id_or_404(run_id)
        run.status = RunStatus.CANCELLED
        run.finished_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(run)
        return run

    # ── Agent Run Step CRUD ──────────────────────────────────────────────────

    def list_steps(self, run_id: int) -> List[AgentRunStep]:
        """List all steps for a run, ordered by step_index."""
        return (
            self.db.query(AgentRunStep)
            .filter(AgentRunStep.run_id == run_id)
            .order_by(AgentRunStep.step_index.asc(), AgentRunStep.created_at.asc())
            .all()
        )

    def create_step(self, run_id: int, data: AgentRunStepCreate) -> AgentRunStep:
        """Create a new run step."""
        # Ensure run exists
        self.get_run_by_id_or_404(run_id)
        db_step = AgentRunStep(
            run_id=run_id,
            step_name=data.step_name,
            step_index=data.step_index,
            status=data.status or StepStatus.PENDING,
            input_summary=data.input_summary,
            output_summary=data.output_summary,
            error_message=data.error_message,
            duration_ms=data.duration_ms,
            tokens_used=data.tokens_used,
        )
        self.db.add(db_step)
        self.db.commit()
        self.db.refresh(db_step)
        return db_step

    def update_step(self, step_id: int, data: AgentRunStepUpdate) -> AgentRunStep:
        """Update a run step."""
        step = self.db.query(AgentRunStep).filter(AgentRunStep.id == step_id).first()
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent run step with id {step_id} not found",
            )
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(step, field, value)
        self.db.commit()
        self.db.refresh(step)
        return step

    def start_step(
        self,
        run_id: int,
        step_name: str,
        step_index: int = 0,
        input_summary: Optional[str] = None,
    ) -> AgentRunStep:
        """Create a new step and mark it as running."""
        step_data = AgentRunStepCreate(
            step_name=step_name,
            step_index=step_index,
            status=StepStatus.RUNNING,
            input_summary=input_summary,
        )
        db_step = self.create_step(run_id, step_data)
        db_step.started_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(db_step)
        return db_step

    def complete_step(
        self,
        step_id: int,
        output_summary: Optional[str] = None,
        duration_ms: Optional[int] = None,
        tokens_used: Optional[int] = None,
    ) -> AgentRunStep:
        """Mark a step as completed."""
        step = self.db.query(AgentRunStep).filter(AgentRunStep.id == step_id).first()
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent run step with id {step_id} not found",
            )
        step.status = StepStatus.COMPLETED
        step.finished_at = datetime.utcnow()
        if output_summary:
            step.output_summary = output_summary
        if tokens_used is not None:
            step.tokens_used = tokens_used
        if step.started_at and step.finished_at and duration_ms is None:
            step.duration_ms = int((step.finished_at - step.started_at).total_seconds() * 1000)
        elif duration_ms is not None:
            step.duration_ms = duration_ms
        self.db.commit()
        self.db.refresh(step)
        return step

    def fail_step(self, step_id: int, error_message: str) -> AgentRunStep:
        """Mark a step as failed."""
        step = self.db.query(AgentRunStep).filter(AgentRunStep.id == step_id).first()
        if not step:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Agent run step with id {step_id} not found",
            )
        step.status = StepStatus.FAILED
        step.finished_at = datetime.utcnow()
        step.error_message = error_message
        if step.started_at and step.finished_at and step.duration_ms is None:
            step.duration_ms = int((step.finished_at - step.started_at).total_seconds() * 1000)
        self.db.commit()
        self.db.refresh(step)
        return step

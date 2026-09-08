"""Integration tests for agent run persistence and LangGraph step tracking."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.agents.base import BaseAgent
from app.models.agent import AgentRun, RunStatus
from app.models.llm_config import LLMConfig
from app.models.project import Project
from app.schemas.agent import AgentCreate, AgentRunCreate
from app.services.agent_service import AgentService


class _State(TypedDict):
    value: int


class _TestAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "test"

    @property
    def description(self) -> str:
        return "test"

    def build_graph(self):
        graph = StateGraph(_State)
        graph.add_node("first", lambda state: {"value": state["value"] + 1})
        graph.add_node("second", lambda state: {"value": state["value"] + 1})
        graph.add_edge(START, "first")
        graph.add_edge("first", "second")
        graph.add_edge("second", END)
        return graph


class _NestedAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "nested"

    @property
    def description(self) -> str:
        return "nested"

    def build_graph(self):
        inner = StateGraph(_State)
        inner.add_node("inner", lambda state: {"value": state["value"] + 1})
        inner.add_edge(START, "inner")
        inner.add_edge("inner", END)
        inner_graph = inner.compile()

        outer = StateGraph(_State)
        outer.add_node("outer", lambda state: inner_graph.invoke(state))
        outer.add_edge(START, "outer")
        outer.add_edge("outer", END)
        return outer


def test_invoke_with_run_records_only_graph_nodes(db_session):
    result, run_id = _TestAgent(llm=None).invoke_with_run({"value": 0}, db_session)

    assert result == {"value": 2}
    run = db_session.get(AgentRun, run_id)
    assert run.status == RunStatus.COMPLETED
    assert run.started_at is not None
    assert run.finished_at is not None
    assert [(step.step_name, step.step_index) for step in run.steps] == [
        ("first", 1),
        ("second", 1),
    ]
    assert all(step.status.value == "completed" for step in run.steps)


def test_deleting_agent_preserves_run_history(db_session):
    service = AgentService(db_session)
    agent = service.create(
        AgentCreate(agent_key="temporary", name="临时智能体", agent_type="测试")
    )
    run = service.create_run(AgentRunCreate(agent_id=agent.id))

    service.delete(agent.id)
    db_session.expire_all()

    preserved = db_session.get(AgentRun, run.id)
    assert preserved is not None
    assert preserved.agent_id is None


def test_nested_graph_is_recorded_as_one_parent_step(db_session):
    _, run_id = _NestedAgent(llm=None).invoke_with_run({"value": 0}, db_session)

    run = db_session.get(AgentRun, run_id)
    assert [step.step_name for step in run.steps] == ["outer"]


def test_agent_default_llm_takes_precedence_over_global_default(db_session):
    global_default = LLMConfig(
        name="global",
        provider="openai",
        model_type="text",
        model_name="global-model",
        api_key="key",
        is_default=True,
    )
    agent_default = LLMConfig(
        name="agent",
        provider="openai",
        model_type="text",
        model_name="agent-model",
        api_key="key",
    )
    db_session.add_all([global_default, agent_default])
    db_session.commit()
    service = AgentService(db_session)
    agent = service.create(
        AgentCreate(
            agent_key="configured",
            name="配置智能体",
            agent_type="测试",
            default_llm_config_id=agent_default.id,
        )
    )

    assert service.resolve_llm_config(agent).id == agent_default.id
    assert service.resolve_llm_config(agent, global_default.id).id == global_default.id


def test_disabled_agent_cannot_resolve_llm_config(db_session):
    service = AgentService(db_session)
    agent = service.create(
        AgentCreate(
            agent_key="disabled", name="禁用智能体", agent_type="测试", is_enabled=False
        )
    )

    try:
        service.resolve_llm_config(agent)
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 409
    else:
        raise AssertionError("disabled agent should not be executable")


def test_agent_default_params_only_fill_omitted_request_values(db_session):
    service = AgentService(db_session)
    agent = service.create(
        AgentCreate(
            agent_key="defaults",
            name="默认参数智能体",
            agent_type="测试",
            default_params={"genre": "悬疑", "num_scenes": 6},
        )
    )

    result = service.resolve_params(
        agent,
        {"genre": "都市", "style": None, "num_scenes": 10},
        provided_fields={"num_scenes"},
    )

    assert result == {"genre": "悬疑", "style": None, "num_scenes": 10}


def test_run_api_filters_by_project(client, db_session):
    project_a = Project(name="A")
    project_b = Project(name="B")
    db_session.add_all([project_a, project_b])
    db_session.commit()
    service = AgentService(db_session)
    service.create_run(AgentRunCreate(project_id=project_a.id))
    service.create_run(AgentRunCreate(project_id=project_b.id))

    response = client.get("/api/v1/agent-runs", params={"project_id": project_a.id})

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["project_id"] == project_a.id

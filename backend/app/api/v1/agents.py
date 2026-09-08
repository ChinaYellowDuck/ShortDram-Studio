"""Agent execution endpoints."""
from fastapi import APIRouter, HTTPException, status

from app.api.deps import AgentServiceDep, ProjectServiceDep, ScriptServiceDep
from app.models.script import CharacterType, Emotion, IntExt, TimeOfDay
from app.schemas.llm_config import LLMConfigResponse
from app.schemas.project import ProjectCreate
from app.schemas.script import (
    ScriptCharacterCreate,
    ScriptCreate,
    ScriptDialogueCreate,
    ScriptGenerateRequest,
    ScriptRefineRequest,
    ScriptSceneCreate,
)

router = APIRouter()


def _screenwriter_state(idea: str, genre: str, style: str, num_scenes: int) -> dict:
    """Build the initial state for the screenwriter graph."""
    return {
        "idea": idea,
        "genre": genre,
        "style": style or "",
        "num_scenes": num_scenes,
        "logline": "",
        "synopsis": "",
        "characters": [],
        "scene_outlines": [],
        "current_scene_index": 0,
        "scenes": [],
        "review": {},
        "current_stage": "starting",
        "error": "",
    }


def _producer_state(
    idea: str, genre: str, style: str, num_scenes: int, llm
) -> dict:
    """Build the initial state for the producer graph."""
    project_name = idea[:20].strip() + "..." if len(idea) > 20 else idea
    return {
        "project_name": project_name,
        "idea": idea,
        "genre": genre,
        "style": style or "",
        "num_scenes": num_scenes,
        "llm": llm,
        "validation": {},
        "script_result": {},
        "current_stage": "starting",
        "error": "",
    }


@router.get("/list", summary="获取可用智能体列表")
def list_agents(service: AgentServiceDep):
    """List all enabled agents from the database."""
    agents, _ = service.list_agents(is_enabled=True, limit=100)
    return [
        {
            "id": agent.id,
            "agent_key": agent.agent_key,
            "name": agent.name,
            "description": agent.description or "",
            "status": "available" if agent.is_enabled else "disabled",
            "category": agent.category or "",
            "default_llm_config_id": agent.default_llm_config_id,
        }
        for agent in agents
    ]


# ── Generic Agent Chat ──────────────────────────────────────────────────────


@router.post("/chat", summary="智能体对话测试")
async def agent_chat(
    agent_service: AgentServiceDep,
    agent_key: str,
    message: str,
    llm_config_id: int | None = None,
):
    """Run a conversation-style test against any agent.

    For dialog agents the message is used directly; for creative agents the
    message is treated as the creative idea.
    """
    run_id: int | None = None
    try:
        from app.agents.llm import LLMFactory

        agent_meta = agent_service.get_by_key_or_404(agent_key)
        config = agent_service.resolve_llm_config(agent_meta, llm_config_id)
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        agent_id = agent_meta.id
        llm_config_id = config.id
        llm_model_name = config.model_name

        if agent_key == "hello_agent":
            from langchain_core.messages import HumanMessage

            from app.agents.hello_agent import HelloAgent

            agent = HelloAgent(llm)
            input_data = {"messages": [HumanMessage(content=message)]}
            result, run_id = await agent.ainvoke_with_run(
                input_data=input_data,
                db=agent_service.db,
                agent_id=agent_id,
                llm_config_id=llm_config_id,
                llm_model_name=llm_model_name,
            )
            response = result.get("greeting", "")

        elif agent_key == "screenwriter":
            from app.agents.screenwriter import ScreenwriterAgent

            params = agent_service.resolve_params(
                agent_meta,
                {"genre": "都市", "style": "", "num_scenes": 3},
                provided_fields=set(),
            )
            agent = ScreenwriterAgent(llm)
            input_data = _screenwriter_state(
                message, params["genre"], params["style"], params["num_scenes"]
            )
            result, run_id = await agent.ainvoke_with_run(
                input_data=input_data,
                db=agent_service.db,
                agent_id=agent_id,
                llm_config_id=llm_config_id,
                llm_model_name=llm_model_name,
            )
            response = "\n\n".join(
                part for part in (result.get("logline"), result.get("synopsis")) if part
            ).strip()

        elif agent_key == "producer":
            from app.agents.producer import ProducerAgent

            params = agent_service.resolve_params(
                agent_meta,
                {"genre": "都市", "style": "", "num_scenes": 3},
                provided_fields=set(),
            )
            agent = ProducerAgent(llm)
            input_data = _producer_state(
                message, params["genre"], params["style"], params["num_scenes"], llm
            )
            result, run_id = await agent.ainvoke_with_run(
                input_data=input_data,
                db=agent_service.db,
                agent_id=agent_id,
                llm_config_id=llm_config_id,
                llm_model_name=llm_model_name,
            )
            script = result.get("script_result", {})
            response = "\n".join(
                part
                for part in (
                    f"项目：{result.get('project_name', '')}",
                    f"梗概：{script.get('logline', '')}",
                    f"大纲：{script.get('synopsis', '')}",
                )
                if part
            ).strip()

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Agent '{agent_key}' does not support chat",
            )

        return {
            "agent": agent_key,
            "run_id": run_id,
            "message": message,
            "response": response,
            "llm_config": {
                "id": config.id,
                "name": config.name,
                "provider": config.provider,
                "model": config.model_name,
            },
        }

    except HTTPException:
        raise
    except ImportError as e:
        if run_id is not None:
            agent_service.fail_run(run_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent dependencies not available: {e}",
        ) from e
    except Exception as e:
        if run_id is not None:
            agent_service.fail_run(run_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent chat failed: {str(e)}",
        ) from e


# ── Hello Agent ─────────────────────────────────────────────────────────────


@router.post("/hello/chat", summary="Hello Agent 对话（测试用）")
async def hello_agent_chat(
    agent_service: AgentServiceDep,
    message: str,
    llm_config_id: int | None = None,
):
    """
    Test the Hello Agent with a message.

    - **message**: 用户输入消息
    - **llm_config_id**: 可选，使用指定的 LLM 配置；不传则使用默认配置
    """
    try:
        from langchain_core.messages import HumanMessage

        from app.agents.hello_agent import HelloAgent
        from app.agents.llm import LLMFactory

        # Look up agent metadata
        agent_meta = agent_service.get_by_key_or_404("hello_agent")
        agent_id = agent_meta.id
        config = agent_service.resolve_llm_config(agent_meta, llm_config_id)

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        # Create agent and invoke with run recording
        agent = HelloAgent(llm)
        input_data = {"messages": [HumanMessage(content=message)]}
        result, run_id = await agent.ainvoke_with_run(
            input_data=input_data,
            db=agent_service.db,
            agent_id=agent_id,
            project_id=None,
            llm_config_id=config.id,
            llm_model_name=config.model_name,
        )

        return {
            "agent": "hello_agent",
            "run_id": run_id,
            "message": message,
            "response": result.get("greeting", ""),
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


# ── Screenwriter Agent ──────────────────────────────────────────────────────


@router.post("/screenwriter/generate", summary="编剧智能体：生成剧本")
async def screenwriter_generate(
    req: ScriptGenerateRequest,
    agent_service: AgentServiceDep,
):
    """
    Generate a complete script from a creative idea using the screenwriter agent.

    - **idea**: 创意描述
    - **genre**: 题材（都市/仙侠/甜宠/悬疑/重生 等）
    - **style**: 风格（可选）
    - **num_scenes**: 生成场景数量（默认10）
    - **llm_config_id**: 可选，指定LLM配置
    """
    run_id: int | None = None
    try:
        from app.agents.llm import LLMFactory
        from app.agents.screenwriter import ScreenwriterAgent

        # Look up agent metadata
        agent_meta = agent_service.get_by_key_or_404("screenwriter")
        agent_id = agent_meta.id
        config = agent_service.resolve_llm_config(agent_meta, req.llm_config_id)

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        # Apply the agent's stored defaults only for fields the caller omitted.
        provided_fields = set(req.model_fields_set)
        params = agent_service.resolve_params(
            agent_meta,
            {"genre": req.genre, "style": req.style, "num_scenes": req.num_scenes},
            provided_fields=provided_fields,
        )

        # Build initial state
        initial_state = {
            "idea": req.idea,
            "genre": params["genre"],
            "style": params["style"] or "",
            "num_scenes": params["num_scenes"],
            "logline": "",
            "synopsis": "",
            "characters": [],
            "scene_outlines": [],
            "current_scene_index": 0,
            "scenes": [],
            "review": {},
            "current_stage": "starting",
            "error": "",
        }

        # Create agent and invoke with run recording
        agent = ScreenwriterAgent(llm)
        result, run_id = await agent.ainvoke_with_run(
            input_data=initial_state,
            db=agent_service.db,
            agent_id=agent_id,
            project_id=None,
            llm_config_id=config.id,
            llm_model_name=config.model_name,
        )

        return {
            "agent": "screenwriter",
            "run_id": run_id,
            "llm_config": {
                "id": config.id,
                "name": config.name,
                "provider": config.provider,
                "model": config.model_name,
            },
            "result": {
                "logline": result.get("logline", ""),
                "synopsis": result.get("synopsis", ""),
                "genre": result.get("genre", ""),
                "style": result.get("style", ""),
                "characters": result.get("characters", []),
                "scenes": result.get("scenes", []),
                "review": result.get("review", {}),
                "current_stage": result.get("current_stage", ""),
                "error": result.get("error", ""),
            },
        }

    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent dependencies not available: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Script generation failed: {str(e)}",
        ) from e


@router.post("/screenwriter/refine", summary="编剧智能体：打磨场景/剧本")
async def screenwriter_refine(
    req: ScriptRefineRequest,
    script_service: ScriptServiceDep,
    agent_service: AgentServiceDep,
):
    """
    Refine a specific scene or the whole script based on feedback.

    - **script_id**: 剧本ID
    - **scene_id**: 可选，场景ID；不填则打磨整个剧本（v0.1仅支持单场景打磨）
    - **feedback**: 修改意见/反馈
    - **llm_config_id**: 可选，指定LLM配置
    """
    import time

    from app.schemas.agent import AgentRunCreate, AgentRunStepCreate

    try:
        from app.agents.llm import LLMFactory
        from app.agents.screenwriter import ScreenwriterAgent

        # Look up agent metadata
        agent_meta = agent_service.get_by_key_or_404("screenwriter")
        agent_id = agent_meta.id

        # Get script for context
        script = script_service.get_detail(req.script_id)

        # Get scene to refine
        if not req.scene_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="v0.1 仅支持单场景打磨，请指定 scene_id",
            )

        scene = script_service.get_scene_detail(req.scene_id)

        # Build context
        characters = [
            {
                "name": c.name,
                "role": c.character_type.value,
                "description": c.description or "",
                "personality": c.appearance or "",
            }
            for c in script.characters
        ]

        # Find prev/next scene summaries
        all_scenes = script_service.list_scenes(req.script_id)
        current_idx = next(
            (i for i, s in enumerate(all_scenes) if s.id == req.scene_id), -1
        )
        prev_summary = (
            all_scenes[current_idx - 1].description if current_idx > 0 else "（开场）"
        )
        next_summary = (
            all_scenes[current_idx + 1].description
            if current_idx < len(all_scenes) - 1
            else "（结尾）"
        )

        scene_data = {
            "scene_number": scene.scene_number,
            "location": scene.location,
            "int_ext": scene.int_ext.value,
            "time_of_day": scene.time_of_day.value,
            "description": scene.description or "",
            "key_characters": list({d.character_name for d in scene.dialogues}),
            "dialogues": [
                {
                    "character_name": d.character_name,
                    "dialogue": d.dialogue,
                    "action": d.action or "",
                    "emotion": d.emotion.value,
                }
                for d in scene.dialogues
            ],
        }

        context = {
            "logline": script.logline or "",
            "genre": script.genre or "",
            "style": script.style or "",
            "characters": characters,
            "prev_scene_summary": prev_summary or "（无）",
            "next_scene_summary": next_summary or "（无）",
        }

        # Get LLM config
        config = agent_service.resolve_llm_config(agent_meta, req.llm_config_id)

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        # ── Create agent run record (refine is a single-step LLM call) ──
        run = agent_service.create_run(
            AgentRunCreate(
                agent_id=agent_id,
                project_id=script.project_id,
                llm_config_id=config.id,
                llm_model_name=config.model_name,
                input_summary=f"Refine scene {scene.scene_number}: {req.feedback[:200]}",
            )
        )
        run_id = run.id
        agent_service.start_run(run_id)

        # Create a single step for the refine operation
        step = agent_service.start_step(
            run_id=run_id,
            step_name="refine_scene",
            step_index=0,
            input_summary=f"Scene {scene.scene_number} - feedback: {req.feedback[:200]}",
        )

        start_time = time.time()
        try:
            # Refine
            agent = ScreenwriterAgent(llm)
            refined = await agent.arefine_scene(scene_data, req.feedback, context)

            duration_ms = int((time.time() - start_time) * 1000)
            agent_service.complete_step(step.id, duration_ms=duration_ms)
            agent_service.complete_run(
                run_id,
                output_summary=f"Refined scene {scene.scene_number} successfully",
                duration_ms=duration_ms,
            )

            return {
                "agent": "screenwriter",
                "run_id": run_id,
                "action": "refine_scene",
                "scene_id": req.scene_id,
                "feedback": req.feedback,
                "llm_config": {
                    "id": config.id,
                    "name": config.name,
                    "provider": config.provider,
                    "model": config.model_name,
                },
                "refined_scene": refined,
            }

        except HTTPException:
            raise
        except ImportError as e:
            agent_service.fail_step(step.id, str(e))
            agent_service.fail_run(run_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Agent dependencies not available: {e}",
            ) from e
        except Exception as e:
            agent_service.fail_step(step.id, str(e))
            agent_service.fail_run(run_id, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Scene refinement failed: {str(e)}",
            ) from e

    except HTTPException:
        raise
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent dependencies not available: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scene refinement failed: {str(e)}",
        ) from e


# ── Producer Agent ──────────────────────────────────────────────────────────


@router.post("/producer/create-project", summary="制片人智能体：从创意创建项目")
async def producer_create_project(
    req: ScriptGenerateRequest,
    project_service: ProjectServiceDep,
    script_service: ScriptServiceDep,
    agent_service: AgentServiceDep,
):
    """
    Create a complete project with script from a creative idea in one click.

    This runs the full producer pipeline:
    1. Validate the idea
    2. Generate script via screenwriter agent
    3. Save project and script to database

    - **idea**: 创意描述
    - **genre**: 题材
    - **style**: 风格（可选）
    - **num_scenes**: 场景数量
    - **llm_config_id**: 可选，指定LLM配置
    """
    try:
        from app.agents.llm import LLMFactory
        from app.agents.producer import ProducerAgent

        # Look up agent metadata
        agent_meta = agent_service.get_by_key_or_404("producer")
        agent_id = agent_meta.id
        config = agent_service.resolve_llm_config(agent_meta, req.llm_config_id)

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        # Generate project name from idea
        project_name = req.idea[:30].strip()
        if len(req.idea) > 30:
            project_name += "..."

        # Create agent
        agent = ProducerAgent(llm)

        # Build initial state for the producer graph
        initial_state = {
            "project_name": project_name,
            "idea": req.idea,
            "genre": req.genre,
            "style": req.style or "",
            "num_scenes": req.num_scenes,
            "llm": llm,
            "validation": {},
            "script_result": {},
            "current_stage": "starting",
            "error": "",
        }

        # Run producer agent with run recording
        # Note: project_id will be set after project creation (below)
        result, run_id = await agent.ainvoke_with_run(
            input_data=initial_state,
            db=agent_service.db,
            agent_id=agent_id,
            project_id=None,  # project doesn't exist yet
            llm_config_id=config.id,
            llm_model_name=config.model_name,
        )

        # Check for errors
        if result.get("error"):
            agent_service.fail_run(run_id, result["error"])
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        script_result = result.get("script_result", {})

        # Save project to database
        project = project_service.create(
            ProjectCreate(
                name=result["project_name"],
                description=script_result.get("logline", req.idea),
            )
        )

        # Update agent run with project_id now that it exists
        from app.schemas.agent import AgentRunUpdate
        agent_service.update_run(run_id, AgentRunUpdate(project_id=project.id))

        # Save script to database
        script = script_service.create(
            ScriptCreate(
                project_id=project.id,
                title=result["project_name"],
                logline=script_result.get("logline", ""),
                genre=script_result.get("genre", req.genre),
                style=script_result.get("style", req.style),
                synopsis=script_result.get("synopsis", ""),
                total_episodes=1,
                version="v0.1",
            )
        )

        # Save characters
        char_id_map = {}  # character_name -> character_id
        for char_data in script_result.get("characters", []):
            char_type_str = char_data.get("role", "配角")
            # Map role string to CharacterType enum
            type_map = {
                "主角": CharacterType.LEAD,
                "主演": CharacterType.LEAD,
                "LEAD": CharacterType.LEAD,
                "lead": CharacterType.LEAD,
                "配角": CharacterType.SUPPORTING,
                "SUPPORTING": CharacterType.SUPPORTING,
                "supporting": CharacterType.SUPPORTING,
                "客串": CharacterType.CAMEO,
                "CAMEO": CharacterType.CAMEO,
                "cameo": CharacterType.CAMEO,
                "龙套": CharacterType.EXTRA,
                "EXTRA": CharacterType.EXTRA,
                "extra": CharacterType.EXTRA,
            }
            char_type = type_map.get(char_type_str, CharacterType.SUPPORTING)

            char = script_service.create_character(
                script.id,
                ScriptCharacterCreate(
                    name=char_data.get("name", "未知角色"),
                    description=char_data.get("description", ""),
                    character_type=char_type,
                    age=char_data.get("age", ""),
                    appearance=char_data.get("personality", char_data.get("appearance", "")),
                ),
            )
            char_id_map[char.name] = char.id

        # Save scenes and dialogues
        for scene_data in script_result.get("scenes", []):
            int_ext_str = scene_data.get("int_ext", "INT")
            int_ext_map = {
                "INT": IntExt.INT,
                "内景": IntExt.INT,
                "内": IntExt.INT,
                "EXT": IntExt.EXT,
                "外景": IntExt.EXT,
                "外": IntExt.EXT,
                "INT/EXT": IntExt.INT_EXT,
                "内外景": IntExt.INT_EXT,
            }
            int_ext = int_ext_map.get(int_ext_str.upper(), IntExt.INT)

            time_str = scene_data.get("time_of_day", "日")
            time_map = {
                "日": TimeOfDay.DAY,
                "白天": TimeOfDay.DAY,
                "DAY": TimeOfDay.DAY,
                "夜": TimeOfDay.NIGHT,
                "晚上": TimeOfDay.NIGHT,
                "NIGHT": TimeOfDay.NIGHT,
                "晨": TimeOfDay.DAWN,
                "清晨": TimeOfDay.DAWN,
                "DAWN": TimeOfDay.DAWN,
                "昏": TimeOfDay.DUSK,
                "黄昏": TimeOfDay.DUSK,
                "DUSK": TimeOfDay.DUSK,
            }
            time_of_day = time_map.get(time_str, TimeOfDay.DAY)

            scene = script_service.create_scene(
                script.id,
                ScriptSceneCreate(
                    scene_number=str(scene_data.get("scene_number", "")),
                    location=scene_data.get("location", "未知地点"),
                    int_ext=int_ext,
                    time_of_day=time_of_day,
                    description=scene_data.get("description", ""),
                    order_index=scene_data.get("order_index", 0),
                ),
            )

            # Save dialogues
            for dlg_data in scene_data.get("dialogues", []):
                char_name = dlg_data.get("character_name", "旁白")
                emotion_str = dlg_data.get("emotion", "正常")
                emotion_map = {e.value: e for e in Emotion}
                emotion = emotion_map.get(emotion_str, Emotion.NORMAL)

                script_service.create_dialogue(
                    scene.id,
                    ScriptDialogueCreate(
                        character_name=char_name,
                        character_id=char_id_map.get(char_name),
                        dialogue=dlg_data.get("dialogue", ""),
                        action=dlg_data.get("action", ""),
                        emotion=emotion,
                    ),
                )

        # Return full result
        return {
            "agent": "producer",
            "run_id": run_id,
            "project_id": project.id,
            "script_id": script.id,
            "validation": result.get("validation", {}),
            "llm_config": {
                "id": config.id,
                "name": config.name,
                "provider": config.provider,
                "model": config.model_name,
            },
            "result": {
                "project_name": result["project_name"],
                "logline": script_result.get("logline", ""),
                "synopsis": script_result.get("synopsis", ""),
                "num_characters": len(script_result.get("characters", [])),
                "num_scenes": len(script_result.get("scenes", [])),
                "review": script_result.get("review", {}),
            },
            "current_stage": result.get("current_stage", ""),
        }

    except HTTPException:
        raise
    except ImportError as e:
        if run_id is not None:
            agent_service.fail_run(run_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent dependencies not available: {e}",
        ) from e
    except Exception as e:
        if run_id is not None:
            agent_service.fail_run(run_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project creation failed: {str(e)}",
        ) from e

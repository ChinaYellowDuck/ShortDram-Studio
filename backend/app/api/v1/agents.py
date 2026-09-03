"""Agent execution endpoints."""
from fastapi import APIRouter, HTTPException, status

from app.api.deps import LLMConfigServiceDep, ProjectServiceDep, ScriptServiceDep
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


@router.get("/list", summary="获取可用智能体列表")
def list_agents():
    """List all available agents with descriptions."""
    return [
        {
            "id": "hello_agent",
            "name": "Hello Agent",
            "description": "简单的问候智能体，用于测试智能体框架是否正常工作",
            "status": "available",
            "category": "测试",
        },
        {
            "id": "screenwriter",
            "name": "编剧智能体",
            "description": "从创意生成完整短剧剧本，支持场景大纲、对白撰写、多轮打磨",
            "status": "available",
            "category": "创作",
        },
        {
            "id": "producer",
            "name": "制片人智能体",
            "description": "统筹短剧制作全流程，一键从创意生成完整剧本项目",
            "status": "available",
            "category": "协调",
        },
    ]


# ── Hello Agent ─────────────────────────────────────────────────────────────


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

        # Get LLM config
        if llm_config_id:
            config = service.get_by_id_or_404(llm_config_id)
        else:
            config = service.get_default_or_404()

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
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


# ── Screenwriter Agent ──────────────────────────────────────────────────────


@router.post("/screenwriter/generate", summary="编剧智能体：生成剧本")
async def screenwriter_generate(
    req: ScriptGenerateRequest,
    llm_service: LLMConfigServiceDep,
):
    """
    Generate a complete script from a creative idea using the screenwriter agent.

    - **idea**: 创意描述
    - **genre**: 题材（都市/仙侠/甜宠/悬疑/重生 等）
    - **style**: 风格（可选）
    - **num_scenes**: 生成场景数量（默认10）
    - **llm_config_id**: 可选，指定LLM配置
    """
    try:
        from app.agents.llm import LLMFactory
        from app.agents.screenwriter import ScreenwriterAgent

        # Get LLM config
        if req.llm_config_id:
            config = llm_service.get_by_id_or_404(req.llm_config_id)
        else:
            config = llm_service.get_default_or_404()

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        # Create agent and generate
        agent = ScreenwriterAgent(llm)
        result = await agent.agenerate_script(
            idea=req.idea,
            genre=req.genre,
            style=req.style,
            num_scenes=req.num_scenes,
        )

        return {
            "agent": "screenwriter",
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
    llm_service: LLMConfigServiceDep,
    script_service: ScriptServiceDep,
):
    """
    Refine a specific scene or the whole script based on feedback.

    - **script_id**: 剧本ID
    - **scene_id**: 可选，场景ID；不填则打磨整个剧本（v0.1仅支持单场景打磨）
    - **feedback**: 修改意见/反馈
    - **llm_config_id**: 可选，指定LLM配置
    """
    try:
        from app.agents.llm import LLMFactory
        from app.agents.screenwriter import ScreenwriterAgent

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
        if req.llm_config_id:
            config = llm_service.get_by_id_or_404(req.llm_config_id)
        else:
            config = llm_service.get_default_or_404()

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        # Refine
        agent = ScreenwriterAgent(llm)
        refined = await agent.arefine_scene(scene_data, req.feedback, context)

        return {
            "agent": "screenwriter",
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
    llm_service: LLMConfigServiceDep,
    project_service: ProjectServiceDep,
    script_service: ScriptServiceDep,
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

        # Get LLM config
        if req.llm_config_id:
            config = llm_service.get_by_id_or_404(req.llm_config_id)
        else:
            config = llm_service.get_default_or_404()

        # Create LLM instance
        llm = LLMFactory.create_from_config(
            LLMConfigResponse.model_validate(config),
            config.api_key,
        )

        # Generate project name from idea
        project_name = req.idea[:30].strip()
        if len(req.idea) > 30:
            project_name += "..."

        # Run producer agent
        agent = ProducerAgent(llm)
        result = await agent.acreate_project_from_idea(
            idea=req.idea,
            project_name=project_name,
            genre=req.genre,
            style=req.style,
            num_scenes=req.num_scenes,
        )

        # Check for errors
        if result.get("error"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"],
            )

        script_result = result.get("script", {})

        # Save project to database
        project = project_service.create(
            ProjectCreate(
                name=result["project_name"],
                description=script_result.get("logline", req.idea),
            )
        )

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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent dependencies not available: {e}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project creation failed: {str(e)}",
        ) from e

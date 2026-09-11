"""Script service - business logic for script management.

Handles CRUD for scripts, scenes, characters, dialogues,
and provides Fountain format export.
"""
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session, joinedload

from app.models.script import (
    Script,
    ScriptCharacter,
    ScriptDialogue,
    ScriptEpisode,
    ScriptGenerationStage,
    ScriptScene,
)
from app.schemas.script import (
    ScriptCharacterCreate,
    ScriptCharacterUpdate,
    ScriptCreate,
    ScriptDialogueCreate,
    ScriptDialogueUpdate,
    ScriptEpisodeCreate,
    ScriptEpisodeUpdate,
    ScriptSceneCreate,
    ScriptSceneUpdate,
    ScriptUpdate,
)
import re


class ScriptService:
    """Service for managing scripts, scenes, characters, and dialogues."""

    def __init__(self, db: Session):
        self.db = db

    # ── Script CRUD ────────────────────────────────────────────────────────

    def get_by_id(self, script_id: int) -> Optional[Script]:
        """Get a script by ID."""
        return self.db.query(Script).filter(Script.id == script_id).first()

    def get_by_id_or_404(self, script_id: int) -> Script:
        """Get a script by ID, raising 404 if not found."""
        script = self.get_by_id(script_id)
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Script with id {script_id} not found",
            )
        return script

    def get_detail(self, script_id: int) -> Script:
        """Get a script with all scenes, dialogues, and characters loaded."""
        script = (
            self.db.query(Script)
            .options(
                joinedload(Script.scenes).joinedload(ScriptScene.dialogues),
                joinedload(Script.characters),
            )
            .filter(Script.id == script_id)
            .first()
        )
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Script with id {script_id} not found",
            )
        return script

    def list_by_project(
        self, project_id: int, skip: int = 0, limit: int = 100
    ) -> Tuple[List[Script], int]:
        """List scripts for a project with pagination."""
        query = self.db.query(Script).filter(Script.project_id == project_id)
        total = query.count()
        scripts = query.order_by(Script.updated_at.desc()).offset(skip).limit(limit).all()
        return scripts, total

    def create(self, data: ScriptCreate) -> Script:
        """Create a new script."""
        script = Script(
            project_id=data.project_id,
            title=data.title,
            logline=data.logline,
            genre=data.genre,
            style=data.style,
            total_episodes=data.total_episodes,
            synopsis=data.synopsis,
            version=data.version,
        )
        self.db.add(script)
        self.db.commit()
        self.db.refresh(script)
        return script

    def update(self, script_id: int, data: ScriptUpdate) -> Script:
        """Update a script."""
        script = self.get_by_id_or_404(script_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(script, field, value)
        self.db.commit()
        self.db.refresh(script)
        return script

    def delete(self, script_id: int) -> None:
        """Delete a script."""
        script = self.get_by_id_or_404(script_id)
        self.db.delete(script)
        self.db.commit()

    # ── Scene CRUD ─────────────────────────────────────────────────────────

    def get_scene(self, scene_id: int) -> Optional[ScriptScene]:
        """Get a scene by ID."""
        return self.db.query(ScriptScene).filter(ScriptScene.id == scene_id).first()

    def get_scene_or_404(self, scene_id: int) -> ScriptScene:
        """Get a scene by ID, raising 404 if not found."""
        scene = self.get_scene(scene_id)
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scene with id {scene_id} not found",
            )
        return scene

    def get_scene_detail(self, scene_id: int) -> ScriptScene:
        """Get a scene with dialogues loaded."""
        scene = (
            self.db.query(ScriptScene)
            .options(joinedload(ScriptScene.dialogues))
            .filter(ScriptScene.id == scene_id)
            .first()
        )
        if not scene:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Scene with id {scene_id} not found",
            )
        return scene

    def list_scenes(self, script_id: int) -> List[ScriptScene]:
        """List all scenes for a script, ordered by order_index."""
        return (
            self.db.query(ScriptScene)
            .filter(ScriptScene.script_id == script_id)
            .order_by(ScriptScene.order_index.asc())
            .all()
        )

    def create_scene(self, script_id: int, data: ScriptSceneCreate) -> ScriptScene:
        """Create a new scene in a script."""
        # Verify script exists
        self.get_by_id_or_404(script_id)

        # Auto-assign order_index if not provided
        order_index = data.order_index
        if order_index == 0:
            max_order = (
                self.db.query(ScriptScene)
                .filter(ScriptScene.script_id == script_id)
                .count()
            )
            order_index = max_order

        scene = ScriptScene(
            script_id=script_id,
            scene_number=data.scene_number,
            location=data.location,
            int_ext=data.int_ext,
            time_of_day=data.time_of_day,
            description=data.description,
            order_index=order_index,
        )
        self.db.add(scene)
        self.db.commit()
        self.db.refresh(scene)
        return scene

    def update_scene(self, scene_id: int, data: ScriptSceneUpdate) -> ScriptScene:
        """Update a scene."""
        scene = self.get_scene_or_404(scene_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scene, field, value)
        self.db.commit()
        self.db.refresh(scene)
        return scene

    def delete_scene(self, scene_id: int) -> None:
        """Delete a scene."""
        scene = self.get_scene_or_404(scene_id)
        self.db.delete(scene)
        self.db.commit()

    # ── Character CRUD ────────────────────────────────────────────────────

    def get_character(self, character_id: int) -> Optional[ScriptCharacter]:
        """Get a character by ID."""
        return (
            self.db.query(ScriptCharacter)
            .filter(ScriptCharacter.id == character_id)
            .first()
        )

    def get_character_or_404(self, character_id: int) -> ScriptCharacter:
        """Get a character by ID, raising 404 if not found."""
        character = self.get_character(character_id)
        if not character:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Character with id {character_id} not found",
            )
        return character

    def list_characters(self, script_id: int) -> List[ScriptCharacter]:
        """List all characters in a script."""
        return (
            self.db.query(ScriptCharacter)
            .filter(ScriptCharacter.script_id == script_id)
            .order_by(ScriptCharacter.id.asc())
            .all()
        )

    def create_character(
        self, script_id: int, data: ScriptCharacterCreate
    ) -> ScriptCharacter:
        """Create a new character in a script."""
        self.get_by_id_or_404(script_id)
        character = ScriptCharacter(
            script_id=script_id,
            name=data.name,
            description=data.description,
            character_type=data.character_type,
            age=data.age,
            appearance=data.appearance,
        )
        self.db.add(character)
        self.db.commit()
        self.db.refresh(character)
        return character

    def update_character(
        self, character_id: int, data: ScriptCharacterUpdate
    ) -> ScriptCharacter:
        """Update a character."""
        character = self.get_character_or_404(character_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(character, field, value)
        self.db.commit()
        self.db.refresh(character)
        return character

    def delete_character(self, character_id: int) -> None:
        """Delete a character."""
        character = self.get_character_or_404(character_id)
        self.db.delete(character)
        self.db.commit()

    # ── Dialogue CRUD ──────────────────────────────────────────────────────

    def get_dialogue(self, dialogue_id: int) -> Optional[ScriptDialogue]:
        """Get a dialogue by ID."""
        return (
            self.db.query(ScriptDialogue)
            .filter(ScriptDialogue.id == dialogue_id)
            .first()
        )

    def get_dialogue_or_404(self, dialogue_id: int) -> ScriptDialogue:
        """Get a dialogue by ID, raising 404 if not found."""
        dialogue = self.get_dialogue(dialogue_id)
        if not dialogue:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dialogue with id {dialogue_id} not found",
            )
        return dialogue

    def list_dialogues(self, scene_id: int) -> List[ScriptDialogue]:
        """List all dialogues in a scene, ordered by order_index."""
        return (
            self.db.query(ScriptDialogue)
            .filter(ScriptDialogue.scene_id == scene_id)
            .order_by(ScriptDialogue.order_index.asc())
            .all()
        )

    def create_dialogue(
        self, scene_id: int, data: ScriptDialogueCreate
    ) -> ScriptDialogue:
        """Create a new dialogue line in a scene."""
        self.get_scene_or_404(scene_id)

        # Auto-assign order_index if not provided or zero
        order_index = data.order_index
        if order_index == 0:
            max_order = (
                self.db.query(ScriptDialogue)
                .filter(ScriptDialogue.scene_id == scene_id)
                .count()
            )
            order_index = max_order

        dialogue = ScriptDialogue(
            scene_id=scene_id,
            character_id=data.character_id,
            character_name=data.character_name,
            dialogue=data.dialogue,
            action=data.action,
            emotion=data.emotion,
            order_index=order_index,
        )
        self.db.add(dialogue)
        self.db.commit()
        self.db.refresh(dialogue)
        return dialogue

    def update_dialogue(
        self, dialogue_id: int, data: ScriptDialogueUpdate
    ) -> ScriptDialogue:
        """Update a dialogue line."""
        dialogue = self.get_dialogue_or_404(dialogue_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dialogue, field, value)
        self.db.commit()
        self.db.refresh(dialogue)
        return dialogue

    def delete_dialogue(self, dialogue_id: int) -> None:
        """Delete a dialogue line."""
        dialogue = self.get_dialogue_or_404(dialogue_id)
        self.db.delete(dialogue)
        self.db.commit()

    # ── Fountain Export ────────────────────────────────────────────────────

    def export_fountain(self, script_id: int) -> str:
        """Export a script to Fountain format.

        Fountain is a plain text markup language for screenplays.
        Reference: https://fountain.io/syntax

        Args:
            script_id: Script ID to export.

        Returns:
            Fountain format string.
        """
        script = self.get_detail(script_id)
        lines: list[str] = []

        # Title page
        lines.append(f"Title: {script.title}")
        if script.logline:
            lines.append(f"Logline: {script.logline}")
        if script.genre:
            lines.append(f"Genre: {script.genre}")
        if script.style:
            lines.append(f"Style: {script.style}")
        lines.append(f"Version: {script.version}")
        lines.append("")

        # Synopsis (optional section)
        if script.synopsis:
            lines.append("= 故事大纲")
            lines.append("")
            for para in script.synopsis.strip().split("\n"):
                para = para.strip()
                if para:
                    lines.append(para)
                    lines.append("")

        # Scenes
        for scene in script.scenes:
            # Scene heading (Fountain slugline): INT. LOCATION - DAY
            int_ext_str = scene.int_ext.value
            time_str = scene.time_of_day.value
            slug = f"{int_ext_str}. {scene.location.upper()} - {time_str}"
            lines.append(slug)
            lines.append("")

            # Scene description / action
            if scene.description:
                for para in scene.description.strip().split("\n"):
                    para = para.strip()
                    if para:
                        lines.append(para)
                        lines.append("")

            # Dialogues
            for dlg in scene.dialogues:
                # Action (parenthetical for action before line)
                if dlg.action:
                    lines.append(f"({dlg.action})")

                # Character name (all caps for Fountain)
                lines.append(dlg.character_name.upper())

                # Dialogue text
                for para in dlg.dialogue.strip().split("\n"):
                    para = para.strip()
                    if para:
                        lines.append(para)

                lines.append("")

            lines.append("")

        return "\n".join(lines)

    # ── Script Import ──────────────────────────────────────────────────────

    def import_from_text(self, script_id: int, text: str, source_type: str = "auto") -> dict:
        """Import a script from plain text.

        Supports two formats:
        - 'fountain': Standard Fountain screenplay format
        - 'novel': Novel/story text (auto-detect chapters as scenes)
        - 'auto': Auto-detect format

        Returns summary stats about what was imported.
        """
        script = self.get_by_id_or_404(script_id)
        text = text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="导入内容不能为空")

        # Detect format
        if source_type == "auto":
            source_type = self._detect_format(text)

        stats = {"format": source_type, "scenes": 0, "dialogues": 0, "characters": 0}

        if source_type == "fountain":
            stats.update(self._parse_fountain(script_id, text))
        else:
            stats.update(self._parse_novel(script_id, text))

        # Update generation stage
        script.generation_stage = ScriptGenerationStage.COMPLETED
        script.synopsis = text[:500] if not script.synopsis else script.synopsis
        self.db.commit()

        return stats

    def _detect_format(self, text: str) -> str:
        """Auto-detect if text is Fountain format or novel."""
        lines = text.strip().split("\n")
        fountain_signals = 0

        # Check for Fountain markers
        fountain_patterns = [
            r"^INT[./\s]",
            r"^EXT[./\s]",
            r"^INT/EXT",
            r"^\..+",  # Scene heading with dot prefix
            r"^[A-Z ]+$",  # All-caps character name
        ]

        for line in lines[:100]:
            line = line.strip()
            for pat in fountain_patterns:
                if re.match(pat, line):
                    fountain_signals += 1
                    break

        return "fountain" if fountain_signals >= 3 else "novel"

    def _parse_fountain(self, script_id: int, text: str) -> dict:
        """Parse Fountain format text into scenes and dialogues."""
        lines = text.split("\n")
        scenes_created = 0
        dialogues_created = 0
        characters_seen: dict[str, int] = {}
        current_scene_id: Optional[int] = None
        current_char: Optional[str] = None
        current_dialogue: list[str] = []
        current_action: list[str] = []
        scene_num = 0

        def flush_dialogue():
            nonlocal dialogues_created, current_char, current_dialogue, current_scene_id
            if current_char and current_dialogue and current_scene_id:
                char_id = characters_seen.get(current_char)
                if not char_id:
                    char = self.create_character(
                        script_id,
                        ScriptCharacterCreate(name=current_char, character_type="配角"),
                    )
                    characters_seen[current_char] = char.id
                    char_id = char.id

                self.create_dialogue(
                    current_scene_id,
                    ScriptDialogueCreate(
                        character_name=current_char,
                        character_id=char_id,
                        dialogue="\n".join(current_dialogue).strip(),
                        order_index=dialogues_created,
                    ),
                )
                dialogues_created += 1
            current_char = None
            current_dialogue = []

        def flush_action():
            nonlocal current_action
            # Action lines are stored as scene description enhancement
            current_action = []

        for line in lines:
            stripped = line.strip()

            # Scene heading (INT./EXT. or . prefix)
            if re.match(r"^(INT|EXT|INT/EXT)[\s./-]", stripped, re.IGNORECASE) or \
               (stripped.startswith(".") and len(stripped) > 1 and stripped[1].isupper()):
                flush_dialogue()
                scene_num += 1
                scenes_created += 1

                # Parse location and time
                heading = stripped.lstrip(".")
                int_ext = "INT"
                location = heading
                time_of_day = "日"

                # Extract INT/EXT prefix
                ie_match = re.match(r"^(INT/EXT|INT|EXT)[\s.\-/]+(.+)$", heading, re.IGNORECASE)
                if ie_match:
                    ie_raw = ie_match.group(1).upper().replace(".", "")
                    if ie_raw == "INT/EXT":
                        int_ext = "INT_EXT"
                    else:
                        int_ext = ie_raw
                    rest = ie_match.group(2).strip()

                    # Try to extract time from the rest (after - or :)
                    rest_match = re.match(r"(.+?)\s+[-—–]\s+(.+)$", rest)
                    if rest_match:
                        location = rest_match.group(1).strip()
                        time_str = rest_match.group(2).strip()
                    else:
                        location = rest
                        time_str = ""

                    # Determine time of day
                    time_str_lower = time_str.lower()
                    if "夜" in time_str or "night" in time_str_lower:
                        time_of_day = "夜"
                    elif "晨" in time_str or "dawn" in time_str_lower or "清晨" in time_str:
                        time_of_day = "晨"
                    elif "昏" in time_str or "dusk" in time_str_lower or "黄昏" in time_str or "傍晚" in time_str:
                        time_of_day = "昏"
                    elif time_str:
                        time_of_day = "日"

                scene = self.create_scene(
                    script_id,
                    ScriptSceneCreate(
                        scene_number=str(scene_num),
                        location=location[:200] if location else "未知场景",
                        int_ext=int_ext,
                        time_of_day=time_of_day,
                        order_index=scene_num,
                    ),
                )
                current_scene_id = scene.id
                continue

            # Character name (all caps, standalone line, followed by dialogue)
            if current_scene_id and stripped.isupper() and len(stripped) >= 2 and not stripped.startswith("@"):
                flush_dialogue()
                current_char = stripped.title()
                continue

            # Dialogue text (follows character name)
            if current_char and stripped:
                if current_scene_id:
                    current_dialogue.append(stripped)
                    continue

            # Action / description
            if current_scene_id and stripped:
                current_action.append(stripped)
            elif stripped == "":
                flush_dialogue()

        # Flush remaining
        flush_dialogue()

        return {
            "scenes": scenes_created,
            "dialogues": dialogues_created,
            "characters": len(characters_seen),
        }

    def _parse_novel(self, script_id: int, text: str) -> dict:
        """Parse novel/story text into scenes.

        Treats chapters as scenes, and dialogue in quotes as character lines.
        """
        lines = text.split("\n")
        scenes_created = 0
        dialogues_created = 0
        characters_seen: dict[str, int] = {}
        current_scene_id: Optional[int] = None
        current_action: list[str] = []
        scene_num = 0

        # Chapter patterns: 第X章 / 第X节 / Chapter X / === title ===
        chapter_pattern = re.compile(
            r"^(第[一二三四五六七八九十百千零\d]+[章回节集篇卷]|Chapter\s+\d+|\={2,}.*\={2,})",
            re.IGNORECASE,
        )

        # Dialogue patterns: "xxx" or 「xxx」 or “xxx”
        dialogue_pattern = re.compile(r'[""「『](.+?)[""」』]')

        def flush_action():
            nonlocal current_action, current_scene_id
            if current_action and current_scene_id:
                # Append to scene description
                pass
            current_action = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # New chapter = new scene
            if chapter_pattern.match(stripped):
                scene_num += 1
                scenes_created += 1
                flush_action()
                scene = self.create_scene(
                    script_id,
                    ScriptSceneCreate(
                        scene_number=str(scene_num),
                        location=stripped[:200],
                        int_ext="INT",
                        time_of_day="日",
                        description=stripped,
                        order_index=scene_num,
                    ),
                )
                current_scene_id = scene.id
                continue

            # Create a default first scene if none yet
            if not current_scene_id:
                scene_num += 1
                scenes_created += 1
                scene = self.create_scene(
                    script_id,
                    ScriptSceneCreate(
                        scene_number=str(scene_num),
                        location="开场",
                        int_ext="INT",
                        time_of_day="日",
                        description="故事开场",
                        order_index=scene_num,
                    ),
                )
                current_scene_id = scene.id

            # Extract dialogues from quoted text
            dialogues = dialogue_pattern.findall(stripped)
            if dialogues:
                for dlg_text in dialogues:
                    # Try to find speaker (text before the quote)
                    speaker = self._guess_speaker(stripped, dlg_text)
                    char_id = characters_seen.get(speaker)
                    if not char_id:
                        char = self.create_character(
                            script_id,
                            ScriptCharacterCreate(name=speaker, character_type="配角"),
                        )
                        characters_seen[speaker] = char.id
                        char_id = char.id

                    self.create_dialogue(
                        current_scene_id,
                        ScriptDialogueCreate(
                            character_name=speaker,
                            character_id=char_id,
                            dialogue=dlg_text,
                            order_index=dialogues_created,
                        ),
                    )
                    dialogues_created += 1
            else:
                # Narrative / action
                current_action.append(stripped)

        return {
            "scenes": scenes_created,
            "dialogues": dialogues_created,
            "characters": len(characters_seen),
        }

    def _guess_speaker(self, line: str, dialogue_text: str) -> str:
        """Try to guess who is speaking from the context line."""
        # Look for patterns like "张三说：..." or "他道：..."
        dlg_idx = line.find('"')
        if dlg_idx == -1:
            dlg_idx = line.find('"')
        if dlg_idx == -1:
            dlg_idx = line.find('「')
        if dlg_idx == -1:
            dlg_idx = line.find('『')

        if dlg_idx > 0:
            before = line[:dlg_idx].strip()
            # Try to find a name + speaking verb
            speak_verbs = ["说", "道", "问", "答", "喊", "叫", "低语", "轻声",
                          "叹", "笑", "冷笑", "怒道", "平静", "开口", "说道"]
            for verb in speak_verbs:
                if before.endswith(verb):
                    name = before[:-len(verb)].strip()
                    if name and len(name) <= 10:
                        return name
            # If the whole prefix is short, treat it as speaker
            if 1 <= len(before) <= 6 and before not in ("他", "她", "我", "你"):
                return before

        return "未知角色"

    # ── Episode Management ─────────────────────────────────────────────────

    def list_episodes(self, script_id: int) -> List[ScriptEpisode]:
        """List all episodes of a script."""
        return (
            self.db.query(ScriptEpisode)
            .filter(ScriptEpisode.script_id == script_id)
            .order_by(ScriptEpisode.order_index.asc())
            .all()
        )

    def get_episode(self, episode_id: int) -> Optional[ScriptEpisode]:
        return self.db.query(ScriptEpisode).filter(ScriptEpisode.id == episode_id).first()

    def get_episode_or_404(self, episode_id: int) -> ScriptEpisode:
        ep = self.get_episode(episode_id)
        if not ep:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Episode with id {episode_id} not found",
            )
        return ep

    def create_episode(self, script_id: int, data: ScriptEpisodeCreate) -> ScriptEpisode:
        """Create a new episode."""
        ep = ScriptEpisode(script_id=script_id, **data.model_dump())
        self.db.add(ep)
        self.db.commit()
        self.db.refresh(ep)
        return ep

    def update_episode(self, episode_id: int, data: ScriptEpisodeUpdate) -> ScriptEpisode:
        """Update an episode."""
        ep = self.get_episode_or_404(episode_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(ep, field, value)
        self.db.commit()
        self.db.refresh(ep)
        return ep

    def delete_episode(self, episode_id: int) -> None:
        ep = self.get_episode_or_404(episode_id)
        self.db.delete(ep)
        self.db.commit()

    # ── Generation Stage Management ────────────────────────────────────────

    def set_generation_stage(self, script_id: int, stage: ScriptGenerationStage) -> Script:
        """Update the generation stage of a script."""
        script = self.get_by_id_or_404(script_id)
        script.generation_stage = stage
        self.db.commit()
        self.db.refresh(script)
        return script

    def advance_generation_stage(self, script_id: int, target: ScriptGenerationStage) -> Script:
        """Advance script generation to target stage (can't go backward)."""
        script = self.get_by_id_or_404(script_id)
        stages = list(ScriptGenerationStage)
        current_idx = stages.index(script.generation_stage)
        target_idx = stages.index(target)
        if target_idx > current_idx:
            script.generation_stage = target
            self.db.commit()
            self.db.refresh(script)
        return script

    def generate_outline(
        self,
        script_id: int,
        idea: str,
        genre: str,
        style: Optional[str],
        total_episodes: int,
    ) -> Tuple[Script, List[dict]]:
        """Generate story outline and episode outlines.

        Uses the screenwriter agent if available, otherwise creates placeholder structure.
        """
        script = self.get_by_id_or_404(script_id)
        script.core_idea = idea
        script.genre = genre
        script.style = style
        script.total_episodes = total_episodes

        # Try using screenwriter agent
        from app.agents.manager import AgentManager

        agent_result = None
        try:
            mgr = AgentManager(self.db)
            agent_result = mgr.invoke(
                "screenwriter",
                "generate_script",
                project_id=script.project_id,
                idea=idea,
                genre=genre,
                style=style or "",
                num_scenes=max(total_episodes, 5),
            )
        except Exception as e:
            logger.warning(f"[ScriptService] Screenwriter agent unavailable: {e}")

        if agent_result and agent_result.get("synopsis"):
            # Use AI-generated content
            script.synopsis = agent_result.get("synopsis", "")
            script.logline = agent_result.get("logline", "")

            ai_characters = agent_result.get("characters", [])
            ai_scenes = agent_result.get("scene_outlines", [])

            # Build episode outlines from AI scenes (group scenes into episodes)
            outlines = []
            scenes_per_ep = max(1, len(ai_scenes) // max(total_episodes, 1))

            for i in range(total_episodes):
                start = i * scenes_per_ep
                end = start + scenes_per_ep if i < total_episodes - 1 else len(ai_scenes)
                ep_scenes = ai_scenes[start:end] if ai_scenes else []
                synopsis = " ".join(
                    [s.get("description", "") for s in ep_scenes if isinstance(s, dict)]
                )
                outlines.append({
                    "episode_number": i + 1,
                    "title": f"第{i + 1}集",
                    "synopsis": synopsis[:300] or f"第{i + 1}集剧情",
                    "hook": ep_scenes[0].get("description", "")[:100] if ep_scenes and isinstance(ep_scenes[0], dict) else "",
                    "cliffhanger": ep_scenes[-1].get("description", "")[:100] if ep_scenes and isinstance(ep_scenes[-1], dict) else "",
                })

            script.episode_outlines = outlines
            script.generation_stage = ScriptGenerationStage.OUTLINE

            # Store AI characters for later use (in generate_characters)
            self.db.info["ai_characters"] = ai_characters

            # Create episode records
            for i in range(total_episodes):
                ep = ScriptEpisode(
                    script_id=script.id,
                    episode_number=i + 1,
                    title=f"第{i + 1}集",
                    order_index=i,
                    is_generated=False,
                )
                self.db.add(ep)
        else:
            # Fallback: create placeholder structure
            outlines = []
            for i in range(total_episodes):
                outlines.append({
                    "episode_number": i + 1,
                    "title": f"第{i + 1}集",
                    "synopsis": "",
                    "hook": "",
                    "cliffhanger": "",
                })

            script.episode_outlines = outlines
            script.generation_stage = ScriptGenerationStage.OUTLINE

            # Create episode records
            for i in range(total_episodes):
                ep = ScriptEpisode(
                    script_id=script.id,
                    episode_number=i + 1,
                    title=f"第{i + 1}集",
                    order_index=i,
                    is_generated=False,
                )
                self.db.add(ep)

        self.db.commit()
        self.db.refresh(script)
        return script, outlines

    def generate_characters(
        self,
        script_id: int,
        num_characters: int = 5,
    ) -> List[ScriptCharacter]:
        """Generate characters for the script.

        Uses the screenwriter agent if available. Falls back to placeholders.
        """
        script = self.get_by_id_or_404(script_id)

        existing = self.list_characters(script_id)
        if existing:
            script.generation_stage = ScriptGenerationStage.CHARACTERS
            self.db.commit()
            return existing

        # Try to get AI-generated characters from the outline step
        from app.agents.manager import AgentManager

        ai_characters = None
        try:
            mgr = AgentManager(self.db)
            # Re-run outline generation if we need characters from agent
            # Or use a lightweight character generation
            result = mgr.invoke(
                "screenwriter",
                "generate_script",
                project_id=script.project_id,
                idea=script.core_idea or script.title or "短剧故事",
                genre=script.genre or "都市",
                style=script.style or "",
                num_scenes=5,
            )
            if result:
                ai_characters = result.get("characters", [])
        except Exception as e:
            logger.warning(f"[ScriptService] Character generation via agent failed: {e}")

        if ai_characters:
            for idx, char in enumerate(ai_characters):
                if isinstance(char, dict):
                    name = char.get("name", f"角色{idx + 1}")
                    desc = char.get("description", char.get("backstory", ""))
                    role_type = char.get("role", "主角" if idx == 0 else "配角")
                    if isinstance(role_type, str) and role_type not in ("主角", "配角", "客串"):
                        role_type = "主角" if idx == 0 else "配角"
                    self.create_character(script_id, ScriptCharacterCreate(
                        name=name[:50],
                        character_type=role_type,
                        description=desc[:500] if desc else "",
                    ))
        else:
            # Fallback: placeholders
            for i in range(num_characters):
                self.create_character(script_id, ScriptCharacterCreate(
                    name=f"角色{i + 1}",
                    character_type="主角" if i == 0 else "配角",
                ))

        script.generation_stage = ScriptGenerationStage.CHARACTERS
        self.db.commit()
        return self.list_characters(script_id)

    def mark_episode_generated(self, episode_id: int) -> ScriptEpisode:
        """Mark an episode as fully generated."""
        ep = self.get_episode_or_404(episode_id)
        ep.is_generated = True
        self.db.commit()
        self.db.refresh(ep)

        # Check if all episodes are generated → advance stage
        all_generated = all(
            e.is_generated for e in self.list_episodes(ep.script_id)
        )
        if all_generated:
            script = self.get_by_id(ep.script_id)
            if script:
                script.generation_stage = ScriptGenerationStage.COMPLETED
                self.db.commit()

        return ep

    def generate_episode_script(self, episode_id: int) -> ScriptEpisode:
        """Generate full script (scenes + dialogues) for an episode.

        Note: This creates demo/seed content based on episode info.
        Real AI generation is handled by the agent layer.
        """
        ep = self.get_episode_or_404(episode_id)
        script = self.get_by_id(ep.script_id)
        if not script:
            raise HTTPException(status_code=404, detail="Script not found")

        # Get characters for the script
        chars = self.list_characters(ep.script_id)
        if not chars:
            # Create default characters if none exist
            self.create_character(
                ep.script_id,
                ScriptCharacterCreate(name="主角", character_type="主角", description="故事的主要角色"),
            )
            self.create_character(
                ep.script_id,
                ScriptCharacterCreate(name="配角", character_type="配角", description="辅助推动剧情的角色"),
            )
            chars = self.list_characters(ep.script_id)

        # Generate 3-5 demo scenes for the episode
        num_scenes = 4
        locations = ["客厅", "办公室", "街道", "咖啡馆", "公园", "家中", "餐厅"]
        int_ext_values = ["INT", "EXT", "INT/EXT"]
        times = ["日", "夜", "晨", "昏"]

        scene_templates = [
            f"第{ep.episode_number}集开场 - {ep.title or '故事展开'}",
            "冲突升级",
            "关键转折",
            "悬念收尾",
        ]

        dialogue_templates = [
            ("你来了。", "我以为你不会来。"),
            ("这件事，你怎么看？", "我觉得没那么简单。"),
            ("真相到底是什么？", "也许我们永远不会知道。"),
            ("别走。", "对不起，我必须走。"),
        ]

        for i in range(num_scenes):
            scene = self.create_scene(
                ep.script_id,
                ScriptSceneCreate(
                    scene_number=f"{ep.episode_number}.{i + 1}",
                    location=locations[i % len(locations)],
                    int_ext=int_ext_values[i % len(int_ext_values)],
                    time_of_day=times[i % len(times)],
                    description=f"第{ep.episode_number}集 第{i + 1}场 - {scene_templates[i % len(scene_templates)]}\n" +
                                (ep.synopsis or "剧情发展中...")[:100],
                    order_index=ep.episode_number * 1000 + i,
                ),
            )

            # Add 2-3 dialogues per scene
            for j in range(3):
                char = chars[j % len(chars)]
                dlg_template = dialogue_templates[(i + j) % len(dialogue_templates)]
                text = dlg_template[0] if j % 2 == 0 else dlg_template[1]
                self.create_dialogue(
                    scene.id,
                    ScriptDialogueCreate(
                        character_name=char.name,
                        character_id=char.id,
                        dialogue=text + f"（第{i + 1}场第{j + 1}句）",
                        action="走进来" if j == 0 else None,
                        order_index=j,
                    ),
                )

        ep.is_generated = True
        # Update synopsis if empty
        if not ep.synopsis:
            ep.synopsis = f"第{ep.episode_number}集内容：故事继续发展，主角面临新的挑战。"

        self.db.commit()
        self.db.refresh(ep)

        # Check if all episodes are generated
        all_generated = all(
            e.is_generated for e in self.list_episodes(ep.script_id)
        )
        if all_generated:
            script.generation_stage = ScriptGenerationStage.COMPLETED
            self.db.commit()
        else:
            script.generation_stage = ScriptGenerationStage.EPISODES
            self.db.commit()

        return ep
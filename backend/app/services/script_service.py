"""Script service - business logic for script management.

Handles CRUD for scripts, scenes, characters, dialogues,
and provides Fountain format export.
"""
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.script import (
    Script,
    ScriptCharacter,
    ScriptDialogue,
    ScriptScene,
)
from app.schemas.script import (
    ScriptCharacterCreate,
    ScriptCharacterUpdate,
    ScriptCreate,
    ScriptDialogueCreate,
    ScriptDialogueUpdate,
    ScriptSceneCreate,
    ScriptSceneUpdate,
    ScriptUpdate,
)


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
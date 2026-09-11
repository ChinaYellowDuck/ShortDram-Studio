"""Tests for skill import functionality."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.skill_service import SkillService
from app.schemas.skill import SkillImportItem


def test_parse_skill_markdown(db_session: Session):
    """Test parsing skill from markdown format."""
    service = SkillService(db_session)

    text = "# 创意写作助手\n\n帮助用户生成创意写作内容。\n\n## 使用方法\n\n请输入你想要写的主题..."
    name, desc, content = service.parse_skill_from_text(text)

    assert name == "创意写作助手"
    assert desc is not None
    assert "帮助用户" in desc
    assert "使用方法" in content
    assert "主题" in content


def test_parse_skill_yaml_front_matter(db_session: Session):
    """Test parsing skill from YAML front matter format."""
    service = SkillService(db_session)

    text = """---
name: 代码审查助手
description: 审查代码质量和风格
---
你是一个资深代码审查专家..."""

    name, desc, content = service.parse_skill_from_text(text)

    assert name == "代码审查助手"
    assert desc == "审查代码质量和风格"
    assert "代码审查专家" in content


def test_parse_skill_plain_text(db_session: Session):
    """Test parsing skill from plain text."""
    service = SkillService(db_session)

    text = "翻译助手\n\n你是一个专业的翻译..."
    name, desc, content = service.parse_skill_from_text(text)

    assert name == "翻译助手"
    assert "专业的翻译" in content


def test_import_from_text_creates_skill(db_session: Session):
    """Test importing a skill from text."""
    service = SkillService(db_session)

    text = "# 测试导入 Skill\n\n这是一个测试描述。\n\n实际内容行。"
    result = service.import_from_text(text)

    assert result.total == 1
    assert result.created == 1
    assert result.updated == 0
    assert result.skipped == 0
    assert len(result.imported_ids) == 1
    assert len(result.errors) == 0

    # Verify the skill was created
    skill = service.get_by_id(result.imported_ids[0])
    assert skill is not None
    assert skill.name == "测试导入 Skill"


def test_import_duplicate_skipped(db_session: Session):
    """Test that duplicate skill names are skipped without overwrite."""
    service = SkillService(db_session)

    text = "# 重复导入测试\n内容"
    service.import_from_text(text)

    result = service.import_from_text(text)
    assert result.total == 1
    assert result.created == 0
    assert result.skipped == 1
    assert len(result.errors) == 1
    assert "已存在" in result.errors[0]


def test_import_duplicate_overwritten(db_session: Session):
    """Test that duplicate skill names are overwritten when enabled."""
    service = SkillService(db_session)

    text1 = "# 覆盖测试\n旧内容"
    r1 = service.import_from_text(text1)
    assert r1.created == 1

    text2 = "# 覆盖测试\n新内容"
    r2 = service.import_from_text(text2, overwrite=True)
    assert r2.updated == 1
    assert r2.skipped == 0

    skill = service.get_by_id(r1.imported_ids[0])
    assert skill is not None
    assert "新内容" in skill.content


def test_batch_import(db_session: Session):
    """Test batch importing multiple skills."""
    service = SkillService(db_session)

    items = [
        SkillImportItem(name="批量测试1", content="内容1"),
        SkillImportItem(name="批量测试2", content="内容2", description="描述2"),
        SkillImportItem(name="批量测试1", content="重复"),  # duplicate
    ]
    result = service.import_batch(items)

    assert result.total == 3
    assert result.created == 2
    assert result.skipped == 1
    assert len(result.imported_ids) == 2


def test_import_api_text_endpoint(client: TestClient):
    """Test the /skills/import/text API endpoint."""
    resp = client.post(
        "/api/v1/skills/import/text",
        json={
            "text": "# API 导入测试\nAPI 测试内容",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["created"] == 1


def test_import_api_batch_endpoint(client: TestClient):
    """Test the /skills/import/batch API endpoint."""
    resp = client.post(
        "/api/v1/skills/import/batch",
        json={
            "skills": [
                {"name": "API批量1", "content": "内容1"},
                {"name": "API批量2", "content": "内容2"},
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["created"] == 2

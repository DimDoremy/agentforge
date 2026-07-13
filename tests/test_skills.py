"""Meta-tests for the agentforge skill pack itself.

These verify the pack's structural integrity — they don't import the template
package (which has its own tests under template/). Run from the repo root:
``uv run pytest`` (or ``python -m pytest``).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"

# The five skills the pack is supposed to ship.
EXPECTED_SKILLS = {
    "harness-core",
    "postgres-as-platform",
    "fastapi-serving",
    "deepagent-authoring",
    "dev-workflow",
}

_FRONTMATTER = re.compile(r"^---\n(?P<body>.*?)\n---\n", re.DOTALL)


def _skill_dirs() -> list[Path]:
    return [p for p in SKILLS_DIR.iterdir() if (p / "SKILL.md").is_file()]


def test_all_expected_skills_present():
    actual = {p.name for p in _skill_dirs()}
    assert actual == EXPECTED_SKILLS, (
        f"skill set mismatch. expected {EXPECTED_SKILLS}, got {actual}"
    )


@pytest.mark.parametrize("skill_dir", _skill_dirs(), ids=lambda p: p.name)
def test_skill_md_has_valid_frontmatter(skill_dir: Path):
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    m = _FRONTMATTER.match(text)
    assert m, f"{skill_dir}/SKILL.md missing YAML front-matter"
    body = m.group("body")
    assert re.search(r"^name:\s*\S+", body, re.MULTILINE), "front-matter needs `name`"
    desc = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
    assert desc, "front-matter needs `description`"
    assert "Use when" in desc.group(1) or "Use at the START" in desc.group(
        1
    ), "description must start with a 'Use when…' trigger"


@pytest.mark.parametrize("skill_dir", _skill_dirs(), ids=lambda p: p.name)
def test_skill_has_references_dir(skill_dir: Path):
    refs = skill_dir / "references"
    assert refs.is_dir() and any(refs.glob("*.md")), (
        f"{skill_dir.name}/references/ missing or empty"
    )


@pytest.mark.parametrize("ref", list(SKILLS_DIR.rglob("references/*.md")))
def test_reference_has_toc(ref: Path):
    text = ref.read_text(encoding="utf-8")
    assert "## Table of Contents" in text, f"{ref} missing a Table of Contents"

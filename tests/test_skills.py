"""Unit tests for the skill registry + token-fill."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import skills  # noqa: E402


@pytest.fixture(scope="module")
def registry():
    return skills.load_skills()


def test_loads_known_skills(registry):
    assert "line-column-combo-chart" in registry
    assert "time-window-highlight" in registry


def test_resolve_explicit_skill(registry):
    sk = skills.resolve_skill({"skill": "line-column-combo-chart"}, registry)
    assert sk is not None and sk.name == "line-column-combo-chart"


def test_resolve_unknown_returns_none(registry):
    assert skills.resolve_skill({"skill": "does-not-exist"}, registry) is None
    assert skills.resolve_skill({}, registry) is None


def test_example_tokens_cover_all_referenced_tokens(registry):
    # Every <TOKEN> used in template files should have an example in the token table.
    for sk in registry.values():
        missing = sk.tokens - set(sk.example_tokens())
        assert not missing, f"{sk.name} missing example tokens: {missing}"


def test_fill_produces_valid_json(registry):
    for sk in registry.values():
        filled = skills.fill(sk, sk.example_tokens())
        for rel, text in filled.items():
            assert "<" not in text or ">" not in text or not skills.TOKEN_RE.search(text)
            if rel.endswith(".json"):
                json.loads(text)  # raises on invalid


def test_fill_raises_on_missing_token(registry):
    sk = registry["line-column-combo-chart"]
    with pytest.raises(ValueError):
        skills.fill(sk, {})  # no tokens supplied


def test_id_helpers_format():
    assert len(skills.new_lineage_tag()) == 36 and skills.new_lineage_tag().count("-") == 4
    assert len(skills.new_pbi_id()) == 32
    assert len(skills.new_visual_name()) == 20

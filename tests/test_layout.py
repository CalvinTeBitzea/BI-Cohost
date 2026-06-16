"""Unit tests for the deterministic snap engine."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib import layout  # noqa: E402


def _exec_overview_page() -> dict:
    return {
        "page_id": "p1", "name": "Overview", "type": "overview",
        "visuals": [
            {"visual_id": "f1", "type": "slicer", "grid": {"col": 0, "row": 0, "colSpan": 4, "rowSpan": 1}},
            {"visual_id": "f2", "type": "slicer", "grid": {"col": 4, "row": 0, "colSpan": 4, "rowSpan": 1}},
            {"visual_id": "s1", "type": "card", "grid": {"col": 0, "row": 1, "colSpan": 3, "rowSpan": 1}},
            {"visual_id": "s2", "type": "card", "grid": {"col": 3, "row": 1, "colSpan": 3, "rowSpan": 1}},
            {"visual_id": "s3", "type": "card", "grid": {"col": 6, "row": 1, "colSpan": 3, "rowSpan": 1}},
            {"visual_id": "s5", "type": "line", "grid": {"col": 0, "row": 2, "colSpan": 8, "rowSpan": 2}},
            {"visual_id": "s6", "type": "bar", "grid": {"col": 8, "row": 2, "colSpan": 4, "rowSpan": 1}},
            {"visual_id": "s7", "type": "table", "grid": {"col": 8, "row": 3, "colSpan": 4, "rowSpan": 1}},
        ],
    }


def _by_id(page: dict) -> dict:
    return {v["visual_id"]: v for v in page["visuals"]}


def test_every_visual_gets_layout_and_no_issues():
    page, issues = layout.snap_page(_exec_overview_page())
    assert issues == []
    for v in page["visuals"]:
        assert set(v["layout"]) == {"x", "y", "w", "h", "z", "tabOrder"}


def test_bands_stack_top_to_bottom():
    page, _ = layout.snap_page(_exec_overview_page())
    v = _by_id(page)
    assert v["f1"]["layout"]["y"] < v["s1"]["layout"]["y"] < v["s5"]["layout"]["y"]


def test_trend_rowspan_is_taller_than_single_row_chart():
    page, _ = layout.snap_page(_exec_overview_page())
    v = _by_id(page)
    assert v["s5"]["layout"]["h"] > v["s6"]["layout"]["h"]


def test_z_order_banded_by_type():
    page, _ = layout.snap_page(_exec_overview_page())
    v = _by_id(page)
    assert v["f1"]["layout"]["z"] < 1000          # slicer band
    assert 1000 <= v["s1"]["layout"]["z"] < 2000   # card band
    assert v["s5"]["layout"]["z"] >= 2000          # chart band


def test_all_within_canvas_bounds():
    page, _ = layout.snap_page(_exec_overview_page())
    for v in page["visuals"]:
        L = v["layout"]
        assert L["x"] >= -1 and L["y"] >= -1
        assert L["x"] + L["w"] <= layout.CANVAS_W + 1
        assert L["y"] + L["h"] <= layout.CANVAS_H + 1


def test_deterministic():
    a, _ = layout.snap_page(_exec_overview_page())
    b, _ = layout.snap_page(_exec_overview_page())
    assert [v["layout"] for v in a["visuals"]] == [v["layout"] for v in b["visuals"]]


def test_overlap_detected():
    page = {"visuals": [
        {"visual_id": "a", "type": "card", "grid": {"col": 0, "row": 1, "colSpan": 4, "rowSpan": 1}},
        {"visual_id": "b", "type": "card", "grid": {"col": 0, "row": 1, "colSpan": 4, "rowSpan": 1}},
    ]}
    _, issues = layout.snap_page(page)
    assert any("overlap" in i for i in issues)


def test_over_cap_flagged():
    n = layout.MAX_VISUALS + 1
    page = {"visuals": [
        {"visual_id": f"c{i}", "type": "card",
         "grid": {"col": (i % 4) * 3, "row": 1 + i // 4, "colSpan": 3, "rowSpan": 1}}
        for i in range(n)
    ]}
    _, issues = layout.snap_page(page)
    assert any(f"max {layout.MAX_VISUALS}" in i for i in issues)


def test_grid_synthesis_fallback_no_overlap():
    page = {"visuals": [
        {"visual_id": "sl", "type": "slicer"},
        {"visual_id": "k1", "type": "card"},
        {"visual_id": "k2", "type": "card"},
        {"visual_id": "ch1", "type": "bar"},
        {"visual_id": "ch2", "type": "line"},
    ]}
    _, issues = layout.snap_page(page)
    assert not any("overlap" in i for i in issues)
    for v in page["visuals"]:
        assert "layout" in v and "grid" in v

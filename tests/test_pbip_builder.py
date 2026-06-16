"""End-to-end: retail golden example → ingest → PBIR builder.

Drives the real retail wireframe spec + semantic model (hand-encoded from the
BI-Workflow agent's wireframe.html + requirements.md) through ingest and the builder,
with no Power BI Desktop and no API key. Proves the realigned bridge:
agent artifacts → IR (snapped) → PBIR, gates passing, skill visual emitted.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest  # noqa: E402
import lib.artifact_store as store  # noqa: E402
import agents.ingest as ingest  # noqa: E402
import agents.pbip_builder as pbip  # noqa: E402

EXAMPLE = Path(__file__).parent.parent / "examples" / "retail"


@pytest.fixture()
def build(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "_BASE", tmp_path)
    monkeypatch.setattr(pbip, "artifact_path", lambda bid, fn: tmp_path / bid / fn)
    ingest.run("r1", str(EXAMPLE / "dashboard_spec.json"),
               str(EXAMPLE / "semantic_model.json"))
    return tmp_path


def test_ingest_snaps_layout_and_validates(build):
    spec = store.read_artifact("r1", "dashboard_spec.json")
    for page in spec["pages"]:
        for v in page["visuals"]:
            assert set(v["layout"]) == {"x", "y", "w", "h", "z", "tabOrder"}


def test_build_gates_pass(build):
    result = pbip.run("r1", pbip_report_path=None)
    assert result["gate1"]["passed"], result["gate1"]["errors"]
    assert result["gate3"]["passed"], result["gate3"]["issues"]


def test_two_pages_and_all_visuals_written(build):
    result = pbip.run("r1", pbip_report_path=None)
    pages_dir = Path(result["output_dir"])
    page_dirs = [d for d in pages_dir.iterdir() if d.is_dir()]
    assert len(page_dirs) == 2
    visual_files = list(pages_dir.rglob("visual.json"))
    assert len(visual_files) == 21  # 13 on p1 + 8 on p2


def test_pareto_uses_combo_skill(build):
    result = pbip.run("r1", pbip_report_path=None)
    types = {json.loads(f.read_text())["visual"]["visualType"]
             for f in Path(result["output_dir"]).rglob("visual.json")}
    assert "lineStackedColumnComboChart" in types   # Pareto via the skill
    assert "scatterChart" in types                   # scatter fallback
    assert "donutChart" in types                     # donut fallback
    assert "tableEx" in types                         # ranked table fallback


def test_combo_bound_to_pareto_fields(build):
    result = pbip.run("r1", pbip_report_path=None)
    combo = next(json.loads(f.read_text()) for f in Path(result["output_dir"]).rglob("visual.json")
                 if json.loads(f.read_text())["visual"]["visualType"] == "lineStackedColumnComboChart")
    qs = combo["visual"]["query"]["queryState"]
    # bars = Net Revenue, line = cumulative %, category = ProductName
    assert qs["Y"]["projections"][0]["nativeQueryRef"] == "Net Revenue"
    assert qs["Y2"]["projections"][0]["nativeQueryRef"] == "Cumulative Net Revenue %"
    assert qs["Category"]["projections"][0]["queryRef"] == "Dim_Product.ProductName"

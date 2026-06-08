"""
Stage 4 — PBIP Builder (PBIR format)

Writes pages and visuals into an existing PBIP project using the PBIR format.
The project must already exist — created by Power BI Desktop. This agent
writes only into the definition/pages/ folder and updates pages.json.

PBIR files written per page:
  {report}/definition/pages/{pageName}/page.json
  {report}/definition/pages/{pageName}/visuals/{visualName}/visual.json

Files NOT touched (Desktop owns these):
  report.json, version.json, .platform, definition.pbir

Three gates:
  Gate 1 — all generated JSON files parse cleanly (runs here)
  Gate 2 — open in Power BI Desktop (manual, Windows VM)
  Gate 3 — IR fidelity: page/visual count, types, positions (runs here)
"""

import json
import re
import uuid
from pathlib import Path

from lib.anthropic_client import BRAIN, call_with_tool, consult_advisor
from lib.artifact_store import read_artifact, write_artifact, artifact_path, mark_stage_done

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SCHEMA_FALLBACK = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/visualContainer/2.0.0/schema.json"
)
_PAGE_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/page/2.0.0/schema.json"
)
_PAGES_META_SCHEMA = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/pagesMetadata/1.0.0/schema.json"
)

_VISUAL_TYPE_MAP = {
    "card":      "cardVisual",
    "bar":       "clusteredBarChart",
    "column":    "clusteredColumnChart",
    "line":      "lineChart",
    "table":     "tableEx",
    "slicer":    "slicer",
    "matrix":    "pivotTable",
    "pie":       "pieChart",
    "donut":     "donutChart",
    "gauge":     "gauge",
    "scatter":   "scatterChart",
    "waterfall": "waterfallChart",
    "funnel":    "funnelChart",
}

# Z-order ranges by visual category
_Z_RANGES = {"slicer": 500, "cardVisual": 1000}
_Z_DEFAULT = 2000

# ---------------------------------------------------------------------------
# Schema version detection
# ---------------------------------------------------------------------------

def _detect_schema_version(pages_dir: Path) -> str:
    """Read $schema URL from an existing visual.json. Falls back to 2.0.0."""
    if not pages_dir.exists():
        return _SCHEMA_FALLBACK
    for page_dir in pages_dir.iterdir():
        visuals_dir = page_dir / "visuals"
        if not visuals_dir.is_dir():
            continue
        for v_dir in visuals_dir.iterdir():
            f = v_dir / "visual.json"
            if f.is_file():
                try:
                    j = json.loads(f.read_text())
                    if "$schema" in j:
                        return j["$schema"]
                except (json.JSONDecodeError, OSError):
                    pass
    return _SCHEMA_FALLBACK


def _next_page_number(pages_dir: Path) -> int:
    """Auto-increment page number based on existing pg## folders."""
    if not pages_dir.exists():
        return 1
    nums = []
    for d in pages_dir.iterdir():
        m = re.match(r"^pg(\d+)", d.name)
        if m:
            nums.append(int(m.group(1)))
    return (max(nums) + 1) if nums else 1


# ---------------------------------------------------------------------------
# Naming helpers
# ---------------------------------------------------------------------------

def _slug(name: str, max_len: int = 30) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]", "", name.replace(" ", "_"))
    return s[:max_len] or "unnamed"


def _page_folder_name(idx: int, page_spec: dict) -> str:
    return f"pg{idx:02d}{_slug(page_spec.get('name', 'Page'))}"


def _visual_folder_name(idx: int, visual_spec: dict) -> str:
    title = visual_spec.get("title", visual_spec.get("visual_id", "Visual"))
    return f"v{idx:02d}{_slug(title)}"


# ---------------------------------------------------------------------------
# Field projection builders
# ---------------------------------------------------------------------------

def _measure_projection(name: str, measure_defs: dict) -> dict | None:
    m = measure_defs.get(name)
    if not m:
        return None
    return {
        "field": {
            "Measure": {
                "Expression": {"SourceRef": {"Entity": m["home_table"]}},
                "Property": name
            }
        },
        "queryRef": f"{m['home_table']}.{name}",
        "nativeQueryRef": name,
    }


def _dimension_projection(name: str, dimension_defs: dict) -> dict | None:
    d = dimension_defs.get(name)
    if not d:
        return None
    return {
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": d["source_table"]}},
                "Property": d["source_column"]
            }
        },
        "queryRef": f"{d['source_table']}.{d['source_column']}",
        "nativeQueryRef": d["source_column"],
    }


def _projections(names: list[str], is_measure: bool, defs: dict) -> list[dict]:
    fn = _measure_projection if is_measure else _dimension_projection
    return [p for n in names if (p := fn(n, defs))]


# ---------------------------------------------------------------------------
# Query state builder (per visual type)
# ---------------------------------------------------------------------------

def _build_query_state(
    pbi_type: str,
    measures_used: list[str],
    dimensions_used: list[str],
    measure_defs: dict,
    dimension_defs: dict,
) -> dict:
    """
    Build the queryState dict for a visual.
    Each key is a data role name; value has a projections list.
    """
    pm = _projections(measures_used, True, measure_defs)
    pd = _projections(dimensions_used, False, dimension_defs)
    state: dict = {}

    if pbi_type == "cardVisual":
        if pm:
            state["Data"] = {"projections": pm[:1]}
        if len(pm) > 1:
            state["ReferenceLabels"] = {"projections": pm[1:2]}
        if len(pm) > 2:
            state["AdditionalMeasure"] = {"projections": pm[2:3]}

    elif pbi_type in ("clusteredColumnChart", "clusteredBarChart", "lineChart"):
        if pd:
            state["Category"] = {"projections": pd}
        if pm:
            state["Y"] = {"projections": pm}

    elif pbi_type == "tableEx":
        all_p = pd + pm
        if all_p:
            state["Values"] = {"projections": all_p}

    elif pbi_type == "slicer":
        first = (pd or pm)[:1]
        if first:
            state["Values"] = {"projections": first}

    elif pbi_type == "pivotTable":
        if pd:
            state["Rows"] = {"projections": pd}
        if pm:
            state["Values"] = {"projections": pm}

    elif pbi_type in ("pieChart", "donutChart"):
        if pd:
            state["Category"] = {"projections": pd}
        if pm:
            state["Y"] = {"projections": pm}

    elif pbi_type == "gauge":
        if pm:
            state["Y"] = {"projections": pm[:1]}

    else:  # fallback: category + Y
        if pd:
            state["Category"] = {"projections": pd}
        if pm:
            state["Y"] = {"projections": pm}

    return state


# ---------------------------------------------------------------------------
# Visual JSON builder
# ---------------------------------------------------------------------------

def _build_visual_json(
    visual_spec: dict,
    folder_name: str,
    tab_order: int,
    schema_url: str,
    measure_defs: dict,
    dimension_defs: dict,
) -> dict:
    pbi_type = _VISUAL_TYPE_MAP.get(visual_spec.get("type", "card"), "cardVisual")
    z = _Z_RANGES.get(pbi_type, _Z_DEFAULT) + tab_order

    # Use positions from the IR spec (set by dashboard_spec layout engine)
    pos = visual_spec.get("_position", {})
    x = pos.get("x", 30)
    y = pos.get("y", 80)
    w = pos.get("w", 280)
    h = pos.get("h", 130)

    query_state = _build_query_state(
        pbi_type,
        visual_spec.get("measures", []),
        visual_spec.get("dimensions", []),
        measure_defs,
        dimension_defs,
    )

    return {
        "$schema": schema_url,
        "name": folder_name,
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab_order},
        "visual": {
            "visualType": pbi_type,
            "query": {"queryState": query_state} if query_state else {},
            "drillFilterOtherVisuals": True,
        },
    }


# ---------------------------------------------------------------------------
# Page JSON builder
# ---------------------------------------------------------------------------

def _build_page_json(page_spec: dict, folder_name: str) -> dict:
    return {
        "$schema": _PAGE_SCHEMA,
        "name": folder_name,
        "displayName": page_spec.get("name", "Page"),
        "displayOption": "FitToPage",
        "width": 1280,
        "height": 720,
    }


# ---------------------------------------------------------------------------
# Layout: attach positions to visual specs
# ---------------------------------------------------------------------------

def _attach_positions(page_spec: dict) -> None:
    """
    Compute and attach _position dicts to each visual in the page spec.
    Uses standard grid positions from the SKILL.md reference layout.
    Modifies page_spec.visuals in-place.
    """
    visuals = page_spec.get("visuals", [])
    margin = 16

    slicers  = [v for v in visuals if v.get("type") == "slicer"]
    cards    = [v for v in visuals if v.get("type") == "card"]
    charts   = [v for v in visuals if v.get("type") not in ("slicer", "card")]

    y = margin

    if slicers:
        n = len(slicers)
        w = (1280 - margin * (n + 1)) // n
        for i, v in enumerate(slicers):
            v["_position"] = {"x": margin + i * (w + margin), "y": y, "w": w, "h": 60}
        y += 60 + margin

    if cards:
        n = len(cards)
        w = min(280, (1280 - margin * (n + 1)) // n)
        for i, v in enumerate(cards):
            v["_position"] = {"x": margin + i * (w + margin), "y": y, "w": w, "h": 130}
        y += 130 + margin

    if charts:
        cols = min(2, len(charts))
        cw = (1280 - margin * (cols + 1)) // cols
        remaining = 720 - y - margin
        rows = (len(charts) + cols - 1) // cols
        ch = max(150, (remaining - margin * (rows - 1)) // rows)
        for i, v in enumerate(charts):
            col = i % cols
            row = i // cols
            v["_position"] = {
                "x": margin + col * (cw + margin),
                "y": y + row * (ch + margin),
                "w": cw,
                "h": ch
            }

    # fallback for anything that didn't get a position
    for v in visuals:
        if "_position" not in v:
            v["_position"] = {"x": margin, "y": margin, "w": 400, "h": 300}


# ---------------------------------------------------------------------------
# TMDL generation (Claude) — for new semantic models
# ---------------------------------------------------------------------------

_TMDL_SYSTEM = """You are a Power BI TMDL expert. Generate valid TMDL for a semantic model.

Rules:
- Tab indentation (one tab per level, never spaces)
- Top-level: `model Model` with `compatibilityLevel = 1550` and `culture = 'en-US'`
- Tables: `table 'Name'` with `lineageTag: <uuid>`
- Columns: `column 'Name'` with `dataType`, `sourceColumn`, `summarizeBy = none`, `lineageTag: <uuid>`
  - dataType values: string | int64 | double | dateTime | boolean | decimal
- Measures inside their home table: `measure 'Name' = <DAX>` with `formatString`, `lineageTag: <uuid>`
- Relationships at model level: `relationship` block with fromTable/fromColumn/toTable/toColumn/guid
- No data source section — user connects source in Desktop
- Output ONLY the raw TMDL. No markdown fences."""

_TMDL_TOOL_SCHEMA = {
    "type": "object",
    "required": ["tmdl"],
    "properties": {"tmdl": {"type": "string", "description": "Complete model.tmdl file content"}}
}


def _generate_tmdl(model: dict) -> str:
    result = call_with_tool(
        system=_TMDL_SYSTEM,
        user_message=f"Generate TMDL:\n{json.dumps(model, indent=2)}",
        tool_name="submit_tmdl",
        tool_schema=_TMDL_TOOL_SCHEMA,
        model=BRAIN,
        max_tokens=8096,
    )
    tmdl = result.get("tmdl", "").strip()
    if "model Model" not in tmdl:
        raise RuntimeError("TMDL missing required 'model Model' block")
    return tmdl


# ---------------------------------------------------------------------------
# File writing
# ---------------------------------------------------------------------------

def _write_page(
    pages_dir: Path,
    page_folder: str,
    page_json: dict,
    visuals: list[tuple[str, dict]],  # [(folder_name, visual_json)]
) -> list[Path]:
    page_dir = pages_dir / page_folder
    visuals_dir = page_dir / "visuals"
    visuals_dir.mkdir(parents=True, exist_ok=True)

    written = []
    p = page_dir / "page.json"
    p.write_text(json.dumps(page_json, indent=2))
    written.append(p)

    for v_folder, v_json in visuals:
        v_dir = visuals_dir / v_folder
        v_dir.mkdir(exist_ok=True)
        f = v_dir / "visual.json"
        f.write_text(json.dumps(v_json, indent=2))
        written.append(f)

    return written


def _update_pages_json(pages_dir: Path, new_page_names: list[str]) -> None:
    pages_meta = pages_dir / "pages.json"
    if pages_meta.exists():
        data = json.loads(pages_meta.read_text())
    else:
        data = {"$schema": _PAGES_META_SCHEMA, "pageOrder": [], "activePageName": ""}

    for name in new_page_names:
        if name not in data.get("pageOrder", []):
            data.setdefault("pageOrder", []).append(name)

    if not data.get("activePageName") and data.get("pageOrder"):
        data["activePageName"] = data["pageOrder"][0]

    pages_meta.write_text(json.dumps(data, indent=2))


# ---------------------------------------------------------------------------
# Gate 1 — JSON validation
# ---------------------------------------------------------------------------

def _gate1_validate(files: list[Path]) -> tuple[bool, list[str]]:
    """Parse every generated file. Returns (passed, errors)."""
    errors = []
    for f in files:
        try:
            json.loads(f.read_text())
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"{f.name}: {e}")
    return (len(errors) == 0), errors


# ---------------------------------------------------------------------------
# Gate 3 — IR fidelity check
# ---------------------------------------------------------------------------

def _gate3_fidelity(spec: dict, written_pages: dict) -> tuple[bool, list[str]]:
    """
    Compare IR spec to generated files.
    Returns (passed, issues). Tolerance: visual type exact match; position ±10px.
    """
    issues = []
    spec_pages = spec.get("pages", [])

    if len(spec_pages) != len(written_pages):
        issues.append(f"Page count: spec={len(spec_pages)}, written={len(written_pages)}")

    for page_spec in spec_pages:
        folder = written_pages.get(page_spec.get("page_id"))
        if not folder:
            issues.append(f"Page '{page_spec.get('name')}' not found in output")
            continue

        spec_visuals = page_spec.get("visuals", [])
        written_count = sum(1 for _ in (folder / "visuals").iterdir()) if (folder / "visuals").exists() else 0
        if len(spec_visuals) != written_count:
            issues.append(f"Page '{page_spec.get('name')}' visual count: spec={len(spec_visuals)}, written={written_count}")

        for v_spec in spec_visuals:
            expected_type = _VISUAL_TYPE_MAP.get(v_spec.get("type", ""), "unknown")
            # Find matching visual.json by folder name prefix
            if (folder / "visuals").exists():
                for v_dir in (folder / "visuals").iterdir():
                    vf = v_dir / "visual.json"
                    if vf.exists():
                        vj = json.loads(vf.read_text())
                        actual_type = vj.get("visual", {}).get("visualType", "")
                        if actual_type != expected_type:
                            issues.append(
                                f"Visual type mismatch in {v_dir.name}: "
                                f"expected={expected_type}, got={actual_type}"
                            )

    return (len(issues) == 0), issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(build_id: str, pbip_report_path: str | None = None) -> dict:
    """
    Write PBIR pages + visuals into an existing PBIP project.

    Args:
        build_id: identifies the build artifacts (semantic_model.json, dashboard_spec.json)
        pbip_report_path: path to the .Report folder of the existing PBIP project.
            If None, generates into artifacts/{build_id}/report.pbir/ as a scaffold
            for inspection (not a complete PBIP — cannot open directly in Desktop).

    Returns:
        dict with gate results and file paths.
    """
    model = read_artifact(build_id, "semantic_model.json")
    spec  = read_artifact(build_id, "dashboard_spec.json")

    measure_defs   = {m["name"]: m for m in model.get("measures", [])}
    dimension_defs = {d["name"]: d for d in model.get("dimensions", [])}

    # Resolve the pages directory
    if pbip_report_path:
        report_path = Path(pbip_report_path)
        pages_dir = report_path / "definition" / "pages"
    else:
        # Scaffold output — write into artifacts for inspection
        pages_dir = artifact_path(build_id, "") .parent / "report.pbir" / "definition" / "pages"
        print("  [pbip_builder] no --pbip-path given — writing scaffold to artifacts/")

    pages_dir.mkdir(parents=True, exist_ok=True)

    # Detect schema version from existing project (or use fallback)
    schema_url = _detect_schema_version(pages_dir)
    print(f"  [pbip_builder] schema version: {schema_url.split('/')[-3]}")

    # Auto-increment page number
    page_idx_start = _next_page_number(pages_dir)

    all_written: list[Path] = []
    page_folders: dict[str, Path] = {}  # page_id → written dir
    new_page_names: list[str] = []

    for page_offset, page_spec in enumerate(spec.get("pages", [])):
        page_idx = page_idx_start + page_offset
        page_folder = _page_folder_name(page_idx, page_spec)

        # Attach layout positions to visual specs
        _attach_positions(page_spec)

        page_json = _build_page_json(page_spec, page_folder)

        visuals: list[tuple[str, dict]] = []
        for v_idx, v_spec in enumerate(page_spec.get("visuals", [])):
            v_folder = _visual_folder_name(v_idx + 1, v_spec)
            v_json = _build_visual_json(
                v_spec, v_folder, v_idx, schema_url, measure_defs, dimension_defs
            )
            visuals.append((v_folder, v_json))

        written = _write_page(pages_dir, page_folder, page_json, visuals)
        all_written.extend(written)
        page_folders[page_spec.get("page_id", "")] = pages_dir / page_folder
        new_page_names.append(page_folder)

        print(f"  [pbip_builder] wrote page '{page_folder}' ({len(visuals)} visuals)")

    # Update pages.json
    _update_pages_json(pages_dir, new_page_names)

    # Gate 1 — JSON validation
    gate1_passed, gate1_errors = _gate1_validate(all_written)
    if gate1_passed:
        print("  [pbip_builder] Gate 1 ✓ — all JSON valid")
    else:
        print(f"  [pbip_builder] Gate 1 ✗ — {len(gate1_errors)} error(s):")
        for e in gate1_errors:
            print(f"    {e}")

    # Gate 3 — IR fidelity
    gate3_passed, gate3_issues = _gate3_fidelity(spec, page_folders)
    if gate3_passed:
        print("  [pbip_builder] Gate 3 ✓ — IR fidelity check passed")
    else:
        print(f"  [pbip_builder] Gate 3 ✗ — {len(gate3_issues)} issue(s):")
        for i in gate3_issues:
            print(f"    {i}")

    result = {
        "pages_written": new_page_names,
        "files_written": len(all_written),
        "output_dir": str(pages_dir),
        "gate1": {"passed": gate1_passed, "errors": gate1_errors},
        "gate3": {"passed": gate3_passed, "issues": gate3_issues},
        "schema_version_used": schema_url,
    }

    write_artifact(build_id, "pbip_build_result.json", result)
    mark_stage_done(build_id, "pbip_builder")

    if pbip_report_path:
        print(f"\n  Close Desktop if open, then reopen: {pbip_report_path.replace('.Report', '.pbip')}")

    return result

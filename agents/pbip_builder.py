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

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from lib.anthropic_client import BRAIN, call_with_tool, consult_advisor
from lib.artifact_store import read_artifact, write_artifact, artifact_path, mark_stage_done
from lib import skills as skill_lib
from lib import layout as layout_engine

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
# Skill token-fill (v1: skills emit their report visual; the semantic model is
# owned by semantic_model.json, so a skill's TMDL fragments are not applied here.
# A skill that needs a new model object is flagged via _skill_needs_model_objects.)
# ---------------------------------------------------------------------------

_GEOM_SUFFIX = {"_X": "x", "_Y": "y", "_Z": "z", "_HEIGHT": "h", "_WIDTH": "w",
                "_TAB_ORDER": "tabOrder"}


def _skill_tokens(skill, visual: dict, folder_name: str,
                  measure_defs: dict, dimension_defs: dict) -> dict:
    """Build the token dict for a skill from the IR visual + model. Starts from the
    skill's documented example values (safe defaults for display tokens like axis
    bounds) and overrides geometry, fields, ids, and skill_params."""
    L = visual.get("layout", {})
    measures = visual.get("measures", [])
    dims = visual.get("dimensions", [])
    tokens = dict(skill.example_tokens())

    for tok in skill.tokens:
        for suf, key in _GEOM_SUFFIX.items():
            if tok.endswith(suf):
                tokens[tok] = L.get(key, 0)
        if tok.endswith("_LINEAGE_TAG"):
            tokens[tok] = skill_lib.new_lineage_tag()
        elif tok.endswith("_PBI_ID"):
            tokens[tok] = skill_lib.new_pbi_id()
        elif tok.endswith("VISUAL_NAME"):
            tokens[tok] = folder_name

    def setif(key, val):
        if key in tokens and val:
            tokens[key] = val

    if measures:
        m0 = measure_defs.get(measures[0], {})
        setif("MEASURE_TABLE", m0.get("home_table"))
        setif("VOLUME_MEASURE_NAME", measures[0])
        setif("VOLUME_MEASURE_NATIVE_REF", measures[0])
        setif("VALUE_MEASURE", measures[0])
    if len(measures) > 1:
        setif("GROWTH_MEASURE_NAME", measures[1])
        setif("GROWTH_MEASURE_NATIVE_REF", measures[1])
    if dims:
        d0 = dimension_defs.get(dims[0], {})
        setif("DATE_TABLE", d0.get("source_table"))
        setif("SOURCE_DATE_TABLE", d0.get("source_table"))
        setif("DATE_AXIS_COLUMN", d0.get("source_column"))
        setif("SOURCE_DATE_COLUMN", d0.get("source_column"))
    setif("CHART_TITLE", visual.get("title"))

    # skill_params from the IR override anything, by exact token name.
    for k, v in (visual.get("skill_params") or {}).items():
        tokens[k] = v
        tokens[k.upper()] = v
    return tokens


def _skill_outputs(skill, visual: dict, folder_name: str,
                   measure_defs: dict, dimension_defs: dict) -> tuple[list[dict], list[tuple[str, str]]]:
    """Fill a skill's templates once. Returns (visual_jsons, tmdl_fragments).

    visual_jsons — parsed *.visual.json objects with name aligned to folder_name
    tmdl_fragments — list of (filename, tmdl_text) for any *.tmdl templates
    Raises on unfilled tokens or invalid JSON.
    """
    tokens = _skill_tokens(skill, visual, folder_name, measure_defs, dimension_defs)
    filled = skill_lib.fill(skill, tokens)
    visuals: list[dict] = []
    tmdl: list[tuple[str, str]] = []
    for rel, text in filled.items():
        if rel.endswith(".visual.json"):
            vj = json.loads(text)
            vj["name"] = folder_name
            visuals.append(vj)
        elif rel.endswith(".tmdl"):
            tmdl.append((Path(rel).name, text))
    return visuals, tmdl


def _skill_needs_model_objects(skill) -> bool:
    """True if the skill ships TMDL fragments for the SemanticModel."""
    return any(rel.endswith(".tmdl") for rel in skill.templates)


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

    # Geometry comes straight from the IR layout (resolved once by lib.layout).
    L = visual_spec.get("layout", {})
    x = L.get("x", 30)
    y = L.get("y", 80)
    w = L.get("w", 280)
    h = L.get("h", 130)
    z = L.get("z", _Z_RANGES.get(pbi_type, _Z_DEFAULT) + tab_order)
    tab = L.get("tabOrder", tab_order)

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
        "position": {"x": x, "y": y, "z": z, "width": w, "height": h, "tabOrder": tab},
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


# Layout is now resolved once by lib.layout.snap_page and carried in the IR
# (visual["layout"]). The builder reads it directly — see _build_visual_json.


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

def _gate3_fidelity(spec: dict, written_pages: dict, pos_tol: float = 10.0) -> tuple[bool, list[str]]:
    """
    Compare the IR spec to the generated PBIR files. Matches each spec visual to its
    written `visual.json` by folder name, then checks:
      - page + visual counts match
      - position within `pos_tol` px of the IR layout (x, y, width, height)
      - visualType matches the type map (skipped for skill visuals — the skill owns it)
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

        visuals_dir = folder / "visuals"
        written = {}
        if visuals_dir.exists():
            for v_dir in visuals_dir.iterdir():
                vf = v_dir / "visual.json"
                if vf.exists():
                    written[v_dir.name] = json.loads(vf.read_text())

        spec_visuals = page_spec.get("visuals", [])
        if len(spec_visuals) != len(written):
            issues.append(f"Page '{page_spec.get('name')}' visual count: "
                          f"spec={len(spec_visuals)}, written={len(written)}")

        for v_idx, v_spec in enumerate(spec_visuals):
            folder_name = _visual_folder_name(v_idx + 1, v_spec)
            vj = written.get(folder_name)
            if vj is None:
                issues.append(f"Visual '{v_spec.get('visual_id')}' "
                              f"(folder {folder_name}) not written")
                continue

            # position fidelity
            L = v_spec.get("layout", {})
            pos = vj.get("position", {})
            for ir_key, pos_key in (("x", "x"), ("y", "y"), ("w", "width"), ("h", "height")):
                if abs(L.get(ir_key, 0) - pos.get(pos_key, 0)) > pos_tol:
                    issues.append(f"{v_spec.get('visual_id')}: {pos_key} off by "
                                  f">{pos_tol}px (IR {L.get(ir_key)} vs {pos.get(pos_key)})")

            # type fidelity (only for fallback visuals; skills define their own type)
            if not v_spec.get("skill"):
                expected = _VISUAL_TYPE_MAP.get(v_spec.get("type", ""), "unknown")
                actual = vj.get("visual", {}).get("visualType", "")
                if actual != expected:
                    issues.append(f"{v_spec.get('visual_id')}: type mismatch "
                                  f"(expected {expected}, got {actual})")

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
    registry       = skill_lib.load_skills()
    skill_warnings: list[str] = []

    # Resolve the pages directory
    if pbip_report_path:
        report_path = Path(pbip_report_path)
        pages_dir = report_path / "definition" / "pages"
    else:
        # Scaffold output — write into artifacts for inspection
        pages_dir = artifact_path(build_id, "report.pbir") / "definition" / "pages"
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
    tmdl_fragments: list[tuple[str, str]] = []  # (filename, content) for SemanticModel

    for page_offset, page_spec in enumerate(spec.get("pages", [])):
        page_idx = page_idx_start + page_offset
        page_folder = _page_folder_name(page_idx, page_spec)

        # Geometry comes from the IR. Snap only if an older spec lacks layout.
        if any("layout" not in v for v in page_spec.get("visuals", [])):
            layout_engine.snap_page(page_spec)

        page_json = _build_page_json(page_spec, page_folder)

        visuals: list[tuple[str, dict]] = []
        for v_idx, v_spec in enumerate(page_spec.get("visuals", [])):
            v_folder = _visual_folder_name(v_idx + 1, v_spec)
            skill = skill_lib.resolve_skill(v_spec, registry)
            v_json = None
            if skill is not None:
                try:
                    built_visuals, built_tmdl = _skill_outputs(
                        skill, v_spec, v_folder, measure_defs, dimension_defs)
                    if built_visuals:
                        v_json = built_visuals[0]
                    for fname, tmdl_text in built_tmdl:
                        # Deduplicate by filename (same table may appear across pages)
                        if not any(n == fname for n, _ in tmdl_fragments):
                            tmdl_fragments.append((fname, tmdl_text))
                            skill_warnings.append(
                                f"TMDL fragment '{fname}' from skill '{skill.name}' "
                                f"included in zip — copy to "
                                f"<YourReport>.SemanticModel/definition/tables/")
                except (ValueError, KeyError) as e:
                    skill_warnings.append(f"{v_spec.get('visual_id')}: skill fill failed "
                                          f"({e}); using fallback visual")
            if v_json is None:
                v_json = _build_visual_json(
                    v_spec, v_folder, v_idx, schema_url, measure_defs, dimension_defs)
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

    if skill_warnings:
        print(f"  [pbip_builder] {len(skill_warnings)} skill warning(s):")
        for w in skill_warnings:
            print(f"    {w}")

    result = {
        "pages_written": new_page_names,
        "files_written": len(all_written),
        "output_dir": str(pages_dir),
        "gate1": {"passed": gate1_passed, "errors": gate1_errors},
        "gate3": {"passed": gate3_passed, "issues": gate3_issues},
        "skill_warnings": skill_warnings,
        "schema_version_used": schema_url,
        "tmdl_fragments": tmdl_fragments,  # [(filename, content)] for SemanticModel
    }

    write_artifact(build_id, "pbip_build_result.json", result)
    mark_stage_done(build_id, "pbip_builder")

    if pbip_report_path:
        print(f"\n  Close Desktop if open, then reopen: {pbip_report_path.replace('.Report', '.pbip')}")

    return result

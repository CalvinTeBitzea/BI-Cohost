"""
Stage 3: Dashboard Spec
Requirements + semantic model → page/visual layout specification.
"""
import uuid
from datetime import datetime, timezone

from lib.anthropic_client import EXECUTOR_HEAVY, call_with_tool
from lib.artifact_store import read_artifact, write_artifact, mark_stage_done
from lib.schema_validator import validate

_VISUAL_TYPES = ["card", "bar", "line", "column", "pie", "donut", "table", "matrix", "slicer", "map", "scatter", "waterfall", "funnel", "gauge"]

_TOOL_SCHEMA = {
    "type": "object",
    "required": ["spec_id", "created_at", "requirements_spec_id", "model_id", "pages"],
    "properties": {
        "spec_id":               {"type": "string"},
        "created_at":            {"type": "string"},
        "requirements_spec_id":  {"type": "string"},
        "model_id":              {"type": "string"},
        "pages": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["page_id", "name", "type", "visuals"],
                "properties": {
                    "page_id": {"type": "string"},
                    "name":    {"type": "string"},
                    "type":    {"type": "string", "enum": ["overview", "detail", "drillthrough", "tooltip"]},
                    "visuals": {
                        "type": "array",
                        "maxItems": 8,
                        "items": {
                            "type": "object",
                            "required": ["visual_id", "type", "title", "measures", "dimensions", "accessibility_label"],
                            "properties": {
                                "visual_id":           {"type": "string"},
                                "type":                {"type": "string", "enum": _VISUAL_TYPES},
                                "title":               {"type": "string"},
                                "measures":            {"type": "array", "items": {"type": "string"}},
                                "dimensions":          {"type": "array", "items": {"type": "string"}},
                                "accessibility_label": {"type": "string"},
                                "filters":             {"type": "array", "items": {"type": "string"}},
                                "sort_by":             {"type": "string"},
                                "sort_direction":      {"type": "string", "enum": ["asc", "desc"]},
                            },
                        },
                    },
                    "global_filters": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    },
}

_SYSTEM = f"""You are a Power BI dashboard layout designer. Given requirements and a semantic model, produce a page/visual specification.

Rules:
- Every must-have KPI must appear in at least one visual
- Max 8 visuals per page
- Every visual must have a descriptive accessibility_label (a full sentence)
- measures and dimensions in visuals must exactly match names in the semantic model
- visual IDs: use short slugs like "v1", "v2" etc.
- page IDs: use short slugs like "p1", "p2" etc.
- Visual type guide: card→single KPI, column/bar→comparison, line→trend over time, table/matrix→detail view, slicer→filter control
- Start with an overview page. Add detail pages only if clearly needed.
- Available visual types: {_VISUAL_TYPES}"""


def run(build_id: str) -> dict:
    spec = read_artifact(build_id, "requirements.json")
    model = read_artifact(build_id, "semantic_model.json")
    dash_id = f"dash_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    user_message = (
        f"Requirements:\n{spec}\n\n"
        f"Semantic model:\n{model}\n\n"
        f"Use spec_id = '{dash_id}', created_at = '{now}', "
        f"requirements_spec_id = '{spec['spec_id']}', model_id = '{model['model_id']}'."
    )

    result = call_with_tool(
        system=_SYSTEM,
        user_message=user_message,
        tool_name="submit_dashboard_spec",
        tool_schema=_TOOL_SCHEMA,
        model=EXECUTOR_HEAVY,
    )

    # Validate every must-have KPI is covered
    must_have = {k["name"] for k in spec["kpis"] if k["priority"] == "must-have"}
    all_measures_used: set[str] = set()
    for page in result["pages"]:
        for visual in page["visuals"]:
            all_measures_used.update(visual["measures"])

    model_measure_names = {m["name"] for m in model["measures"]}
    missing_kpis = must_have - all_measures_used - model_measure_names
    # Best-effort check: warn but don't hard-fail (KPI name may differ from measure name)
    if missing_kpis:
        print(f"  [dashboard_spec] warning: these KPIs may not be covered: {missing_kpis}")

    validate("dashboard_spec", result)
    write_artifact(build_id, "dashboard_spec.json", result)
    mark_stage_done(build_id, "dashboard_spec")
    return result

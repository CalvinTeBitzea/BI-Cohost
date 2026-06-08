"""
Stage 1: Requirements Intake
Brief + column definitions → structured requirements spec.
"""
import uuid
from datetime import datetime, timezone

from lib.anthropic_client import BRAIN, call_with_tool
from lib.artifact_store import write_artifact, mark_stage_done
from lib.schema_validator import validate

_TOOL_SCHEMA = {
    "type": "object",
    "required": ["spec_id", "created_at", "raw_brief", "kpis", "columns", "grain", "audience", "refresh_cadence", "approved"],
    "properties": {
        "spec_id":          {"type": "string"},
        "created_at":       {"type": "string"},
        "raw_brief":        {"type": "string"},
        "kpis": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "description", "priority"],
                "properties": {
                    "name":        {"type": "string"},
                    "description": {"type": "string"},
                    "priority":    {"type": "string", "enum": ["must-have", "nice-to-have"]},
                },
            },
        },
        "columns": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "type"],
                "properties": {
                    "name":        {"type": "string"},
                    "type":        {"type": "string"},
                    "description": {"type": "string"},
                },
            },
        },
        "grain":            {"type": "string"},
        "audience":         {"type": "string"},
        "refresh_cadence":  {"type": "string"},
        "visual_preferences": {"type": "object"},
        "approved":         {"type": "boolean"},
        "notes":            {"type": ["string", "null"]},
    },
}

_SYSTEM = """You are a Power BI requirements analyst. Convert a freetext business brief into a structured requirements specification.

Rules:
- Extract every measurable KPI mentioned. Mark clear business metrics as must-have; nice-to-haves are enhancements.
- grain: describe what one row in the underlying data represents (e.g. "one transaction per customer per day").
- audience: who will use this dashboard (e.g. "sales managers", "executive team").
- refresh_cadence: how often data should refresh (e.g. "daily", "weekly").
- Set approved = true (no human gate in this MVP pipeline).
- Pass the provided columns through unchanged in the columns array.
- Be specific and actionable. No vague KPIs."""


def run(build_id: str, raw_brief: str, columns: list[dict]) -> dict:
    spec_id = f"spec_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    user_message = (
        f"Brief:\n{raw_brief}\n\n"
        f"Available columns: {columns}\n\n"
        f"Use spec_id = '{spec_id}' and created_at = '{now}'."
    )

    result = call_with_tool(
        system=_SYSTEM,
        user_message=user_message,
        tool_name="submit_requirements",
        tool_schema=_TOOL_SCHEMA,
        model=BRAIN,
    )

    validate("requirements", result)
    write_artifact(build_id, "requirements.json", result)
    mark_stage_done(build_id, "requirements")
    return result

"""
Stage 2: Semantic Model
Requirements spec → DAX measures, dimensions, relationships.
"""
import uuid
from datetime import datetime, timezone

from lib.anthropic_client import BRAIN, call_with_tool, consult_advisor
from lib.artifact_store import read_artifact, write_artifact, mark_stage_done
from lib.schema_validator import validate

_TOOL_SCHEMA = {
    "type": "object",
    "required": ["model_id", "created_at", "spec_id", "measures", "dimensions"],
    "properties": {
        "model_id":   {"type": "string"},
        "created_at": {"type": "string"},
        "spec_id":    {"type": "string"},
        "measures": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "dax", "format_string", "description", "home_table"],
                "properties": {
                    "name":          {"type": "string"},
                    "dax":           {"type": "string"},
                    "format_string": {"type": "string"},
                    "description":   {"type": "string"},
                    "home_table":    {"type": "string"},
                },
            },
        },
        "dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["name", "source_table", "source_column", "data_type"],
                "properties": {
                    "name":          {"type": "string"},
                    "source_table":  {"type": "string"},
                    "source_column": {"type": "string"},
                    "data_type":     {"type": "string"},
                },
            },
        },
        "relationships": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["from_table", "from_column", "to_table", "to_column", "cardinality", "cross_filter_direction"],
                "properties": {
                    "from_table":             {"type": "string"},
                    "from_column":            {"type": "string"},
                    "to_table":               {"type": "string"},
                    "to_column":              {"type": "string"},
                    "cardinality":            {"type": "string"},
                    "cross_filter_direction": {"type": "string"},
                },
            },
        },
        "advisor_guidance": {"type": ["string", "null"]},
    },
}

_SYSTEM = """You are a Power BI semantic model designer. Given a requirements spec and available columns, produce a semantic model.

DAX conventions (mandatory):
- Quote table names: 'TableName'[ColumnName]
- Use CALCULATE, FILTER, SUMX, COUNTROWS patterns — never raw aggregations without context
- No literal data values in DAX (no hardcoded dates, IDs, strings)
- format_string examples: "#,##0", "#,##0.00", "0.0%", "$#,##0", "0"

Model conventions:
- home_table: the table where the measure logically lives (usually the fact table)
- Each KPI in requirements must have at least one measure
- Dimensions map columns to their display names and data types
- For a single flat table, relationships array can be empty
- data_type values: text, integer, decimal, date, datetime, boolean"""


def run(build_id: str) -> dict:
    spec = read_artifact(build_id, "requirements.json")
    model_id = f"model_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()

    user_message = (
        f"Requirements spec:\n{spec}\n\n"
        f"Use model_id = '{model_id}' and created_at = '{now}' and spec_id = '{spec['spec_id']}'."
    )

    result = call_with_tool(
        system=_SYSTEM,
        user_message=user_message,
        tool_name="submit_semantic_model",
        tool_schema=_TOOL_SCHEMA,
        model=BRAIN,
    )

    # Advisor check: verify DAX correctness before committing
    context = f"Semantic model produced:\n{result}"
    question = "Do the DAX expressions look correct for these measures? Any double-counting risks or filter context issues?"
    guidance = consult_advisor(context, question)
    result["advisor_guidance"] = guidance

    validate("semantic_model", result)
    write_artifact(build_id, "semantic_model.json", result)
    mark_stage_done(build_id, "semantic_model")
    return result

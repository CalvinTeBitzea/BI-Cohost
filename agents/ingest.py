"""
Ingest — the entry point of the builder half.

The wireframing agent (BI-Workflow) co-emits two structured artifacts alongside its
human-facing wireframe.html:
  - a wireframe spec  → the dashboard_spec.json IR (pages/visuals/type/fields/grid/skill)
  - a semantic model  → semantic_model.json (measures+DAX, dimensions, relationships)

This stage validates both against the schemas, resolves pixel geometry from each
visual's `grid` (lib.layout.snap_page), and writes them into the build's artifacts so
`pbip_builder` can produce the PBIP. No design happens here — the wireframe is the
authoritative design.
"""
from __future__ import annotations

import json
from pathlib import Path

from lib import layout
from lib.artifact_store import write_artifact, mark_stage_done
from lib.schema_validator import validate


def run(build_id: str, wireframe_spec: str | dict, semantic_model: str | dict) -> dict:
    spec = _load(wireframe_spec)
    model = _load(semantic_model)

    validate("semantic_model", model)
    validate("dashboard_spec", spec)

    # Resolve geometry from grid for any visual missing layout; collect issues.
    issues: list[str] = []
    for page in spec.get("pages", []):
        _, page_issues = layout.snap_page(page)
        issues.extend(f"{page.get('page_id')}: {i}" for i in page_issues)

    # Confirm every referenced field exists in the model.
    issues.extend(_validate_refs(spec, model))

    validate("dashboard_spec", spec)  # re-validate after snap added layout

    write_artifact(build_id, "semantic_model.json", model)
    write_artifact(build_id, "dashboard_spec.json", spec)
    mark_stage_done(build_id, "ingest")

    n_visuals = sum(len(p.get("visuals", [])) for p in spec.get("pages", []))
    print(f"  [ingest] {len(spec.get('pages', []))} page(s), {n_visuals} visual(s)"
          + (f"; {len(issues)} issue(s)" if issues else ""))
    for i in issues:
        print(f"    {i}")
    return {"pages": len(spec.get("pages", [])), "visuals": n_visuals, "issues": issues}


def _validate_refs(spec: dict, model: dict) -> list[str]:
    measures = {m["name"] for m in model.get("measures", [])}
    dims = {d["name"] for d in model.get("dimensions", [])}
    bad = []
    for page in spec.get("pages", []):
        for v in page.get("visuals", []):
            for m in v.get("measures", []):
                if m not in measures:
                    bad.append(f"{v.get('visual_id')}: unknown measure '{m}'")
            for d in v.get("dimensions", []):
                if d not in dims:
                    bad.append(f"{v.get('visual_id')}: unknown dimension '{d}'")
    return bad


def _load(src: str | dict) -> dict:
    if isinstance(src, dict):
        return src
    return json.loads(Path(src).read_text())

# IR → PBIR Mapping Rules

The IR (Intermediate Representation) is the dashboard_spec.json produced by the
dashboard_spec agent. The pbip_builder maps each IR element to PBIR files.

## Project structure written by the agent

```
SalesReport.Report/
  definition/
    pages/
      pages.json                     ← UPDATED: add new page to pageOrder
      pg01Overview/                  ← CREATED per page
        page.json                    ← CREATED
        visuals/
          v01KpiRevenue/             ← CREATED per visual
            visual.json              ← CREATED
```

Files touched by the agent: only `pages/` folder contents + `pages.json` update.
Files NOT touched: report.json, version.json, .platform, definition.pbir — Desktop owns these.

## Page mapping

| IR field | PBIR file/property |
|---|---|
| `page.page_id` | Folder name: `pg{idx:02d}{slug}` |
| `page.name` | `page.json → displayName` |
| `page.page_id` (slug) | `page.json → name` (must match folder name) |
| canvas | `page.json → width=1280, height=720, displayOption=FitToPage` |

## Visual mapping

| IR field | PBIR file/property |
|---|---|
| `visual.visual_id` | Folder name + `visual.json → name` (must match) |
| `visual.type` | `visual.json → visual.visualType` (via type map) |
| `visual.title` | (not in PBIR visual.json — set via objects.title if needed) |
| `visual.measures` | Projections in appropriate query roles |
| `visual.dimensions` | Projections in appropriate query roles |
| layout position | `visual.json → position.{x,y,z,width,height,tabOrder}` |

## Field binding: IR → PBIR

IR measures/dimensions are names only. The builder looks them up in semantic_model.json:
- measures → `model.measures[name]` → `{home_table, name}` → Measure projection
- dimensions → `model.dimensions[name]` → `{source_table, source_column}` → Column projection

The PBIR binding expression for a **measure**:
```json
{
  "field": { "Measure": { "Expression": { "SourceRef": { "Entity": "home_table" } }, "Property": "measure_name" } },
  "queryRef": "home_table.measure_name",
  "nativeQueryRef": "measure_name"
}
```

The PBIR binding expression for a **column (dimension)**:
```json
{
  "field": { "Column": { "Expression": { "SourceRef": { "Entity": "source_table" } }, "Property": "source_column" } },
  "queryRef": "source_table.source_column",
  "nativeQueryRef": "source_column"
}
```

## Gate 1 — Schema validation

After generating all files, parse every .json file written. Any parse error = Gate 1 fail.
Full JSON-schema validation (against pinned schemas) is a stretch goal.
Gate 1 pass = all files parse cleanly as valid JSON.

## Gate 3 — IR fidelity check

Compare generated PBIR back to IR:
- Page count matches
- Visual count per page matches
- Each visual has the correct `visualType`
- Positions within ±10px tolerance
- All field bindings present in queryState

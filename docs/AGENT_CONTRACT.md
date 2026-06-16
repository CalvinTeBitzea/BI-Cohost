# BI-Workflow → bi-cohost: the build contract

The wireframing agent (BI-Workflow) owns requirements + design. Alongside the
human-facing `wireframe.html`, it **co-emits two structured artifacts** that the
bi-cohost builder consumes to produce a production Power BI project (PBIP):

```
BI-Workflow agent ──▶ wireframe.html        (human sign-off view)
                  ──▶ dashboard_spec.json   (the IR — what to build)         ┐
                  ──▶ semantic_model.json    (measures + DAX, dims, rels)     ┘─▶ bi-cohost
                                                                                   ├ ingest (validate + snap geometry)
                                                                                   └ pbip_builder (PBIR via skills)
```

`wireframe.html` and `dashboard_spec.json` describe the **same** page — the HTML is the
render, the JSON is the machine contract. Keep them in lock-step.

Build command:
```
python agents/conductor.py \
  --wireframe-spec dashboard_spec.json \
  --semantic-model semantic_model.json \
  --build-id <id> [--pbip-path /path/MyReport.Report]
```

---

## 1. `semantic_model.json`

Schema: `schemas/semantic_model.json`. Carries everything the report binds to.

```jsonc
{
  "model_id": "retail_sales_v1", "created_at": "<iso>", "spec_id": "<req id>",
  "measures": [
    {"name": "Net Revenue", "home_table": "Fact_Sales", "format_string": "\\$#,0",
     "description": "SUM(TotalAmount) - SUM(Discount)",
     "dax": "SUM('Fact_Sales'[TotalAmount]) - SUM('Fact_Sales'[Discount])"}
  ],
  "dimensions": [
    {"name": "Category", "source_table": "Dim_Product", "source_column": "Category", "data_type": "string"}
  ],
  "relationships": [
    {"from_table": "Dim_Product", "from_column": "ProductKey",
     "to_table": "Fact_Sales", "to_column": "ProductKey",
     "cardinality": "1:N", "cross_filter_direction": "single"}
  ]
}
```

Every `measures`/`dimensions` name referenced by a visual **must** exist here (ingest
validates and reports unknown refs).

---

## 2. `dashboard_spec.json` (the IR)

Schema: `schemas/dashboard_spec.json`. One entry per page; each visual names its type,
fields, grid position, and (optionally) a skill.

```jsonc
{
  "spec_id": "...", "created_at": "<iso>",
  "requirements_spec_id": "<req id>", "model_id": "<model id>",
  "template": "wireframe:retail-sales-analytics",   // free label
  "missing": [],                                      // open questions / unbindable, if any
  "pages": [{
    "page_id": "p1", "name": "Executive Summary", "type": "overview",
    "visuals": [{
      "visual_id": "p1c1",
      "type": "line",                                 // IR type (see vocabulary)
      "title": "Net Revenue & Profit by Month",
      "measures": ["Net Revenue", "Gross Profit"],     // names from semantic_model
      "dimensions": ["MonthName"],
      "accessibility_label": "Dual line of revenue and profit by month",
      "skill": null,                                   // or a pbi-skills/ name
      "skill_params": {},                              // skill display overrides
      "grid": {"col": 0, "row": 2, "colSpan": 7, "rowSpan": 1}
    }]
  }]
}
```

### Grid (band model, 12 columns)
`grid.row` selects a horizontal **band**; `col`/`colSpan` place within it; `rowSpan`
spans bands. The builder resolves pixel `layout {x,y,w,h,z,tabOrder}` from this — do not
hand-place pixels.

| row | band | typical contents |
|---|---|---|
| 0 | filter bar (thin) | slicers |
| 1 | KPI band | cards |
| 2 | chart row A | charts/tables |
| 3 | chart row B | charts/tables |

`colSpan`s in a row should sum to 12. Common splits: KPIs `4,2,2,2,2`; 60/40 `7,5`;
50/50 `6,6`; full `12`. Max 20 visuals per page.

### Visual vocabulary (wireframe `.type` → IR `type` + `skill`)

| Wireframe type | `type` | `skill` |
|---|---|---|
| KPI card | `card` | — |
| Dual line / line | `line` | — |
| Donut | `donut` | — |
| Pie | `pie` | — |
| Clustered bar (vertical) | `column` | — |
| Horizontal bar | `bar` | — |
| Scatter | `scatter` | — |
| Ranked table | `table` | — |
| Matrix | `matrix` | — |
| Slicer | `slicer` | — |
| **Bar + cumulative line** (Pareto) | `column` | `line-column-combo-chart` |
| **Bar + line combo** (e.g. value + margin) | `column` | `line-column-combo-chart` |

**Skilled visuals** render the rich, validated PBIR template from `pbi-skills/<skill>/`.
Field order matters: `measures[0]` = bars (primary Y), `measures[1]` = line (secondary Y),
`dimensions[0]` = category/axis. Display overrides (title, axis bounds, highlight) go in
`skill_params` by the skill's token name (e.g. `"CHART_TITLE"`). A visual with no matching
skill is built by the fallback path (correct `visualType` + field bindings, minimal format).

New skills drop into `pbi-skills/` and become referenceable by name with no builder change.

---

## 3. What ingest checks

- both files validate against their schemas;
- every visual field resolves to a real measure/dimension;
- geometry snaps with no overlaps / out-of-bounds (issues are reported, not silently dropped);
- unbindable refs and skill caveats surface as `missing` / warnings.

See `examples/retail/` for a complete, buildable reference (the retail wireframe + brief
encoded as these two files) and `tests/test_pbip_builder.py` for the end-to-end proof.

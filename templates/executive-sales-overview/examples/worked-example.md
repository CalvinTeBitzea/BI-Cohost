# Worked Example — Executive Sales Overview

A concrete instantiation of `executive-sales-overview`, end to end. Doubles as a test
fixture for `templates.select_template → bind → reconcile → snap`.

## Input brief

> "Monthly sales overview for the leadership team. They need to see total revenue, gross
> margin %, and order count up top, the revenue trend with month-over-month growth, and a
> breakdown of revenue by product category. Let them filter by region."

Must-have KPIs: **Revenue**, **Gross Margin %**, **Order Count**.

## Input semantic model (excerpt)

```jsonc
{
  "measures": [
    { "name": "Revenue",          "home_table": "Sales", "format_string": "\\$#,0",   "dax": "SUM('Sales'[Amount])" },
    { "name": "Gross Margin %",   "home_table": "Sales", "format_string": "0.0%",     "dax": "DIVIDE([Gross Profit],[Revenue])" },
    { "name": "Order Count",      "home_table": "Sales", "format_string": "#,0",      "dax": "DISTINCTCOUNT('Sales'[OrderId])" },
    { "name": "MoM Growth Rate %","home_table": "Sales", "format_string": "0.0%",     "dax": "VAR ... RETURN DIVIDE(cur-prev, prev)" }
  ],
  "dimensions": [
    { "name": "Month",    "source_table": "DimDate",    "source_column": "MonthYearLabel", "data_type": "string" },
    { "name": "Category", "source_table": "DimProduct", "source_column": "Category",       "data_type": "string" },
    { "name": "Region",   "source_table": "DimRegion",  "source_column": "Region",         "data_type": "string" }
  ]
}
```

## Select

Brief intent ("monthly overview for leadership", KPI band + trend + breakdown + filter)
matches `executive-sales-overview` over other archetypes. ✓

## Bind

| slot | data_role | bound to | result |
|---|---|---|---|
| f1 | dimension:date      | `DimDate[MonthYearLabel]`                | ✓ |
| f2 | dimension:category  | `DimRegion[Region]`                      | ✓ |
| f3 | dimension:category  | `DimProduct[Category]`                   | ✓ |
| s1 | measure              | `Sales[Revenue]`                         | ✓ |
| s2 | measure              | `Sales[Gross Margin %]`                  | ✓ |
| s3 | measure              | `Sales[Order Count]`                     | ✓ |
| s4 | measure              | — (no 4th must-have KPI)                 | dropped (optional) |
| s5 | measure over date    | `Sales[Revenue]` over `DimDate[MonthYearLabel]` (+ `Sales[MoM Growth Rate %]`) | ✓ |
| s6 | measure over category| `Sales[Revenue]` over `DimProduct[Category]` | ✓ |
| s7 | measure over category| `Sales[Order Count]` over `DimRegion[Region]` | ✓ |

`missing`: none.

## Reconcile

- Filter bar: date (f1) + region (f2) + category (f3) all bind → 3 slicers across the top.
- All three must-have KPIs (Revenue, Margin %, Orders) are bound to s1–s3. No extra cards needed.
- s4 optional + unbound → dropped.
- s5 trend: both `Revenue` and `MoM Growth Rate %` bind → skill resolves to
  **`line-column-combo-chart`** (Revenue bars, primary Y; MoM Growth % line, secondary Y).
- s7 detail: a second breakdown (Orders by Region) adds information → kept as a `table`.
- Visual count = 9 → over the cap of 8. Drop in priority order: `f3` (category slicer) →
  **8 visuals**. ✓

## Resolved IR (dashboard_spec.json, one page — 8 visuals, f3 dropped by the cap)

```jsonc
{
  "page_id": "p1", "name": "Overview", "type": "overview",
  "visuals": [
    { "visual_id": "f1", "type": "slicer", "title": "Month",
      "measures": [], "dimensions": ["Month"], "skill": null,
      "grid": {"col":0,"row":0,"colSpan":4,"rowSpan":1},
      "layout": {"x":30,"y":16,"w":390,"h":48,"z":500} },

    { "visual_id": "f2", "type": "slicer", "title": "Region",
      "measures": [], "dimensions": ["Region"], "skill": null,
      "grid": {"col":4,"row":0,"colSpan":4,"rowSpan":1},
      "layout": {"x":445,"y":16,"w":390,"h":48,"z":501} },

    { "visual_id": "s1", "type": "card", "title": "Revenue",
      "measures": ["Revenue"], "dimensions": [], "skill": null,
      "grid": {"col":0,"row":1,"colSpan":3,"rowSpan":1},
      "layout": {"x":30,"y":80,"w":280,"h":130,"z":1000} },

    { "visual_id": "s2", "type": "card", "title": "Gross Margin %",
      "measures": ["Gross Margin %"], "dimensions": [], "skill": null,
      "grid": {"col":3,"row":1,"colSpan":3,"rowSpan":1},
      "layout": {"x":330,"y":80,"w":280,"h":130,"z":1001} },

    { "visual_id": "s3", "type": "card", "title": "Order Count",
      "measures": ["Order Count"], "dimensions": [], "skill": null,
      "grid": {"col":6,"row":1,"colSpan":3,"rowSpan":1},
      "layout": {"x":630,"y":80,"w":280,"h":130,"z":1002} },

    { "visual_id": "s5", "type": "line", "title": "Revenue & MoM Growth",
      "measures": ["Revenue","MoM Growth Rate %"], "dimensions": ["Month"],
      "skill": "line-column-combo-chart",
      "skill_params": { "chart_title": "Revenue & MoM Growth",
                        "volume_measure": "Revenue", "growth_measure": "MoM Growth Rate %",
                        "date_axis": "Month" },
      "grid": {"col":0,"row":2,"colSpan":8,"rowSpan":2},
      "layout": {"x":30,"y":230,"w":810,"h":470,"z":2000} },

    { "visual_id": "s6", "type": "bar", "title": "Revenue by Category",
      "measures": ["Revenue"], "dimensions": ["Category"], "skill": null,
      "grid": {"col":8,"row":2,"colSpan":4,"rowSpan":1},
      "layout": {"x":860,"y":230,"w":390,"h":230,"z":2001} },

    { "visual_id": "s7", "type": "table", "title": "Orders by Region",
      "measures": ["Order Count"], "dimensions": ["Region"], "skill": null,
      "grid": {"col":8,"row":3,"colSpan":4,"rowSpan":1},
      "layout": {"x":860,"y":470,"w":390,"h":230,"z":2002} }
  ]
}
```

(Exact pixel `layout` values are whatever `lib/layout.snap_page` produces; the numbers
above illustrate the intent — a top filter bar, a KPI band of 3, a tall combo trend on the
left, a breakdown top-right over a detail table bottom-right.)

## Expected build / wireframe

- Wireframe shows 8 boxes in these positions, hi-fi: 2 top slicers, 3 KPI cards, a combo
  chart (bars + secondary-axis growth line, italic legend), a horizontal bar breakdown, and
  a detail table.
- PBIP build emits `line-column-combo-chart`'s full `visual.json` for s5 (filled from
  `skill_params` + bound fields + `layout`), and fallback minimal visuals for the slicers,
  cards, bar, and table. Gate 3: 8 visuals, types/positions match the IR within ±10px.

---
name: line-column-combo-chart
description: Add a dual-axis combo chart — bars for a volume count on the primary Y axis, a line for MoM growth rate % on the secondary Y axis — with italic legend, data labels, rounded border, and theme-colour-aligned axis labels.
---

# Line + Column Combo Chart — Volume with MoM Growth

## Goal
Add a `lineStackedColumnComboChart` visual that plots a volume measure (bars, primary Y)
alongside a month-over-month growth rate percentage (line, secondary Y). The chart uses
an italic legend, data labels on both series, a rounded white-background border, and
theme-colour-aligned axis labels. A specific category value in the bar series can be
highlighted with a distinct theme colour.

## Prerequisites
- Existing semantic model with a date dimension table containing a month-year label column
- Existing fact table from which to derive a row-count volume measure
- Two pre-existing measures that feed the MoM growth rate calculation (last-month value
  and current-period value)
- Power BI project open in developer / TMDL format

## Token Table

| Token | Description | Example |
|---|---|---|
| `<MEASURE_TABLE>` | Name of the measures table | `_Measures` |
| `<MEASURE_TABLE_LINEAGE_TAG>` | UUID for the measures table | `82b3a42d-fec9-4c43-bd95-92526dd6ea82` |
| `<MEASURE_TABLE_PBI_ID>` | 32-char hex PBI annotation ID | `617eebb3a74c4bd2ab080a2ca81c0bcc` |
| `<MEASURE_TABLE_ANNOTATION_KEY>` | UUID annotation key on the table | `436ba87b-9c83-4389-a31b-ebd06a36be98` |
| `<MEASURE_TABLE_COLUMN_LINEAGE_TAG>` | UUID for the placeholder column | `3de5d470-f5f7-4dd4-9008-ed6df41b669e` |
| `<VOLUME_MEASURE_NAME>` | Name of the count / volume measure | `_Incident Count` |
| `<VOLUME_MEASURE_DAX>` | DAX expression for volume | `COUNTROWS('PBI vFactIncidentsManualHandling')` |
| `<VOLUME_MEASURE_LINEAGE_TAG>` | UUID for volume measure | `80b10bb3-0efb-4a78-a4f1-5a2f30124f66` |
| `<VOLUME_MEASURE_NATIVE_REF>` | `nativeQueryRef` for Y projection | `_Incident Count1` |
| `<GROWTH_MEASURE_NAME>` | Name of the MoM % measure | `MoM Growth Rate %` |
| `<GROWTH_MEASURE_DAX>` | Full multi-line DAX body (see worked example) | — |
| `<GROWTH_MEASURE_LINEAGE_TAG>` | UUID for growth measure | `4589adc3-b639-49e4-90f3-772c8579e529` |
| `<GROWTH_MEASURE_NATIVE_REF>` | `nativeQueryRef` for Y2 projection | `MoM Growth Rate %1` |
| `<DATE_TABLE>` | Existing date dimension table | `CSL vDimDate` |
| `<DATE_AXIS_COLUMN>` | Month-year label column for X axis | `MonthYearLabel` |
| `<PRIMARY_Y_AXIS_END>` | Max value for primary Y axis | `70D` |
| `<SECONDARY_Y_AXIS_START>` | Min value for secondary Y axis | `-5D` |
| `<SECONDARY_Y_AXIS_END>` | Max value for secondary Y axis | `2D` |
| `<CATEGORY_MAX_MARGIN>` | Max margin factor for category labels | `40L` |
| `<DATA_POINT_ENTITY>` | Fact table for data point colour override | `PBI vFactIncidentsManualHandling` |
| `<DATA_POINT_CATEGORY_COLUMN>` | Column used in the highlight selector | `(Manual Handling) Category` |
| `<DATA_POINT_CATEGORY_VALUE>` | Literal category value to highlight | `Patient / Client / Resident` |
| `<DATA_POINT_COLOR_ID>` | ThemeDataColor ColorId for highlight | `9` |
| `<CHART_TITLE>` | Visual title text | `Incidents Trend` |
| `<VISUAL_NAME>` | 20-char hex visual container name | `0c2aefda03bead008b21` |
| `<CHART_X>` | Canvas X position | `95.204056991064959` |
| `<CHART_Y>` | Canvas Y position | `118.69596715769137` |
| `<CHART_Z>` | Z-order | `0` |
| `<CHART_HEIGHT>` | Visual height | `260.26563631972954` |
| `<CHART_WIDTH>` | Visual width | `1004.5882637044192` |
| `<CHART_TAB_ORDER>` | Tab order | `0` |

## Ordered File Map

1. **Create** `SemanticModel/definition/tables/<MEASURE_TABLE>.tmdl`
   Source: `templates/measures-table.tmdl` — new measures table with volume and growth rate measures.

2. **Insert** one line into `SemanticModel/definition/model.tmdl` immediately before the `ref cultureInfo` line.
   Fragment: `templates/model-ref.tmdl`

3. **Create** `Report/definition/pages/<PAGE_ID>/visuals/<VISUAL_NAME>/visual.json`
   Source: `templates/combo-chart.visual.json` — the dual-axis combo chart visual.

## Validation

- `<MEASURE_TABLE>` appears in Model view with two measures and no relationships to other tables
- Chart renders bars for `<VOLUME_MEASURE_NAME>` (primary Y) and a line for `<GROWTH_MEASURE_NAME>` (secondary Y)
- Legend is visible, italic, 9 pt, with no legend title
- Primary Y axis shows values, no axis title; secondary Y axis is hidden
- Bar data labels show at 10 pt with 1 decimal place; line data labels appear above each point
- Highlighted bar (`<DATA_POINT_CATEGORY_VALUE>`) renders in ThemeDataColor `<DATA_POINT_COLOR_ID>`
- Visual has a white background, rounded border (radius 10, colour `#E6E6E6`), and title `<CHART_TITLE>`

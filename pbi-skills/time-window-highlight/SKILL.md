---
name: time-window-highlight
description: Highlight a user-selected date range on a Power BI line chart using a disconnected slicer, X-axis reference lines with shading, and a visual calculation that shows data labels only within the selected window.
---

# Time Window Highlight — Line Chart with Slicer

## Goal
Add a disconnected date-range slicer that lets users select a time window on a
line chart. The chart highlights the window with X-axis reference lines and
background shading, and shows data labels only for points inside the selection.

## Prerequisites
- Existing semantic model with a date dimension and at least one value measure
- The date dimension has a column suitable for the chart's category axis
- Power BI project open in developer / TMDL format

## Token Table

| Token | Description | Example |
|---|---|---|
| `<SLICER_TABLE_NAME>` | Name for the new disconnected slicer table | `dimDate Slicer` |
| `<SOURCE_DATE_TABLE>` | Existing date dimension table | `dimDate` |
| `<SOURCE_DATE_COLUMN>` | Date column in the date dimension | `Date` |
| `<DATE_AXIS_COLUMN>` | Column used as the chart X axis | `EOmonth` |
| `<MEASURE_TABLE>` | Table that holds DAX measures | `_Measures` |
| `<VALUE_MEASURE>` | Existing measure to plot as the main series | `Sales` |
| `<WINDOW_START_MEASURE>` | New measure: MIN of slicer selection | `Window Start Date` |
| `<WINDOW_END_MEASURE>` | New measure: MAX of slicer selection | `Window End Date` |
| `<WINDOW_CALC_NAME>` | Visual calculation series name | `Data Labels Window` |
| `<CHART_TITLE>` | Line chart title text | `Sales` |
| `<DEFAULT_START_DATE>` | Default slicer start datetime literal | `datetime'2025-08-30T01:00:00'` |
| `<DEFAULT_END_DATE>` | Default slicer end datetime literal | `datetime'2026-06-27T01:00:00'` |
| `<FILTER_START_DATE>` | Filter lower bound (midnight, same day as start) | `datetime'2025-08-30T00:00:00'` |
| `<FILTER_END_DATE>` | Filter upper bound (midnight, day after end) | `datetime'2026-06-28T00:00:00'` |
| `<SLICER_TABLE_LINEAGE_TAG>` | Fresh UUID for the slicer table | `4043821c-b0f7-4c37-8bc5-b40d2aadee9a` |
| `<SLICER_COLUMN_LINEAGE_TAG>` | Fresh UUID for the slicer date column | `0a04fbc5-36e8-4e1b-8e16-0174dfd1bdbe` |
| `<SLICER_TABLE_PBI_ID>` | 32-char hex PBI annotation ID | `1ce96267a7de4a62afe0bcb32964a8f9` |
| `<WINDOW_START_LINEAGE_TAG>` | Fresh UUID for Window Start measure | `78e9a5f8-ead6-4eac-9465-dbf4a20b1323` |
| `<WINDOW_END_LINEAGE_TAG>` | Fresh UUID for Window End measure | `15a27af7-0669-4a4d-95ed-97e2d18a50ab` |
| `<VISUAL_NAME_SLICER>` | 20-char hex slicer visual container name | `b3734404e96bdca0e3d2` |
| `<VISUAL_NAME_LINE_CHART>` | 20-char hex line chart visual container name | `c1c97d02ce9912d08174` |
| `<FILTER_NAME_SLICER>` | 20-char hex filter ID for slicer visual | `98ddb8015097c5696056` |
| `<FILTER_NAME_SALES>` | 20-char hex filter ID for measure filter | `1800a24cb77220311b60` |
| `<FILTER_NAME_DATE>` | 20-char hex filter ID for date axis filter | `e70a12013c10005427d5` |
| `<SLICER_X>` / `<SLICER_Y>` / `<SLICER_Z>` / `<SLICER_HEIGHT>` / `<SLICER_WIDTH>` / `<SLICER_TAB_ORDER>` | Slicer position, size, z-order, tab order | `1277.78` / `240` / `1` / `87.78` / `261.11` / `1` |
| `<CHART_X>` / `<CHART_Y>` / `<CHART_Z>` / `<CHART_HEIGHT>` / `<CHART_WIDTH>` / `<CHART_TAB_ORDER>` | Chart position, size, z-order, tab order | `878.89` / `218.89` / `0` / `430` / `712.22` / `0` |

## Ordered File Map

1. **Create** `SemanticModel/definition/tables/<SLICER_TABLE_NAME>.tmdl`
   Source: `templates/dimDate-Slicer.tmdl` — the new disconnected calculated table.

2. **Append** two measure blocks into `SemanticModel/definition/tables/<MEASURE_TABLE>.tmdl`
   before the existing `partition` line.
   Fragment: `templates/measures-window-additions.tmdl`

3. **Append** one line to `SemanticModel/definition/model.tmdl` after the last existing `ref table` line.
   Fragment: `templates/model-ref.tmdl`

4. **Create** folder `Report/definition/pages/<PAGE_ID>/visuals/<VISUAL_NAME_SLICER>/`
   and write `visual.json` from `templates/slicer.visual.json`.

5. **Create** folder `Report/definition/pages/<PAGE_ID>/visuals/<VISUAL_NAME_LINE_CHART>/`
   and write `visual.json` from `templates/line-chart.visual.json`.

## Validation

- In Model view, `<SLICER_TABLE_NAME>` has no relationships to any other table
- Slicer on canvas shows a "Between" date picker with two date inputs
- Line chart renders two Y series: main line without data labels, window series with data labels
- Moving slicer boundaries shifts the shaded region and visible data labels together
- Hovering a data point in the chart tooltip shows `<WINDOW_START_MEASURE>` and `<WINDOW_END_MEASURE>`

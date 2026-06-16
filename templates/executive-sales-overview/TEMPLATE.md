---
name: executive-sales-overview
description: One-page monthly performance review for executives — a KPI band across the top, a large trend in the centre-left, a categorical breakdown top-right, and an optional filter. Reads at a glance, leads with outcomes.
audience: executive / leadership
cadence: monthly
canvas: 1280x720
---

# Executive Sales Overview

A single overview page that answers "how are we tracking this month?" for a leadership
audience. The hierarchy is deliberate: headline KPIs first, then the trend that explains
them, then the breakdown that decomposes them.

## Data contract (minimal model assumed)

The template binds against a semantic model that provides at least:

| need | kind | example |
|---|---|---|
| date dimension | a date axis column (month-year grain) | `DimDate[MonthYearLabel]` |
| primary measure | an additive value measure | `Sales[Revenue]` |
| categorical dimension | a breakdown axis (low cardinality) | `DimProduct[Category]` |

Nice-to-have (unlock extra slots when present):

| need | kind | unlocks |
|---|---|---|
| secondary measures | additive value / ratio | extra KPI cards (s2–s4) |
| MoM-growth measure | period-over-period ratio | combo trend (bars + growth line) on s5 |

## Slots

`data_role` vocabulary: `measure` (single additive measure) · `measure over date`
(measure against the date axis column) · `measure over category` (measure against a
categorical dimension) · `dimension:date` / `dimension:category` (a slicer field).

`grid` is `col,row,colSpan,rowSpan` on a 12-column canvas (1280×720). `row` selects a
**role band** the snap engine owns vertically; `col`/`colSpan` place horizontally within it:

- `row 0` — **filter bar** (slicers, thin band across the top)
- `row 1` — **KPI band** (cards)
- `row 2` — **chart row A**, `row 3` — **chart row B** (a chart with `rowSpan 2` spans both)

| slot | role | skill | data_role | grid (col,row,colSpan,rowSpan) | required |
|---|---|---|---|---|---|
| f1 | filter    | slicer                  | dimension:date       | 0,0,4,1 | yes |
| f2 | filter    | slicer                  | dimension:category   | 4,0,4,1 | no  |
| f3 | filter    | slicer                  | dimension:category   | 8,0,4,1 | no  |
| s1 | kpi       | card                    | measure              | 0,1,3,1 | yes |
| s2 | kpi       | card                    | measure              | 3,1,3,1 | no  |
| s3 | kpi       | card                    | measure              | 6,1,3,1 | no  |
| s4 | kpi       | card                    | measure              | 9,1,3,1 | no  |
| s5 | trend     | line-column-combo-chart | measure over date    | 0,2,8,2 | yes |
| s6 | breakdown | bar                     | measure over category| 8,2,4,1 | yes |
| s7 | detail    | table                   | measure over category| 8,3,4,1 | no  |

**Allowed skills per slot** (first is the default; later entries are fallbacks):
- `f1–f3` filter → `slicer`
- `s1–s4` kpi → `card`
- `s5` trend → `line-column-combo-chart`, `time-window-highlight`, `line`
- `s6` breakdown → `bar`, `column`
- `s7` detail → `table`, `matrix`

Layout shape: a top filter bar (date + up to two more slicers), a KPI band beneath it, then
a tall combo **trend** filling the centre-left and a **breakdown** (top-right) over a
**detail** table (bottom-right) in the right column.

## Reconciliation rules

- **Filter bar:** always include `f1` (date slicer) when a date dimension exists. Add `f2`/`f3`
  from the brief's filter dimensions (region, then one more). Hard cap of **3 slicers**.
- Every **must-have KPI** in the brief that is not already bound to a card slot → add a
  `card` slot to the KPI band, left to right. Hard cap of **4 cards** (s1–s4).
- An **optional** slot whose `data_role` cannot bind to the model → **drop it**.
- Hard cap of **8 visuals** per page (drop optional slots in priority order:
  `f3 → s4 → s7 → f2` until satisfied).
- **s5 (trend) is required and never dropped.** If the model has no date axis column,
  do **not** silently swap — emit a `missing` flag for human review.
- Trend skill selection: use `line-column-combo-chart` when both a value measure and a
  MoM-growth measure bind; otherwise fall back to a plain `line`.
- s6 (breakdown) is required; if no categorical dimension binds, flag for human review.
- s7 (detail) is optional; drop if no second categorical breakdown adds information.

## Theme (IBCS)

| token | colour | use |
|---|---|---|
| actual     | `#0C3549` | primary series / actual values |
| comparison | `#CCCCCC` | prior period / budget |
| positive   | `#44C088` | favourable variance |
| negative   | `#ED7373` | unfavourable variance |

Font: Arial. Visual borders: 1px `#E6E6E6`, radius 10, white background.

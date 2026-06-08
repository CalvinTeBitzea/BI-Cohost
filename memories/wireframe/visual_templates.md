# Known-Good Visual Templates

Source: lukasreese/powerbi-claude-skills SKILL.md, validated 2026-06-08.

## Field reference patterns

### Measure
```json
{ "Measure": { "Expression": { "SourceRef": { "Entity": "TableName" } }, "Property": "MeasureName" } }
```

### Column
```json
{ "Column": { "Expression": { "SourceRef": { "Entity": "TableName" } }, "Property": "ColumnName" } }
```

**Rules:** Entity = exact table name (case-sensitive). Property = exact measure/column name (case-sensitive).
`queryRef` = "Table.Field", `nativeQueryRef` = "Field" (just the name, no table prefix).

---

## Visual type → PBIR visualType mapping

| IR type | PBIR visualType |
|---|---|
| card | cardVisual |
| bar | clusteredBarChart |
| column | clusteredColumnChart |
| line | lineChart |
| table | tableEx |
| slicer | slicer |
| matrix | pivotTable |
| pie | pieChart |
| donut | donutChart |
| gauge | gauge |

---

## Query role assignments

### cardVisual
- `Data` → measures[0] (main KPI)
- `ReferenceLabels` → measures[1] (comparison, optional)
- `AdditionalMeasure` → measures[2] (YoY%, optional)

### clusteredColumnChart / clusteredBarChart / lineChart
- `Category` → dimensions (columns)
- `Y` → measures

### tableEx
- `Values` → all columns + all measures (each as a separate projection in same array)

### slicer
- `Values` → dimensions[0] (the column to filter by)

### pivotTable (matrix)
- `Rows` → dimensions
- `Values` → measures

---

## Z-order convention

| Visual type | Z range |
|---|---|
| Slicers | 500–599 |
| KPI cards | 1000–1099 |
| Charts and tables | 2000–2099 |

tabOrder: sequential from 0, left-to-right, top-to-bottom reading order.

---

## Standard layout grid (1280×720 canvas)

### 4 KPI cards at top
| # | x | y | width | height |
|---|---|---|---|---|
| 1 | 30 | 80 | 280 | 130 |
| 2 | 330 | 80 | 280 | 130 |
| 3 | 630 | 80 | 280 | 130 |
| 4 | 930 | 80 | 280 | 130 |

### 2×2 chart grid (below KPIs)
| # | x | y | width | height |
|---|---|---|---|---|
| Top-left | 30 | 230 | 600 | 230 |
| Top-right | 650 | 230 | 600 | 230 |
| Bottom-left | 30 | 480 | 600 | 230 |
| Bottom-right | 650 | 480 | 600 | 230 |

### Full-width chart (below KPIs)
| Element | x | y | width | height |
|---|---|---|---|---|
| Chart | 30 | 230 | 1220 | 480 |

---

## IBCS colors (use consistently)
- Actual: `#0C3549`
- Comparison: `#CCCCCC`
- Positive: `#44C088`
- Negative: `#ED7373`

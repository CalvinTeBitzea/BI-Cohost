# Worked Example — Incidents Trend with MoM Growth Rate

## Token Substitutions

| Token | Value used |
|---|---|
| `<MEASURE_TABLE>` | `_Measures` |
| `<MEASURE_TABLE_LINEAGE_TAG>` | `82b3a42d-fec9-4c43-bd95-92526dd6ea82` |
| `<MEASURE_TABLE_PBI_ID>` | `617eebb3a74c4bd2ab080a2ca81c0bcc` |
| `<MEASURE_TABLE_ANNOTATION_KEY>` | `436ba87b-9c83-4389-a31b-ebd06a36be98` |
| `<MEASURE_TABLE_COLUMN_LINEAGE_TAG>` | `3de5d470-f5f7-4dd4-9008-ed6df41b669e` |
| `<VOLUME_MEASURE_NAME>` | `_Incident Count` |
| `<VOLUME_MEASURE_DAX>` | `COUNTROWS('PBI vFactIncidentsManualHandling')` |
| `<VOLUME_MEASURE_LINEAGE_TAG>` | `80b10bb3-0efb-4a78-a4f1-5a2f30124f66` |
| `<VOLUME_MEASURE_NATIVE_REF>` | `_Incident Count1` |
| `<GROWTH_MEASURE_NAME>` | `MoM Growth Rate %` |
| `<GROWTH_MEASURE_DAX>` | (see multi-line expansion in Artifact 1 below) |
| `<GROWTH_MEASURE_LINEAGE_TAG>` | `4589adc3-b639-49e4-90f3-772c8579e529` |
| `<GROWTH_MEASURE_NATIVE_REF>` | `MoM Growth Rate %1` |
| `<DATE_TABLE>` | `CSL vDimDate` |
| `<DATE_AXIS_COLUMN>` | `MonthYearLabel` |
| `<PRIMARY_Y_AXIS_END>` | `70D` |
| `<SECONDARY_Y_AXIS_START>` | `-5D` |
| `<SECONDARY_Y_AXIS_END>` | `2D` |
| `<CATEGORY_MAX_MARGIN>` | `40L` |
| `<DATA_POINT_ENTITY>` | `PBI vFactIncidentsManualHandling` |
| `<DATA_POINT_CATEGORY_COLUMN>` | `(Manual Handling) Category` |
| `<DATA_POINT_CATEGORY_VALUE>` | `Patient / Client / Resident` |
| `<DATA_POINT_COLOR_ID>` | `9` |
| `<CHART_TITLE>` | `Incidents Trend` |
| `<VISUAL_NAME>` | `0c2aefda03bead008b21` |
| `<CHART_X>` | `95.204056991064959` |
| `<CHART_Y>` | `118.69596715769137` |
| `<CHART_Z>` | `0` |
| `<CHART_HEIGHT>` | `260.26563631972954` |
| `<CHART_WIDTH>` | `1004.5882637044192` |
| `<CHART_TAB_ORDER>` | `0` |

---

## Artifact 1 — `SemanticModel/definition/tables/_Measures.tmdl`

```tmdl
table _Measures
	lineageTag: 82b3a42d-fec9-4c43-bd95-92526dd6ea82

	measure '_Incident Count' = COUNTROWS('PBI vFactIncidentsManualHandling')
		lineageTag: 80b10bb3-0efb-4a78-a4f1-5a2f30124f66

	measure 'MoM Growth Rate %' =
			
			
			VAR _LM = [_Incident Count - Last Month]
			VAR _Current = [Incident Count (up to month end)]
			VAR _PctChange = DIVIDE(_Current - _LM, _LM)
			
			
			RETURN
			//FORMAT(_LM, "0,0") & " | " & FORMAT(_PctChange, "0.0%")
			_PctChange
		lineageTag: 4589adc3-b639-49e4-90f3-772c8579e529

	column Column
		formatString: 0
		lineageTag: 3de5d470-f5f7-4dd4-9008-ed6df41b669e
		summarizeBy: sum
		isNameInferred
		sourceColumn: [Column]

		annotation SummarizationSetBy = Automatic

	partition _Measures = calculated
		mode: import
		source = Row("Column", BLANK())

	annotation PBI_Id = 617eebb3a74c4bd2ab080a2ca81c0bcc

	annotation 436ba87b-9c83-4389-a31b-ebd06a36be98 = {"Expression":""}
```

---

## Artifact 2 — Fragment inserted into `SemanticModel/definition/model.tmdl`

Insert immediately before the existing `ref cultureInfo en-US` line:

```tmdl
ref table _Measures
```

Resulting `model.tmdl`:

```tmdl
model Model
	culture: en-US
	defaultPowerBIDataSourceVersion: powerBI_V3
	sourceQueryCulture: en-AU
	dataAccessOptions
		legacyRedirects
		returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 1

annotation PBI_ProTooling = ["DevMode"]

ref table _Measures

ref cultureInfo en-US
```

---

## Artifact 3 — `Report/definition/pages/<PAGE_ID>/visuals/0c2aefda03bead008b21/visual.json`

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json",
  "name": "0c2aefda03bead008b21",
  "position": {
    "x": 95.204056991064959,
    "y": 118.69596715769137,
    "z": 0,
    "height": 260.26563631972954,
    "width": 1004.5882637044192,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "lineStackedColumnComboChart",
    "query": {
      "queryState": {
        "Category": {
          "projections": [
            {
              "field": {
                "Column": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "CSL vDimDate"
                    }
                  },
                  "Property": "MonthYearLabel"
                }
              },
              "queryRef": "CSL vDimDate.MonthYearLabel",
              "nativeQueryRef": "MonthYearLabel",
              "active": true
            }
          ]
        },
        "Y": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "_Measures"
                    }
                  },
                  "Property": "_Incident Count"
                }
              },
              "queryRef": "_Measures._Incident Count",
              "nativeQueryRef": "_Incident Count1"
            }
          ]
        },
        "Y2": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "_Measures"
                    }
                  },
                  "Property": "MoM Growth Rate %"
                }
              },
              "queryRef": "_Measures.MoM Growth Rate %",
              "nativeQueryRef": "MoM Growth Rate %1"
            }
          ]
        }
      }
    },
    "objects": {
      "legend": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "showTitle": { "expr": { "Literal": { "Value": "false" } } },
            "fontSize": { "expr": { "Literal": { "Value": "9D" } } },
            "italic": { "expr": { "Literal": { "Value": "true" } } }
          }
        }
      ],
      "categoryAxis": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "maxMarginFactor": { "expr": { "Literal": { "Value": "40L" } } },
            "showAxisTitle": { "expr": { "Literal": { "Value": "false" } } },
            "labelColor": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 1, "Percent": 0.4 } } }
              }
            },
            "fontSize": { "expr": { "Literal": { "Value": "10D" } } }
          }
        }
      ],
      "valueAxis": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "showAxisTitle": { "expr": { "Literal": { "Value": "false" } } },
            "labelColor": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 0, "Percent": 0 } } }
              }
            },
            "secShow": { "expr": { "Literal": { "Value": "false" } } },
            "secLabelColor": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 0, "Percent": 0 } } }
              }
            },
            "secStart": { "expr": { "Literal": { "Value": "-5D" } } },
            "end": { "expr": { "Literal": { "Value": "70D" } } },
            "secEnd": { "expr": { "Literal": { "Value": "2D" } } }
          }
        }
      ],
      "dataPoint": [
        {
          "properties": {
            "fill": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 9, "Percent": 0 } } }
              }
            }
          },
          "selector": {
            "data": [
              {
                "scopeId": {
                  "Comparison": {
                    "ComparisonKind": 0,
                    "Left": {
                      "Column": {
                        "Expression": {
                          "SourceRef": { "Entity": "PBI vFactIncidentsManualHandling" }
                        },
                        "Property": "(Manual Handling) Category"
                      }
                    },
                    "Right": {
                      "Literal": { "Value": "'Patient / Client / Resident'" }
                    }
                  }
                }
              }
            ]
          }
        }
      ],
      "labels": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "detailFontSize": { "expr": { "Literal": { "Value": "10D" } } },
            "detailLabelPrecision": { "expr": { "Literal": { "Value": "1L" } } },
            "enableBackground": { "expr": { "Literal": { "Value": "false" } } }
          }
        },
        {
          "properties": {
            "labelPosition": { "expr": { "Literal": { "Value": "'Above'" } } }
          },
          "selector": { "metadata": "_Measures.MoM Growth Rate %" }
        }
      ],
      "lineStyles": [
        {
          "properties": {
            "showMarker": { "expr": { "Literal": { "Value": "true" } } }
          }
        }
      ]
    },
    "visualContainerObjects": {
      "title": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "titleWrap": { "expr": { "Literal": { "Value": "true" } } },
            "fontColor": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 1, "Percent": 0.4 } } }
              }
            },
            "background": {
              "solid": {
                "color": { "expr": { "Literal": { "Value": "null" } } }
              }
            },
            "fontSize": { "expr": { "Literal": { "Value": "12D" } } },
            "fontFamily": { "expr": { "Literal": { "Value": "'Arial'" } } },
            "text": { "expr": { "Literal": { "Value": "'Incidents Trend'" } } }
          }
        }
      ],
      "background": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "color": {
              "solid": {
                "color": { "expr": { "Literal": { "Value": "'#FFFFFF'" } } }
              }
            },
            "transparency": { "expr": { "Literal": { "Value": "100D" } } }
          }
        }
      ],
      "padding": [
        {
          "properties": {
            "top": { "expr": { "Literal": { "Value": "5D" } } },
            "bottom": { "expr": { "Literal": { "Value": "0D" } } }
          }
        }
      ],
      "border": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "color": {
              "solid": {
                "color": { "expr": { "Literal": { "Value": "'#E6E6E6'" } } }
              }
            },
            "radius": { "expr": { "Literal": { "Value": "10D" } } },
            "width": { "expr": { "Literal": { "Value": "1D" } } }
          }
        }
      ]
    },
    "drillFilterOtherVisuals": true
  }
}
```

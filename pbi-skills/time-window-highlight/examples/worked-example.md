# Worked Example — Sales Report with Monthly Window Highlight

## Token Substitutions

| Token | Value used |
|---|---|
| `<SLICER_TABLE_NAME>` | `dimDate Slicer` |
| `<SOURCE_DATE_TABLE>` | `dimDate` |
| `<SOURCE_DATE_COLUMN>` | `Date` |
| `<DATE_AXIS_COLUMN>` | `EOmonth` |
| `<MEASURE_TABLE>` | `_Measures` |
| `<VALUE_MEASURE>` | `Sales` |
| `<WINDOW_START_MEASURE>` | `Window Start Date` |
| `<WINDOW_END_MEASURE>` | `Window End Date` |
| `<WINDOW_CALC_NAME>` | `Data Labels Window` |
| `<CHART_TITLE>` | `Sales` |
| `<DEFAULT_START_DATE>` | `datetime'2025-08-30T01:00:00'` |
| `<DEFAULT_END_DATE>` | `datetime'2026-06-27T01:00:00'` |
| `<FILTER_START_DATE>` | `datetime'2025-08-30T00:00:00'` |
| `<FILTER_END_DATE>` | `datetime'2026-06-28T00:00:00'` |
| `<SLICER_TABLE_LINEAGE_TAG>` | `4043821c-b0f7-4c37-8bc5-b40d2aadee9a` |
| `<SLICER_COLUMN_LINEAGE_TAG>` | `0a04fbc5-36e8-4e1b-8e16-0174dfd1bdbe` |
| `<SLICER_TABLE_PBI_ID>` | `1ce96267a7de4a62afe0bcb32964a8f9` |
| `<WINDOW_START_LINEAGE_TAG>` | `78e9a5f8-ead6-4eac-9465-dbf4a20b1323` |
| `<WINDOW_END_LINEAGE_TAG>` | `15a27af7-0669-4a4d-95ed-97e2d18a50ab` |
| `<VISUAL_NAME_SLICER>` | `b3734404e96bdca0e3d2` |
| `<VISUAL_NAME_LINE_CHART>` | `c1c97d02ce9912d08174` |
| `<FILTER_NAME_SLICER>` | `98ddb8015097c5696056` |
| `<FILTER_NAME_SALES>` | `1800a24cb77220311b60` |
| `<FILTER_NAME_DATE>` | `e70a12013c10005427d5` |
| `<SLICER_X>` / `<SLICER_Y>` / `<SLICER_Z>` / `<SLICER_HEIGHT>` / `<SLICER_WIDTH>` / `<SLICER_TAB_ORDER>` | `1277.7777777777778` / `240` / `1` / `87.777777777777771` / `261.11111111111109` / `1` |
| `<CHART_X>` / `<CHART_Y>` / `<CHART_Z>` / `<CHART_HEIGHT>` / `<CHART_WIDTH>` / `<CHART_TAB_ORDER>` | `878.88888888888891` / `218.88888888888889` / `0` / `430` / `712.22222222222217` / `0` |

---

## Artifact 1 — `SemanticModel/definition/tables/dimDate Slicer.tmdl`

```tmdl
table 'dimDate Slicer'
	lineageTag: 4043821c-b0f7-4c37-8bc5-b40d2aadee9a

	column Date
		formatString: Short Date
		lineageTag: 0a04fbc5-36e8-4e1b-8e16-0174dfd1bdbe
		summarizeBy: none
		isNameInferred
		sourceColumn: dimDate[Date]

		annotation SummarizationSetBy = Automatic

	partition 'dimDate Slicer' = calculated
		mode: import
		source = ```

				VALUES( dimDate[Date] )

				```

	annotation PBI_Id = 1ce96267a7de4a62afe0bcb32964a8f9
```

---

## Artifact 2 — Fragment appended to `SemanticModel/definition/tables/_Measures.tmdl`

Insert the two blocks below immediately before the existing `partition _Measures = m` line:

```tmdl
	measure 'Window Start Date' = MIN('dimDate Slicer'[Date])
		formatString: General Date
		lineageTag: 78e9a5f8-ead6-4eac-9465-dbf4a20b1323

	measure 'Window End Date' = MAX( 'dimDate Slicer'[Date])
		formatString: General Date
		lineageTag: 15a27af7-0669-4a4d-95ed-97e2d18a50ab
```

---

## Artifact 3 — Fragment appended to `SemanticModel/definition/model.tmdl`

Add after the last existing `ref table` line:

```tmdl
ref table 'dimDate Slicer'
```

---

## Artifact 4 — `Report/definition/pages/2904eb2c583866b57ec8/visuals/b3734404e96bdca0e3d2/visual.json`

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.8.0/schema.json",
  "name": "b3734404e96bdca0e3d2",
  "position": {
    "x": 1277.7777777777778,
    "y": 240,
    "z": 1,
    "height": 87.777777777777771,
    "width": 261.11111111111109,
    "tabOrder": 1
  },
  "visual": {
    "visualType": "slicer",
    "query": {
      "queryState": {
        "Values": {
          "projections": [
            {
              "field": {
                "Column": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "dimDate Slicer"
                    }
                  },
                  "Property": "Date"
                }
              },
              "queryRef": "dimDate Slicer.Date",
              "nativeQueryRef": "Date",
              "active": true
            }
          ]
        }
      },
      "sortDefinition": {
        "sort": [
          {
            "field": {
              "Column": {
                "Expression": {
                  "SourceRef": {
                    "Entity": "dimDate Slicer"
                  }
                },
                "Property": "Date"
              }
            },
            "direction": "Ascending"
          }
        ],
        "isDefaultSort": true
      }
    },
    "objects": {
      "data": [
        {
          "properties": {
            "startDate": {
              "expr": {
                "Literal": {
                  "Value": "datetime'2025-08-30T01:00:00'"
                }
              }
            },
            "endDate": {
              "expr": {
                "Literal": {
                  "Value": "datetime'2026-06-27T01:00:00'"
                }
              }
            },
            "mode": {
              "expr": {
                "Literal": {
                  "Value": "'Between'"
                }
              }
            }
          }
        }
      ],
      "general": [
        {
          "properties": {
            "filter": {
              "filter": {
                "Version": 2,
                "From": [
                  {
                    "Name": "d",
                    "Entity": "dimDate Slicer",
                    "Type": 0
                  }
                ],
                "Where": [
                  {
                    "Condition": {
                      "And": {
                        "Left": {
                          "Comparison": {
                            "ComparisonKind": 2,
                            "Left": {
                              "Column": {
                                "Expression": {
                                  "SourceRef": {
                                    "Source": "d"
                                  }
                                },
                                "Property": "Date"
                              }
                            },
                            "Right": {
                              "Literal": {
                                "Value": "datetime'2025-08-30T00:00:00'"
                              }
                            }
                          }
                        },
                        "Right": {
                          "Comparison": {
                            "ComparisonKind": 3,
                            "Left": {
                              "Column": {
                                "Expression": {
                                  "SourceRef": {
                                    "Source": "d"
                                  }
                                },
                                "Property": "Date"
                              }
                            },
                            "Right": {
                              "Literal": {
                                "Value": "datetime'2026-06-28T00:00:00'"
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                ]
              }
            },
            "responsive": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ],
      "header": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ],
      "date": [
        {
          "properties": {
            "textSize": {
              "expr": {
                "Literal": {
                  "Value": "9D"
                }
              }
            }
          }
        }
      ]
    },
    "visualContainerObjects": {
      "title": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ],
      "visualHeader": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ]
    },
    "drillFilterOtherVisuals": true
  },
  "filterConfig": {
    "filters": [
      {
        "name": "98ddb8015097c5696056",
        "field": {
          "Column": {
            "Expression": {
              "SourceRef": {
                "Entity": "dimDate Slicer"
              }
            },
            "Property": "Date"
          }
        },
        "type": "Categorical"
      }
    ]
  }
}
```

---

## Artifact 5 — `Report/definition/pages/2904eb2c583866b57ec8/visuals/c1c97d02ce9912d08174/visual.json`

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.8.0/schema.json",
  "name": "c1c97d02ce9912d08174",
  "position": {
    "x": 878.88888888888891,
    "y": 218.88888888888889,
    "z": 0,
    "height": 430,
    "width": 712.22222222222217,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "lineChart",
    "query": {
      "queryState": {
        "Category": {
          "projections": [
            {
              "field": {
                "Column": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "dimDate"
                    }
                  },
                  "Property": "EOmonth"
                }
              },
              "queryRef": "dimDate.EOmonth",
              "nativeQueryRef": "EOmonth",
              "active": true
            }
          ]
        },
        "Tooltips": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "_Measures"
                    }
                  },
                  "Property": "Window Start Date"
                }
              },
              "queryRef": "_Measures.Window Start Date",
              "nativeQueryRef": "Window Start Date"
            },
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "_Measures"
                    }
                  },
                  "Property": "Window End Date"
                }
              },
              "queryRef": "_Measures.Window End Date",
              "nativeQueryRef": "Window End Date"
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
                  "Property": "Sales"
                }
              },
              "queryRef": "_Measures.Sales",
              "nativeQueryRef": "Sales"
            },
            {
              "field": {
                "NativeVisualCalculation": {
                  "Language": "dax",
                  "Expression": "\r\nIF (\r\n    [EOmonth] >= [Window Start Date]\r\n        && [EOmonth] <= [Window End Date],\r\n    [Sales]\r\n)",
                  "Name": "Data Labels Window"
                }
              },
              "queryRef": "select",
              "nativeQueryRef": "Data Labels Window"
            }
          ]
        }
      },
      "sortDefinition": {
        "sort": [
          {
            "field": {
              "Column": {
                "Expression": {
                  "SourceRef": {
                    "Entity": "dimDate"
                  }
                },
                "Property": "EOmonth"
              }
            },
            "direction": "Ascending"
          }
        ],
        "isDefaultSort": true
      }
    },
    "objects": {
      "valueAxis": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ],
      "xAxisReferenceLine": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "displayName": { "expr": { "Literal": { "Value": "'window end'" } } },
            "value": {
              "expr": {
                "Aggregation": {
                  "Expression": {
                    "Column": {
                      "Expression": { "SourceRef": { "Entity": "dimDate Slicer" } },
                      "Property": "Date"
                    }
                  },
                  "Function": 4
                }
              }
            },
            "shadeShow": { "expr": { "Literal": { "Value": "true" } } },
            "shadeRegion": { "expr": { "Literal": { "Value": "'before'" } } },
            "position": { "expr": { "Literal": { "Value": "'back'" } } },
            "shadeTransparency": { "expr": { "Literal": { "Value": "85D" } } },
            "width": { "expr": { "Literal": { "Value": "1D" } } }
          },
          "selector": { "id": "1" }
        },
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "displayName": { "expr": { "Literal": { "Value": "'window start'" } } },
            "value": {
              "expr": {
                "Aggregation": {
                  "Expression": {
                    "Column": {
                      "Expression": { "SourceRef": { "Entity": "dimDate Slicer" } },
                      "Property": "Date"
                    }
                  },
                  "Function": 3
                }
              }
            },
            "shadeShow": { "expr": { "Literal": { "Value": "true" } } },
            "shadeRegion": { "expr": { "Literal": { "Value": "'before'" } } },
            "position": { "expr": { "Literal": { "Value": "'back'" } } },
            "shadeColor": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 0, "Percent": 0 } } }
              }
            },
            "shadeTransparency": { "expr": { "Literal": { "Value": "0D" } } },
            "width": { "expr": { "Literal": { "Value": "1D" } } }
          },
          "selector": { "id": "2" }
        }
      ],
      "lineStyles": [
        {
          "properties": {
            "strokeShow": { "expr": { "Literal": { "Value": "false" } } },
            "markerColor": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 2, "Percent": 0.2 } } }
              }
            },
            "markerSize": { "expr": { "Literal": { "Value": "4D" } } }
          },
          "selector": { "metadata": "select" }
        },
        {
          "properties": {
            "showMarker": { "expr": { "Literal": { "Value": "true" } } },
            "markerSize": { "expr": { "Literal": { "Value": "3D" } } }
          }
        },
        {
          "properties": {
            "showMarker": { "expr": { "Literal": { "Value": "false" } } }
          },
          "selector": { "metadata": "_Measures.Sales" }
        }
      ],
      "labels": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "color": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 2, "Percent": 0.2 } } }
              }
            },
            "fontSize": { "expr": { "Literal": { "Value": "8D" } } }
          }
        },
        {
          "properties": {
            "showSeries": { "expr": { "Literal": { "Value": "false" } } }
          },
          "selector": { "metadata": "_Measures.Sales" }
        }
      ],
      "categoryAxis": [
        {
          "properties": {
            "fontSize": { "expr": { "Literal": { "Value": "10D" } } }
          }
        }
      ],
      "legend": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "false" } } }
          }
        }
      ]
    },
    "visualContainerObjects": {
      "subTitle": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "text": { "expr": { "Literal": { "Value": "' '" } } }
          }
        }
      ],
      "divider": [
        {
          "properties": {
            "show": { "expr": { "Literal": { "Value": "true" } } },
            "color": {
              "solid": {
                "color": { "expr": { "ThemeDataColor": { "ColorId": 0, "Percent": -0.1 } } }
              }
            },
            "ignorePadding": { "expr": { "Literal": { "Value": "false" } } }
          }
        }
      ],
      "spacing": [
        {
          "properties": {
            "spaceBelowTitle": { "expr": { "Literal": { "Value": "0D" } } },
            "spaceBelowTitleArea": { "expr": { "Literal": { "Value": "0D" } } },
            "spaceBelowSubTitle": { "expr": { "Literal": { "Value": "0D" } } }
          }
        }
      ],
      "padding": [
        {
          "properties": {
            "top": { "expr": { "Literal": { "Value": "20D" } } },
            "bottom": { "expr": { "Literal": { "Value": "20D" } } },
            "right": { "expr": { "Literal": { "Value": "20D" } } },
            "left": { "expr": { "Literal": { "Value": "20D" } } }
          }
        }
      ],
      "title": [
        {
          "properties": {
            "text": { "expr": { "Literal": { "Value": "'Sales'" } } }
          }
        }
      ]
    },
    "drillFilterOtherVisuals": true
  },
  "filterConfig": {
    "filters": [
      {
        "name": "1800a24cb77220311b60",
        "field": {
          "Measure": {
            "Expression": { "SourceRef": { "Entity": "_Measures" } },
            "Property": "Sales"
          }
        },
        "type": "Advanced"
      },
      {
        "name": "e70a12013c10005427d5",
        "field": {
          "Column": {
            "Expression": { "SourceRef": { "Entity": "dimDate" } },
            "Property": "EOmonth"
          }
        },
        "type": "Categorical"
      }
    ]
  }
}
```

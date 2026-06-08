# PBIR Schema Version — Pinned Reference

**Last verified:** 2026-06-08

## Schema base URLs

All schemas live at:
`https://developer.microsoft.com/json-schemas/fabric/item/report/definition/`

| File | Schema path | Version used |
|---|---|---|
| visual.json | `visualContainer/{version}/schema.json` | 2.0.0 (baseline) |
| page.json | `page/{version}/schema.json` | 2.0.0 (baseline) |
| pages.json | `pagesMetadata/{version}/schema.json` | 1.0.0 |
| report.json | `report/{version}/schema.json` | 1.0.0 |
| version.json | `versionMetadata/{version}/schema.json` | 1.0.0 |

GitHub source: https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition

## Version detection rule

**NEVER hardcode a schema version.** Desktop versions in the wild use `2.6.0`, `2.7.0`, or
later. Always read an existing `visual.json` from the target project and use its `$schema`
URL. Fall back to `2.0.0` only if the project has no existing visuals.

```python
def detect_schema_version(pages_dir):
    for page in pages_dir.iterdir():
        visuals_dir = page / "visuals"
        if visuals_dir.exists():
            for v in visuals_dir.iterdir():
                f = v / "visual.json"
                if f.exists():
                    j = json.loads(f.read_text())
                    if "$schema" in j:
                        return j["$schema"]
    return "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.0.0/schema.json"
```

## PBIR status

- January 2026: PBIR default in Fabric/Service workspaces with Git integration
- March 2026: PBIR default for all new reports in Power BI Desktop
- GA planned Q3 2026 (still preview during transition)
- When GA: PBIR becomes the only supported format

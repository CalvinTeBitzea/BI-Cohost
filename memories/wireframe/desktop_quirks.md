# Power BI Desktop Quirks

## Critical rules

1. **Desktop must be CLOSED when writing files.** If Desktop has the project open,
   writes will be ignored or cause conflicts. Close Desktop, write files, then reopen.

2. **Invalid JSON = blocking error.** A single missing comma or bracket prevents Desktop
   from loading the page. Always run Gate 1 (JSON parse check) before opening.

3. **Name field must match folder name exactly.** For both pages and visuals.
   e.g. folder `v01KpiRevenue/` → `visual.json → name: "v01KpiRevenue"`.

4. **Entity and Property names are case-sensitive.** Must match the semantic model exactly.
   Read TMDL files to confirm exact names before referencing them.

5. **Never create a PBIP from scratch.** Desktop generates `.platform` files with real UUIDs
   and version-specific theme refs in `report.json`. These cannot be reliably hand-crafted.

6. **Semantic model entry point is `definition.pbism`** (a JSON file), NOT `definition.tmdl`.
   TMDL files live inside the `definition/` subfolder.

7. **Schema version changes between Desktop updates.** Always detect from existing visuals.
   Mismatched schema version → non-blocking error or unexpected behavior.

## Setup for Gate 2 (open test)

- Platform: Windows VM / Parallels on Mac
- Require: PBIR preview feature enabled in Desktop
  (File → Options → Preview features → "Store reports using enhanced metadata format (PBIR)")
- Open: the `.pbip` file (not the .Report folder)
- After writing new files: close and reopen Desktop — it does NOT hot-reload

## Version tracking

| Date | Desktop version | Schema version detected |
|---|---|---|
| 2026-06-08 | TBD (first open test pending) | — |

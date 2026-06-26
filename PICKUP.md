# Pick up here (on the Power BI machine)

**State (2026-06-26):** the builder half is complete, proven offline, and **deployed as a live
web API** at `https://bi-cohost.vercel.app/api/build`. The BI-Workflow agent app is also live
at `https://claude-agent-chat-silk.vercel.app`. The two halves are now wired together via a
"Build PBIP ↓" button in the agent app's Output Files panel.

**Your task on this machine:** run Gate 2 — open the generated PBIP in Power BI Desktop and
confirm pages render. You do not need to touch any code.

---

## The full workflow (end-to-end test)

### Step 1 — Prepare a stub dataset in Power BI Desktop

You need a Desktop report connected to a dataset whose **table and column names match the
`semantic_model.json`** you're building against. Real data is not required — a stub dataset
with the right schema and zero or a few dummy rows is enough for Gate 2.

For the **retail example** (`examples/retail/semantic_model.json`), the tables are:
`Fact_Sales`, `Dim_Product`, `Dim_Category`, `Dim_Customer`, `Dim_Date`.
Create an Excel file (or CSV set) with those sheet/file names and at least the column headers
that appear in `semantic_model.json`. Connect it in Desktop as a local data source.

Then:
1. Desktop → **Options → Preview features → enable "Store reports using enhanced metadata
   format (PBIR)"** (required once per machine).
2. Connect the stub dataset → **File → Save as → Power BI Project (.pbip)**.
3. Note the path to the `.Report` folder, e.g. `C:\Reports\MyReport.Report`.
4. **Close Desktop** before the next step.

### Step 2 — Generate the pages via the web app (recommended path)

1. Open `https://claude-agent-chat-silk.vercel.app` in your browser.
2. Paste your schema and brief → run the agent → wait for it to finish.
3. Click **Fetch** in the sidebar → Output Files panel shows
   `dashboard_spec.json`, `semantic_model.json`, `wireframe.html`.
4. Click **Build PBIP ↓** → `pages_XXXX.zip` downloads automatically.
5. Extract the zip. You'll get folders like `pg01.../`, `pg02.../` and a `pages.json`.
6. Copy all extracted contents into `MyReport.Report\definition\pages\`
   (clear any existing content in that folder first).
7. Reopen `MyReport.pbip` in Desktop → new pages appear.

### Step 2 (alternative) — Use the CLI directly

If you prefer to skip the web app and test with the known-good retail example:

```powershell
.\setup.ps1                         # first time only
.\run.ps1 `
  --wireframe-spec examples\retail\dashboard_spec.json `
  --semantic-model examples\retail\semantic_model.json `
  --build-id retail_demo `
  --pbip-path "C:\path\to\MyReport.Report"
```

Reopen `MyReport.pbip` → pages appear.

### Step 3 — Validate (Gate 2 checklist)

- [ ] Pages exist in Desktop (correct count, correct names)
- [ ] Visuals are positioned at the wireframe layout (check against `wireframe.html`)
- [ ] Field bindings resolve — no "Can't load visual" if the stub data columns match
- [ ] Pareto combo chart (if present) renders with both bar and line series
- [ ] Walk `pbi-skills/line-column-combo-chart/SKILL.md` → Validation section
- [ ] Walk `pbi-skills/time-window-highlight/SKILL.md` → Validation section (skill warns
      about missing TMDL objects — this is expected; see Open work #1 below)

---

## Architecture recap

```
[BI-Workflow agent app]  ←→  claude-agent-chat-silk.vercel.app
        │ emits
        ▼
dashboard_spec.json + semantic_model.json
        │
        ▼  "Build PBIP ↓" button  (or CLI: run.ps1 --pbip-path)
        │
[bi-cohost API]  ←→  bi-cohost.vercel.app/api/build
        │ returns pages zip
        ▼
MyReport.Report/definition/pages/   ←  extract zip here
        │
        ▼
Power BI Desktop  (open MyReport.pbip)
```

**What the web API does NOT generate:** the `.platform`, `report.json`, `version.json`, and
`.SemanticModel` files — Desktop owns those. That's why you need the existing `.Report` folder
as the injection target. The API returns only the `pages/` content.

---

## What this repo is

bi-cohost is the **builder half** of the BI-Workflow pipeline. The contract between the two
halves is **`docs/AGENT_CONTRACT.md`** (read this for field-name conventions).
A complete, buildable example is in **`examples/retail/`**.

## Open work (in priority order)

1. **Skill → semantic-model merge.** A skill emits its report visual but its TMDL fragment
   (new measures table / disconnected slicer table) is **not** applied — it just warns
   (`_skill_needs_model_objects` in `agents/pbip_builder.py`). Needed for
   `time-window-highlight`. Plan: token-fill + merge the skill's `.tmdl` into the project's
   SemanticModel, deduped against existing objects.
2. **More skills.** Only two exist (`line-column-combo-chart`, `time-window-highlight`). Add
   skills for donut, scatter, ranked-table, KPI card. New skills drop into `pbi-skills/` and
   are referenceable by name with no builder change.
3. **More golden pages.** `examples/retail/` encodes pages 1–2; pages 3–4 follow the same
   pattern if you want a fuller regression fixture.

## Map of the code

| Path | Role |
|---|---|
| `app.py` | Vercel Flask entry point — `POST /api/build` |
| `docs/AGENT_CONTRACT.md` | agent↔builder interface + visual-type→skill vocabulary |
| `agents/ingest.py` | validate the two JSONs + snap geometry |
| `agents/pbip_builder.py` | IR → PBIR (skill token-fill + fallback), Gates 1 & 3 |
| `agents/conductor.py` | CLI: ingest → build (used by `run.ps1`) |
| `lib/artifact_store.py` | file I/O; respects `ARTIFACT_ROOT` env var |
| `lib/layout.py` | snap engine: `grid` band-intent → pixel `layout` |
| `lib/skills.py` | skill registry + token-fill |
| `schemas/` | `dashboard_spec.json` + `semantic_model.json` JSON schemas |
| `pbi-skills/` | skill templates (SKILL.md + visual.json + tmdl) |
| `examples/retail/` | golden reference — buildable end-to-end |

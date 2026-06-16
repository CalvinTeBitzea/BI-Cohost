# Pick up here (on the Power BI machine)

**State:** the *builder half* is complete and proven offline. What this machine couldn't do
is open the output in **Power BI Desktop** and bind it to **real datasets** — that's the
next step, and the reason for this note.

## What this repo is

bi-cohost is the **builder half** of the BI-Workflow pipeline. The *front half* — requirements
+ wireframe — is a separate app (`active/claude-agent-chat`, the "BI-Workflow" agent;
outputs in `active/claude-agent-outputs/`). That agent co-emits three things:

```
wireframe.html        (human sign-off view)
dashboard_spec.json   (the IR — what to build)        ┐
semantic_model.json   (measures+DAX, dimensions, rels)┘─▶ bi-cohost: ingest → pbip_builder → PBIP
```

The contract between the two halves is **`docs/AGENT_CONTRACT.md`** (read this first).
A complete, buildable example is in **`examples/retail/`** (the real retail wireframe + brief
encoded as the two JSON files).

## 1. Set up

```bash
cd bi-cohost
python -m venv .venv && . .venv/Scripts/activate     # Windows; or source .venv/bin/activate
pip install -r requirements.txt
# .env only needed if you later use the LLM-backed TMDL generator (see "Open work")
```

## 2. Confirm it still works (no Desktop, no API key)

```bash
python -m pytest tests/ -q            # expect: 21 passed
python agents/conductor.py \
  --wireframe-spec examples/retail/dashboard_spec.json \
  --semantic-model examples/retail/semantic_model.json \
  --build-id retail_demo              # expect: Gate 1 PASS, Gate 3 PASS
```
Output PBIR lands in `artifacts/retail_demo/report.pbir/` (gitignored).

## 3. THE NEXT STEP — open in Power BI Desktop + real data

The scaffold from step 2 is correct but **not directly openable**. To see it render:

1. Power BI Desktop → Options → Preview features → enable **Power BI Project (.pbip)**.
2. Create a blank report, connect your **real dataset** (the retail star schema, or any model
   whose measure/dimension names match the `semantic_model.json` you build against),
   **Save as `.pbip`** → gives you a `MyReport.Report` folder.
3. Inject the generated pages into it:
   ```bash
   python agents/conductor.py \
     --wireframe-spec examples/retail/dashboard_spec.json \
     --semantic-model examples/retail/semantic_model.json \
     --build-id retail_demo \
     --pbip-path "C:\path\to\MyReport.Report"
   ```
4. Reopen the `.pbip`. Pages appear at the wireframe positions; visuals light up once the field
   names resolve against the connected model. (`setup.ps1` / `run.ps1` are Windows helpers.)

This is the real validation gate (the builder's "Gate 2 — opens in Desktop"). Walk the
`pbi-skills/*/SKILL.md` **Validation** checklists for the skilled visuals (the Pareto combo).

## Open work (in priority order)

1. **Skill → semantic-model merge (the one known caveat).** Today a skill emits its *report
   visual* but its TMDL fragment (new measures table / disconnected slicer table) is **not**
   applied — it just warns (`_skill_needs_model_objects` in `agents/pbip_builder.py`). Needed
   for skills like `time-window-highlight`. Plan: token-fill + merge the skill's `.tmdl` into the
   project's SemanticModel, deduped against existing objects.
2. **From-scratch semantic model.** `_generate_tmdl` (LLM) exists in `pbip_builder.py` but isn't
   wired into the run path — today we assume the model already exists in the target `.Report`.
   Decide: generate `model.tmdl` from `semantic_model.json`, or always inject into an existing model.
3. **More skills.** Only two exist (`line-column-combo-chart`, `time-window-highlight`). Add skills
   for donut, scatter, ranked-table, KPI card to upgrade those from the fallback to rich PBIR.
   New skills drop into `pbi-skills/` and are referenceable by name with no code change.
4. **More golden pages.** `examples/retail/` encodes pages 1–2; pages 3–4 follow the same pattern
   if you want a fuller regression fixture.

## Map of the code

| Path | Role |
|---|---|
| `docs/AGENT_CONTRACT.md` | the agent↔builder interface + visual-type→skill vocabulary |
| `agents/ingest.py` | validate the two JSONs + snap geometry |
| `agents/pbip_builder.py` | IR → PBIR (skill token-fill + fallback), Gates 1 & 3 |
| `agents/conductor.py` | CLI: ingest → build |
| `lib/layout.py` | snap engine: `grid` band-intent → pixel `layout` |
| `lib/skills.py` | skill registry + token-fill |
| `lib/mdutil.py` | markdown parsing (skills, brief) |
| `schemas/` | `dashboard_spec.json` (IR) + `semantic_model.json` contracts |
| `examples/retail/` | golden reference (buildable) |
| `templates/executive-sales-overview/` | **parked** — an archetype concept from before the pivot; not in the build path (may move to the agent side) |

Note: `lib/wireframe_html.py`, `lib/review_server.py`, `lib/templates.py`,
`agents/dashboard_spec.py` were **retired** in the pivot — the wireframe/review UX lives in the
BI-Workflow app, and the wireframe (not a template) is the authoritative design.

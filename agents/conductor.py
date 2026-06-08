"""
Pipeline conductor — runs all 4 stages in order with checkpointing.

Usage:
  python agents/conductor.py \\
    --brief "Sales dashboard showing revenue by product and region" \\
    --build-id my-build-001 \\
    [--columns '[{"name":"revenue","type":"decimal"},...]']
    [--columns-file columns.json]
    [--pbip-path /path/to/MyReport.Report]   # existing PBIP .Report folder
    [--force]   # re-run all stages even if already done
"""
import json
import sys
import time
from pathlib import Path

import click
from dotenv import load_dotenv

# Ensure project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env from project root (works on Windows where env vars aren't pre-set)
load_dotenv(Path(__file__).parent.parent / ".env")

import agents.requirements as req_agent
import agents.semantic_model as sem_agent
import agents.dashboard_spec as dash_agent
import agents.pbip_builder as pbip_agent
from lib.artifact_store import is_stage_done


def _step(label: str, build_id: str, stage: str, force: bool, fn):
    if not force and is_stage_done(build_id, stage):
        print(f"  ✓ {label} (cached)")
        return
    print(f"  → {label}...")
    t0 = time.time()
    fn()
    elapsed = time.time() - t0
    print(f"  ✓ {label} ({elapsed:.1f}s)")


@click.command()
@click.option("--brief", required=True, help="Freetext business brief for the dashboard")
@click.option("--build-id", required=True, help="Unique identifier for this build")
@click.option("--columns", default=None, help="JSON array of column definitions inline")
@click.option("--columns-file", default=None, type=click.Path(exists=True), help="Path to a JSON file with column definitions")
@click.option("--pbip-path", default=None, type=click.Path(), help="Path to existing .Report folder; agent adds pages into it instead of writing a scaffold")
@click.option("--force", is_flag=True, default=False, help="Re-run all stages even if already completed")
def main(brief: str, build_id: str, columns: str | None, columns_file: str | None, pbip_path: str | None, force: bool):
    """bi-cohost MVP pipeline: brief → .pbip file"""

    # Resolve columns
    cols: list[dict] = []
    if columns:
        cols = json.loads(columns)
    elif columns_file:
        cols = json.loads(Path(columns_file).read_text())

    print(f"\nbi-cohost build: {build_id}")
    print("=" * 50)

    _step(
        "Stage 1: Requirements",
        build_id, "requirements", force,
        lambda: req_agent.run(build_id, brief, cols),
    )

    _step(
        "Stage 2: Semantic Model",
        build_id, "semantic_model", force,
        lambda: sem_agent.run(build_id),
    )

    _step(
        "Stage 3: Dashboard Spec",
        build_id, "dashboard_spec", force,
        lambda: dash_agent.run(build_id),
    )

    pbip_result: dict = {}

    def _run_pbip():
        nonlocal pbip_result
        pbip_result = pbip_agent.run(build_id, pbip_report_path=pbip_path)

    _step(
        "Stage 4: PBIP Builder",
        build_id, "pbip_builder", force,
        _run_pbip,
    )

    print("=" * 50)
    print(f"Done. Artifacts: active/bi-cohost/artifacts/{build_id}/")
    if pbip_result:
        target = pbip_path or pbip_result.get("output_dir", "")
        print(f"  Output: {target}")
        g1 = "PASS" if pbip_result.get("gate1_passed") else "FAIL"
        g3 = "PASS" if pbip_result.get("gate3_passed") else "FAIL"
        print(f"  Gate 1 (JSON valid): {g1}")
        print(f"  Gate 3 (IR fidelity): {g3}")
        if not pbip_result.get("gate1_passed"):
            for err in pbip_result.get("gate1_errors", []):
                print(f"    ✗ {err}")
        if not pbip_result.get("gate3_passed"):
            for err in pbip_result.get("gate3_errors", []):
                print(f"    ✗ {err}")
    if pbip_path:
        print(f"\nReopen the .pbip file in Power BI Desktop to see new pages.")
    else:
        print(f"\nOpen the generated .pbip folder in Power BI Desktop to validate.")


if __name__ == "__main__":
    main()

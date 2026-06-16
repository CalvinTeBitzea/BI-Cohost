"""
Conductor — builder half of the BI-Workflow pipeline.

The wireframing agent (BI-Workflow) produces the design: a human wireframe.html plus
two structured artifacts. This conductor takes those artifacts and builds the PBIP:

    wireframe spec (IR) + semantic model  ──ingest──▶  validate + snap geometry
                                          ──build───▶  PBIR pages + visuals (skills)

Usage:
  python agents/conductor.py \\
    --wireframe-spec  path/to/dashboard_spec.json \\
    --semantic-model  path/to/semantic_model.json \\
    --build-id my-build-001 \\
    [--pbip-path /path/to/MyReport.Report]   # existing PBIP .Report folder
    [--force]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import click

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import agents.ingest as ingest_agent
import agents.pbip_builder as pbip_agent
from lib.artifact_store import is_stage_done


def _step(label: str, build_id: str, stage: str, force: bool, fn):
    if not force and is_stage_done(build_id, stage):
        print(f"  ✓ {label} (cached)")
        return
    print(f"  → {label}...")
    t0 = time.time()
    fn()
    print(f"  ✓ {label} ({time.time() - t0:.1f}s)")


@click.command()
@click.option("--wireframe-spec", required=True, type=click.Path(exists=True),
              help="dashboard_spec.json (IR) co-emitted by the wireframing agent")
@click.option("--semantic-model", required=True, type=click.Path(exists=True),
              help="semantic_model.json co-emitted by the wireframing agent")
@click.option("--build-id", required=True, help="Unique identifier for this build")
@click.option("--pbip-path", default=None, type=click.Path(),
              help="Path to an existing .Report folder; pages are added into it")
@click.option("--force", is_flag=True, default=False, help="Re-run all stages")
def main(wireframe_spec, semantic_model, build_id, pbip_path, force):
    """bi-cohost builder: wireframe spec + semantic model → .pbip"""
    print(f"\nbi-cohost build: {build_id}")
    print("=" * 50)

    _step("Stage 1: Ingest", build_id, "ingest", force,
          lambda: ingest_agent.run(build_id, wireframe_spec, semantic_model))

    result = {}

    def _build():
        nonlocal result
        result = pbip_agent.run(build_id, pbip_report_path=pbip_path)

    _step("Stage 2: PBIP Builder", build_id, "pbip_builder", force, _build)

    print("=" * 50)
    if result:
        g1 = "PASS" if result.get("gate1", {}).get("passed") else "FAIL"
        g3 = "PASS" if result.get("gate3", {}).get("passed") else "FAIL"
        print(f"  Gate 1 (JSON valid): {g1}")
        print(f"  Gate 3 (IR fidelity): {g3}")
        print(f"  Output: {pbip_path or result.get('output_dir', '')}")
    if pbip_path:
        print("\n  Reopen the .pbip in Power BI Desktop to see the new pages.")


if __name__ == "__main__":
    main()

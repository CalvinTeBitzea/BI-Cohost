import json
from pathlib import Path

_BASE = Path(__file__).parent.parent / "artifacts"


def artifact_path(build_id: str, filename: str) -> Path:
    return _BASE / build_id / filename


def write_artifact(build_id: str, filename: str, data: dict) -> Path:
    path = artifact_path(build_id, filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))
    return path


def read_artifact(build_id: str, filename: str) -> dict:
    return json.loads(artifact_path(build_id, filename).read_text())


def artifact_exists(build_id: str, filename: str) -> bool:
    return artifact_path(build_id, filename).exists()


def mark_stage_done(build_id: str, stage: str) -> None:
    path = artifact_path(build_id, f".{stage}.done")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()


def is_stage_done(build_id: str, stage: str) -> bool:
    return artifact_path(build_id, f".{stage}.done").exists()

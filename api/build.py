"""
Vercel Python serverless handler — POST /api/build

Accepts dashboard_spec + semantic_model as JSON, runs the bi-cohost builder
pipeline, and returns a zip of the generated PBIR pages directory.

The caller (claude-agent-chat "Build PBIP" button) extracts the zip into an
existing .Report/definition/pages/ folder created by Power BI Desktop.
"""
import io
import json
import os
import shutil
import sys
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler
from pathlib import Path

# Must set ARTIFACT_ROOT before importing modules that read it at module level.
sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("ARTIFACT_ROOT", "/tmp/bi-cohost-builds")

import agents.ingest as ingest_agent       # noqa: E402
import agents.pbip_builder as pbip_agent   # noqa: E402
from lib.artifact_store import artifact_path  # noqa: E402


def _cors(h: "handler") -> None:
    h.send_header("Access-Control-Allow-Origin", "*")
    h.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    h.send_header("Access-Control-Allow-Headers", "Content-Type")


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self.send_response(200)
        _cors(self)
        self.end_headers()

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))

            spec     = body["dashboard_spec"]
            model    = body["semantic_model"]
            build_id = body.get("build_id") or uuid.uuid4().hex[:8]

            # ingest.run accepts dicts directly (no temp files needed)
            ingest_agent.run(build_id, spec, model)
            pbip_agent.run(build_id)

            pages_dir = artifact_path(build_id, "report.pbir") / "definition" / "pages"

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f in sorted(pages_dir.rglob("*")):
                    if f.is_file():
                        zf.write(f, f.relative_to(pages_dir))
            zip_bytes = buf.getvalue()

            # Clean up this build's artifacts from /tmp
            shutil.rmtree(pages_dir.parent.parent.parent, ignore_errors=True)

            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="pages_{build_id}.zip"',
            )
            self.send_header("Content-Length", str(len(zip_bytes)))
            _cors(self)
            self.end_headers()
            self.wfile.write(zip_bytes)

        except Exception as exc:
            error = json.dumps({"error": str(exc)}).encode()
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(error)))
            _cors(self)
            self.end_headers()
            self.wfile.write(error)

    def log_message(self, *args) -> None:
        pass

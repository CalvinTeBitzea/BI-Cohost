"""
Flask entry point for Vercel deployment — POST /api/build
"""
import io
import json
import os
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("ARTIFACT_ROOT", "/tmp/bi-cohost-builds")

from flask import Flask, jsonify, request, send_file

import agents.ingest as ingest_agent
import agents.pbip_builder as pbip_agent
from lib.artifact_store import artifact_path

app = Flask(__name__)


def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/build", methods=["OPTIONS"])
def build_preflight():
    return _cors(app.response_class("", 200))


@app.route("/api/build", methods=["POST"])
def build():
    try:
        body     = request.get_json(force=True)
        spec     = body["dashboard_spec"]
        model    = body["semantic_model"]
        build_id = body.get("build_id") or uuid.uuid4().hex[:8]

        ingest_agent.run(build_id, spec, model)
        result = pbip_agent.run(build_id)

        pages_dir = artifact_path(build_id, "report.pbir") / "definition" / "pages"

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # pages/ content → extract into .Report/definition/pages/
            for f in sorted(pages_dir.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(pages_dir))
            # tmdl/ content → copy each file to .SemanticModel/definition/tables/
            for fname, tmdl_text in result.get("tmdl_fragments", []):
                zf.writestr(f"tmdl/{fname}", tmdl_text)
        zip_bytes = buf.getvalue()

        shutil.rmtree(pages_dir.parent.parent.parent, ignore_errors=True)

        response = send_file(
            io.BytesIO(zip_bytes),
            mimetype="application/zip",
            as_attachment=True,
            download_name=f"pages_{build_id}.zip",
        )
        return _cors(response)

    except Exception as exc:
        response = jsonify({"error": str(exc)})
        response.status_code = 500
        return _cors(response)

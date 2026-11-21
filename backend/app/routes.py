import json
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint, abort, current_app, jsonify, request, send_from_directory

from . import detect
from .db import get_db
from .engines import analyze_all
from .validators import clean_inputs, merge_inputs, validate_upload

api = Blueprint("api", __name__)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def fail(message, code=400, **extra):
    return jsonify({"error": message, **extra}), code


def get_project(pid):
    row = get_db().execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    if row is None:
        abort(404, description="Project not found.")
    return row


def plan_row(pid):
    return get_db().execute("SELECT * FROM plans WHERE project_id=?", (pid,)).fetchone()


def plan_of(pid):
    r = plan_row(pid)
    if r is None:
        return None
    state = detect.state_of(r["reading_status"], detect.load_reading(r["reading"]))
    return {"name": r["original_name"], "ext": r["ext"], "size": r["size"], "uploaded_at": r["uploaded_at"],
            "reading": state}


def project_json(row):
    return {"id": row["id"], "name": row["name"], "created_at": row["created_at"], "plan": plan_of(row["id"])}


def inputs_of(pid):
    r = get_db().execute("SELECT data FROM inputs WHERE project_id=?", (pid,)).fetchone()
    return json.loads(r["data"]) if r else {}


def model_json(pid):
    """Everything the analyzer pages show. Values read from the drawing fill in whatever the user has not typed."""
    inputs = inputs_of(pid)
    row = plan_row(pid)
    reading = detect.load_reading(row["reading"]) if row else None
    effective, src, notes = detect.effective_inputs(inputs, reading)
    reading_state = detect.state_of(row["reading_status"] if row else None, reading)
    ctx = {
        "src": src,
        "notes": notes,
        "facts": detect.facts_of(reading),
        "found": detect.found_rooms(reading),
        "reading": reading,
        "reading_state": reading_state,
        "has_plan": row is not None,
    }
    return {
        "inputs": inputs,
        "effective": effective,
        "sources": src,
        "reading": detect.summary(reading, row["reading_status"] if row else None),
        "analysis": analyze_all(effective, row is not None, ctx),
    }


@api.get("/health")
def health():
    return jsonify({"status": "ok"})


@api.get("/projects")
def list_projects():
    rows = get_db().execute("SELECT * FROM projects ORDER BY created_at DESC, rowid DESC").fetchall()
    return jsonify({"projects": [project_json(r) for r in rows]})


@api.post("/projects")
def create_project():
    name = str((request.get_json(silent=True) or {}).get("name", "")).strip()
    if not 1 <= len(name) <= 60:
        return fail("Project name must be 1 to 60 characters.")
    pid = uuid.uuid4().hex[:12]
    db = get_db()
    db.execute("INSERT INTO projects (id, name, created_at) VALUES (?,?,?)", (pid, name, now()))
    db.commit()
    return jsonify(project_json(get_project(pid))), 201


@api.get("/projects/<pid>")
def read_project(pid):
    return jsonify(project_json(get_project(pid)))


def remove_plan_file(pid):
    r = get_db().execute("SELECT stored_name FROM plans WHERE project_id=?", (pid,)).fetchone()
    if r:
        try:
            os.remove(os.path.join(current_app.config["UPLOAD_DIR"], r["stored_name"]))
        except FileNotFoundError:
            pass


@api.delete("/projects/<pid>")
def delete_project(pid):
    get_project(pid)
    remove_plan_file(pid)
    db = get_db()
    db.execute("DELETE FROM projects WHERE id=?", (pid,))
    db.commit()
    return "", 204


@api.post("/projects/<pid>/plan")
def upload_plan(pid):
    get_project(pid)
    f = request.files.get("file")
    if f is None or not f.filename:
        return fail("Choose a plan file to upload.")
    ext, problem = validate_upload(f.filename, f.stream.read(2048))
    if problem:
        return fail(problem, 415)
    f.stream.seek(0)
    remove_plan_file(pid)
    stored = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(current_app.config["UPLOAD_DIR"], stored)
    f.save(path)
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO plans (project_id, original_name, stored_name, ext, size, uploaded_at, reading, reading_status)"
        " VALUES (?,?,?,?,?,?,NULL,'pending')",
        (pid, os.path.basename(f.filename)[:120], stored, ext, os.path.getsize(path), now()),
    )
    db.commit()
    detect.start_reading(current_app._get_current_object(), pid, stored, path, ext)
    return jsonify(project_json(get_project(pid))), 201


@api.post("/projects/<pid>/plan/read")
def reread_plan(pid):
    """Read the uploaded drawing again (also used for plans uploaded before the reader existed)."""
    get_project(pid)
    r = plan_row(pid)
    if r is None:
        return fail("Upload a plan first.", 404)
    if r["reading_status"] != "pending":
        db = get_db()
        db.execute("UPDATE plans SET reading=NULL, reading_status='pending' WHERE project_id=?", (pid,))
        db.commit()
        path = os.path.join(current_app.config["UPLOAD_DIR"], r["stored_name"])
        detect.start_reading(current_app._get_current_object(), pid, r["stored_name"], path, r["ext"])
    return jsonify(project_json(get_project(pid))), 202


@api.get("/projects/<pid>/plan/file")
def plan_file(pid):
    get_project(pid)
    r = get_db().execute("SELECT stored_name FROM plans WHERE project_id=?", (pid,)).fetchone()
    if r is None:
        abort(404, description="No plan uploaded.")
    return send_from_directory(current_app.config["UPLOAD_DIR"], r["stored_name"])


@api.delete("/projects/<pid>/plan")
def delete_plan(pid):
    get_project(pid)
    remove_plan_file(pid)
    db = get_db()
    db.execute("DELETE FROM plans WHERE project_id=?", (pid,))
    db.commit()
    return "", 204


@api.get("/projects/<pid>/model")
def read_model(pid):
    get_project(pid)
    return jsonify(model_json(pid))


@api.put("/projects/<pid>/inputs")
def save_inputs(pid):
    get_project(pid)
    patch = request.get_json(silent=True)
    if not isinstance(patch, dict):
        return fail("Send a JSON object of fields to update.")
    merged = merge_inputs(inputs_of(pid), patch)
    clean, errors = clean_inputs(merged)
    if errors:
        return fail("Some inputs are not valid.", 400, fields=errors)
    db = get_db()
    db.execute(
        "INSERT OR REPLACE INTO inputs (project_id, data, updated_at) VALUES (?,?,?)",
        (pid, json.dumps(clean), now()),
    )
    db.commit()
    return jsonify(model_json(pid))


from . import assistant  # noqa: E402,F401  (registers /assistant on the blueprint)

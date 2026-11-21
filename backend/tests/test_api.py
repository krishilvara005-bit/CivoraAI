import os

from conftest import PNG, upload


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_project_lifecycle(client):
    assert client.post("/api/projects", json={"name": "  "}).status_code == 400
    p = client.post("/api/projects", json={"name": "Villa"}).get_json()
    assert client.get("/api/projects").get_json()["projects"][0]["name"] == "Villa"
    assert client.get(f"/api/projects/{p['id']}").status_code == 200
    assert client.delete(f"/api/projects/{p['id']}").status_code == 204
    assert client.get(f"/api/projects/{p['id']}").status_code == 404


def test_upload_and_fetch_plan(client, project):
    r = upload(client, project["id"])
    assert r.status_code == 201 and r.get_json()["plan"]["ext"] == "png"
    f = client.get(f"/api/projects/{project['id']}/plan/file")
    assert f.status_code == 200 and f.data == PNG
    assert f.headers["X-Content-Type-Options"] == "nosniff"


def test_upload_rejects_bad_type_and_fake_png(client, project):
    assert upload(client, project["id"], "x.exe", b"MZ").status_code == 415
    assert upload(client, project["id"], "x.png", b"not a png").status_code == 415


def test_replacing_plan_removes_old_file(client, project, app):
    upload(client, project["id"])
    upload(client, project["id"], "b.png")
    assert len(os.listdir(app.config["UPLOAD_DIR"])) == 1


def test_inputs_flow_into_analysis(client, project):
    pid = project["id"]
    r = client.put(f"/api/projects/{pid}/inputs", json={"floors": "G+1", "area": "1000", "rate": 2000, "range": 10})
    body = r.get_json()
    assert r.status_code == 200 and body["analysis"]["cost"]["total"] == 4_000_000
    r = client.put(f"/api/projects/{pid}/inputs", json={"rooms": {"Kitchen": "SE"}, "north": "top"})
    assert r.get_json()["analysis"]["vastu"]["matched"] == 1
    assert client.get(f"/api/projects/{pid}/model").get_json()["inputs"]["floors"] == "G+1"


def test_clearing_a_field(client, project):
    pid = project["id"]
    client.put(f"/api/projects/{pid}/inputs", json={"zone": "III"})
    r = client.put(f"/api/projects/{pid}/inputs", json={"zone": ""}).get_json()
    assert "zone" not in r["inputs"]


def test_invalid_inputs_are_rejected(client, project):
    r = client.put(f"/api/projects/{project['id']}/inputs", json={"zone": "IX", "area": -5, "bogus": 1})
    assert r.status_code == 400 and set(r.get_json()["fields"]) == {"zone", "area", "bogus"}


def test_assistant_without_key(client):
    assert client.post("/api/assistant", json={"messages": [{"role": "user", "content": "hi"}]}).status_code == 503


def test_assistant_with_stub(app, client, monkeypatch):
    from app import assistant
    app.config["GEMINI_API_KEY"] = "test"
    monkeypatch.setattr(assistant, "call_model", lambda msgs, system=None: "Namaste")
    r = client.post("/api/assistant", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.get_json() == {"reply": "Namaste"}
    assert client.post("/api/assistant", json={"messages": []}).status_code == 400


READING = {
    "method": "ocr", "status": "read", "image": {"w": 660, "h": 440}, "floors": "G+1", "floor_labels": [],
    "panels": [{"floor": 0, "label": "GROUND FLOOR PLAN", "box": [0.0, 0.0, 0.48, 1.0]}],
    "rooms": [
        {"name": "Kitchen", "type": "kitchen", "floor": 0, "fx": 0.28, "fy": 0.15, "cell": 0, "size": None, "size_exact": None, "area": 85},
        {"name": "Bedroom", "type": "bedroom", "floor": 0, "fx": 0.3, "fy": 0.7, "cell": 6, "size": None, "size_exact": None, "area": 150},
        {"name": "Toilet", "type": "toilet", "floor": 0, "fx": 0.2, "fy": 0.4, "cell": 3, "size": None, "size_exact": None, "area": 30},
    ],
    "entrance": {"floor": 0, "fx": 0.9, "fy": 0.6, "cell": 5},
    "width_ft": 27.0, "depth_ft": 38.0, "area": 1026, "room_area": {}, "hints": {}, "warnings": [],
}


def read_with(monkeypatch, reading):
    from app import plan_reader
    monkeypatch.setattr(plan_reader, "read_plan", lambda *a, **k: reading)


def test_upload_fills_details_from_drawing(client, project, monkeypatch):
    read_with(monkeypatch, READING)
    r = upload(client, project["id"])
    assert r.status_code == 201
    m = client.get(f"/api/projects/{project['id']}/model").get_json()
    assert m["effective"]["floors"] == "G+1" and m["effective"]["area"] == 1026
    assert m["inputs"] == {}  # nothing was written as if the user typed it
    assert m["reading"]["state"] == "done" and m["reading"]["status"] == "read"
    cost = {i["key"]: i for i in m["analysis"]["cost"]["items"]}
    assert cost["built"]["display"] == "2,052 sq ft" and cost["floors"]["source"] == "drawing"
    assert cost["rate"]["status"] == "not_provided"  # a rate is never assumed
    st = {i["key"]: i for i in m["analysis"]["structure"]["items"]}
    assert st["size"]["display"].startswith("27' x 38'")


def test_user_values_beat_drawing_values(client, project, monkeypatch):
    read_with(monkeypatch, READING)
    upload(client, project["id"])
    m = client.put(f"/api/projects/{project['id']}/inputs", json={"area": 900}).get_json()
    assert m["effective"]["area"] == 900 and m["sources"]["fields"]["area"] == "you"
    assert m["sources"]["fields"]["floors"] == "drawing"
    m = client.put(f"/api/projects/{project['id']}/inputs", json={"area": ""}).get_json()
    assert m["effective"]["area"] == 1026  # cleared -> back to the drawing's value


def test_vastu_zones_need_confirmed_north(client, project, monkeypatch):
    read_with(monkeypatch, READING)
    upload(client, project["id"])
    pid = project["id"]
    m = client.get(f"/api/projects/{pid}/model").get_json()
    assert m["effective"].get("rooms") is None  # north is never assumed
    v = m["analysis"]["vastu"]
    assert v["awaiting_north"] is True
    assert {r["room"]: r["verdict"] for r in v["rows"]}["Kitchen"] == "found_needs_north"
    m = client.put(f"/api/projects/{pid}/inputs", json={"north": "top"}).get_json()
    assert m["effective"]["rooms"]["Kitchen"] == "NW"            # top-left cell, north up
    assert m["effective"]["rooms"]["Main entrance"] == "E"       # middle-right cell
    assert m["effective"]["rooms"]["Master bedroom"] == "SW"
    rows = {r["room"]: r for r in m["analysis"]["vastu"]["rows"]}
    assert rows["Kitchen"]["verdict"] == "acceptable" and rows["Kitchen"]["source"] == "drawing"
    m = client.put(f"/api/projects/{pid}/inputs", json={"north": "right"}).get_json()
    assert m["effective"]["rooms"]["Kitchen"] == "SW"            # north on the right: top is west, left is south
    m = client.put(f"/api/projects/{pid}/inputs", json={"rooms": {"Kitchen": "SE"}}).get_json()
    assert m["effective"]["rooms"]["Kitchen"] == "SE" and m["sources"]["rooms"]["Kitchen"] == "you"


def test_unreadable_drawing_keeps_everything_not_provided(client, project):
    upload(client, project["id"])  # fake PNG bytes: the reader cannot decode it
    m = client.get(f"/api/projects/{project['id']}/model").get_json()
    assert m["reading"]["state"] == "done" and m["reading"]["status"] in ("unreadable", "unavailable")
    assert m["effective"] == {} and m["reading"]["warnings"]


def test_reread_endpoint(client, project, monkeypatch):
    assert client.post(f"/api/projects/{project['id']}/plan/read").status_code == 404
    upload(client, project["id"])
    read_with(monkeypatch, READING)
    r = client.post(f"/api/projects/{project['id']}/plan/read")
    assert r.status_code == 202 and r.get_json()["plan"]["reading"] == "done"


def test_old_database_is_migrated(tmp_path):
    import sqlite3
    from app import create_app
    path = str(tmp_path / "old.db")
    c = sqlite3.connect(path)
    c.executescript("CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL);"
                    "CREATE TABLE plans (project_id TEXT PRIMARY KEY, original_name TEXT NOT NULL, stored_name TEXT NOT NULL,"
                    " ext TEXT NOT NULL, size INTEGER NOT NULL, uploaded_at TEXT NOT NULL);"
                    "INSERT INTO projects VALUES ('aaaaaaaaaaaa','Old','2026-01-01');"
                    "INSERT INTO plans VALUES ('aaaaaaaaaaaa','a.jpg','x.jpg','jpg',1,'2026-01-01');")
    c.commit(); c.close()
    app = create_app({"DATABASE": path, "UPLOAD_DIR": str(tmp_path / "up"), "READ_ASYNC": False})
    r = app.test_client().get("/api/projects/aaaaaaaaaaaa")
    assert r.get_json()["plan"]["reading"] == "none"


def test_assistant_errors_are_specific(app, client, monkeypatch):
    from app import assistant
    app.config["GEMINI_API_KEY"] = "test"

    def boom(msgs, system=None):
        raise assistant.AssistantError("Mistri's API key was rejected.")
    monkeypatch.setattr(assistant, "call_model", boom)
    r = client.post("/api/assistant", json={"messages": [{"role": "user", "content": "hi"}]})
    assert r.status_code == 502 and "key was rejected" in r.get_json()["error"]


def test_assistant_gets_project_context(app, client, project, monkeypatch):
    from app import assistant
    app.config["GEMINI_API_KEY"] = "test"
    read_with(monkeypatch, READING)
    upload(client, project["id"])
    seen = {}
    monkeypatch.setattr(assistant, "call_model", lambda msgs, system=None: seen.setdefault("s", system) and "ok")
    client.post("/api/assistant", json={"messages": [{"role": "user", "content": "what is my area?"}],
                                        "project_id": project["id"], "page": "cost"})
    assert "Cost Estimation Analyzer" in seen["s"] and "1026" in seen["s"]

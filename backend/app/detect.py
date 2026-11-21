"""Turn what the drawing reader found into analyzer inputs.

Layers, lowest to highest priority:  drawing  <  what the user typed.
Nothing the user entered is ever overwritten, and nothing is guessed when the drawing does not say.
North is never taken from the drawing: Vastu zones are only worked out after the user confirms it.
"""
import json
import threading
from collections import Counter

from . import db, plan_reader
from .engines.vastu import COMPASS, NORTH_POS, RING

FLOOR_TITLES = ["Ground", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth"]
_gate = threading.Semaphore(1)  # OCR is CPU heavy: read one drawing at a time


# ---------------------------------------------------------------- reading storage

def load_reading(raw):
    try:
        return json.loads(raw) if raw else None
    except ValueError:
        return None


def state_of(status, reading):
    """none = never read, pending = in progress, done = finished (see reading['status'] for the outcome)."""
    if status == "pending":
        return "pending"
    return "done" if reading else "none"


def run_reading(database, pid, stored_name, path, ext, cfg):
    """Read the drawing and save the result. Safe to call from a background thread."""
    try:
        with _gate:
            result = plan_reader.read_plan(path, ext, cfg.get("key", ""), cfg.get("model", ""), cfg.get("mode", "ocr"))
    except Exception as e:  # read_plan never raises, but a thread must never die silently
        result = plan_reader._empty("unreadable", [f"The drawing could not be read ({type(e).__name__}). Enter the details manually."])
    conn = db.connect(database)
    try:
        # Only store it if this is still the plan on file (it may have been replaced meanwhile).
        conn.execute("UPDATE plans SET reading=?, reading_status='done' WHERE project_id=? AND stored_name=?",
                     (json.dumps(result), pid, stored_name))
        conn.commit()
    finally:
        conn.close()


def start_reading(app, pid, stored_name, path, ext):
    cfg = {"key": app.config["ANTHROPIC_API_KEY"], "model": app.config["ANTHROPIC_MODEL"], "mode": app.config["PLAN_READER"]}
    args = (app.config["DATABASE"], pid, stored_name, path, ext, cfg)
    if app.config["READ_ASYNC"]:
        threading.Thread(target=run_reading, args=args, daemon=True, name=f"read-{pid}").start()
    else:
        run_reading(*args)


# ---------------------------------------------------------------- what the drawing tells us

def _usable(reading):
    return bool(reading) and reading.get("status") in ("read", "partial")


def detected_fields(reading):
    """Analyzer inputs the drawing supports. Missing keys mean 'not read'."""
    if not _usable(reading):
        return {}
    out = {}
    if reading.get("floors"):
        out["floors"] = reading["floors"]
    if reading.get("area"):
        out["area"] = float(reading["area"])
    hints = reading.get("hints") or {}
    for k in ("zone", "grade"):
        if hints.get(k):
            out[k] = hints[k]
    return out


def zone_of(cell, north):
    """Compass zone of a 3x3 cell of the plan once north is known. None for the centre cell."""
    ring = RING[cell]
    return None if ring is None else COMPASS[(ring - NORTH_POS[north]) % 8]


def _ground(reading):
    rooms = reading.get("rooms") or []
    ground = [r for r in rooms if r.get("floor") in (0, None)]
    return ground or rooms


def detected_rooms(reading, north):
    """Zone of each Vastu room, from where it sits on the drawing. Returns (rooms, notes)."""
    if not _usable(reading) or north not in NORTH_POS:
        return {}, []
    notes, found = [], {}
    ground = _ground(reading)
    all_rooms = reading.get("rooms") or []

    def put(name, cell):
        z = zone_of(cell, north) if cell is not None else None
        if z:
            found[name] = z

    # 1. Entrance / Main Gate
    ent = reading.get("entrance")
    if ent:
        put("Main entrance", ent.get("cell"))
        put("Main Gate", ent.get("cell"))

    # 2. Kitchens (Main Kitchen & Alternative Kitchen)
    kitchens = [r for r in ground if r["type"] == "kitchen"] or [r for r in all_rooms if r["type"] == "kitchen"]
    if kitchens:
        put("Kitchen", kitchens[0]["cell"])
        put("Main Kitchen", kitchens[0]["cell"])
        if len(kitchens) > 1:
            put("Alternative Kitchen", kitchens[1]["cell"])

    # 3. Bedrooms (Master Bedroom, Children's Bedroom, Guest Bedroom)
    beds = [r for r in ground if r["type"] == "bedroom"] or [r for r in all_rooms if r["type"] == "bedroom"]
    if beds:
        named = [r for r in beds if "Master" in r.get("name", "")]
        sw_beds = [r for r in beds if r.get("cell") == 6]
        if named:
            pick = named[0]
        elif sw_beds:
            pick = sw_beds[0]
        else:
            pick = max(beds, key=lambda r: r.get("area") or 0)
        put("Master bedroom", pick["cell"])
        put("Master Bedroom", pick["cell"])
        if not named and not sw_beds:
            notes.append("Master bedroom was taken as the largest bedroom on the drawing. Change it if that is not right.")

        # Assign remaining bedrooms to Children's Bedroom and Guest Bedroom
        other_beds = [r for r in beds if r != pick]
        nw_beds = [r for r in other_beds if r.get("cell") in (0, 3)]
        if nw_beds:
            child_bed = nw_beds[0]
            other_beds = [r for r in other_beds if r != child_bed]
        elif other_beds:
            child_bed = other_beds[0]
            other_beds = other_beds[1:]
        else:
            child_bed = None

        if child_bed:
            put("Children's Bedroom", child_bed["cell"])
        if other_beds:
            put("Guest Bedroom", other_beds[0]["cell"])

    # 4. Toilets & Bathrooms
    toilets = [r for r in ground if r["type"] == "toilet"] or [r for r in all_rooms if r["type"] == "toilet"]
    if toilets:
        w_toilets = [r for r in toilets if r.get("cell") == 3]
        pick_toilet = w_toilets[0] if w_toilets else toilets[0]
        put("Toilet", pick_toilet["cell"])
        rem_toilets = [r for r in toilets if r != pick_toilet]
        if rem_toilets:
            put("Bathroom", rem_toilets[0]["cell"])
        else:
            put("Bathroom", pick_toilet["cell"])
        zones = [zone_of(r["cell"], north) for r in toilets if r.get("cell") is not None]
        zones = [z for z in zones if z]
        if len(set(zones)) > 1:
            notes.append("The drawing has toilets in more than one zone.")

    # 5. Living Room & Family Living Area
    livings = [r for r in ground if r["type"] == "living"] or [r for r in all_rooms if r["type"] == "living"]
    if livings:
        put("Living Room", livings[0]["cell"])
        put("Living room", livings[0]["cell"])
        if len(livings) > 1:
            put("Family Living Area", livings[1]["cell"])
        else:
            put("Family Living Area", livings[0]["cell"])

    # 6. Dining Room
    dinings = [r for r in ground if r["type"] == "dining"] or [r for r in all_rooms if r["type"] == "dining"]
    if dinings:
        put("Dining Room", dinings[0]["cell"])
        put("Dining", dinings[0]["cell"])

    # 7. Pooja Room
    poojas = [r for r in all_rooms if r["type"] == "pooja"]
    if poojas:
        put("Pooja room", poojas[0]["cell"])
        put("Pooja Room", poojas[0]["cell"])

    # 8. Staircase
    stairs = [r for r in all_rooms if r["type"] == "stair"]
    if stairs:
        put("Staircase", stairs[0]["cell"])

    # 9. Study Room & Home Office
    studies = [r for r in all_rooms if r["type"] in ("study", "office")]
    if studies:
        put("Study Room", studies[0]["cell"])
        put("Home Office", studies[-1]["cell"] if len(studies) > 1 else studies[0]["cell"])

    # 10. Parking & Garage
    parkings = [r for r in all_rooms if r["type"] == "parking"]
    if parkings:
        put("Parking", parkings[0]["cell"])
        put("Garage", parkings[0]["cell"])

    # 11. Balcony & Garden
    gardens = [r for r in all_rooms if r.get("type") in ("garden", "balcony")]
    if gardens:
        put("Garden", gardens[0]["cell"])

    # 12. Dressing Room
    dressings = [r for r in all_rooms if r.get("type") == "dressing"]
    if dressings:
        put("Dressing Room", dressings[0]["cell"])

    if "Main entrance" not in found:
        notes.append("No main door marker (MD) was found on the drawing, so choose the entrance zone yourself.")
    return found, notes


def found_rooms(reading):
    """Names of the Vastu rooms the drawing shows, whether or not north is known yet."""
    found, _ = detected_rooms(reading, "top")
    return sorted(found)


# ---------------------------------------------------------------- merge

def effective_inputs(inputs, reading):
    """(effective inputs, source of each field, extra notes). The user's own values always win."""
    drawn = detected_fields(reading)
    eff = {**drawn, **inputs}
    sources = {k: ("you" if k in inputs else "drawing") for k in eff if k != "rooms"}
    rooms_d, notes = detected_rooms(reading, eff.get("north"))
    mine = inputs.get("rooms") or {}
    rooms = {**rooms_d, **mine}
    room_src = {r: ("you" if r in mine else "drawing") for r in rooms}
    if rooms:
        eff["rooms"] = rooms
    return eff, {"fields": sources, "rooms": room_src}, notes


# ---------------------------------------------------------------- summaries for the UI and the engines

def _fmt_ft(v):
    return f"{v:g}'"


def facts_of(reading):
    if not _usable(reading):
        return {}
    facts = {}
    if reading.get("width_ft") and reading.get("depth_ft"):
        facts["size"] = f"{_fmt_ft(reading['width_ft'])} x {_fmt_ft(reading['depth_ft'])} per floor"
    by_floor = {}
    for r in reading.get("rooms") or []:
        by_floor.setdefault(r["floor"] if isinstance(r["floor"], int) else 0, []).append(r["name"])
    parts = []
    for fl in sorted(by_floor):
        counts = Counter(by_floor[fl])
        names = ", ".join(n if c == 1 else f"{n} x{c}" for n, c in counts.items())
        parts.append(f"{FLOOR_TITLES[fl] if fl < 10 else fl}: {names}")
    if parts:
        facts["rooms"] = "; ".join(parts)
    return facts


def summary(reading, status):
    """Small, UI-safe view of a reading."""
    state = state_of(status, reading)
    if not reading:
        return {"state": state, "status": None, "warnings": []}
    ground_box = next((p["box"] for p in reading.get("panels", []) if p.get("floor") in (0, None)), None)
    return {
        "state": state, "status": reading.get("status"), "method": reading.get("method"),
        "floors": reading.get("floors"), "floor_labels": reading.get("floor_labels") or [],
        "width_ft": reading.get("width_ft"), "depth_ft": reading.get("depth_ft"), "area": reading.get("area"),
        "rooms": [{"name": r["name"], "floor": r["floor"], "size": r.get("size")} for r in reading.get("rooms") or []],
        "entrance_found": bool(reading.get("entrance")),
        "image": reading.get("image"), "ground_box": ground_box,
        "hints": reading.get("hints") or {}, "warnings": reading.get("warnings") or [],
    }

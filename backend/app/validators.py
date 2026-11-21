import math
import re

from .engines.vastu import COMPASS, ROOM_RULES

ZONES = ("II", "III", "IV", "V")
SOILS = ("Rock", "Hard soil", "Medium soil", "Soft soil")
GRADES = ("M20", "M25", "M30", "M35")
FRAMINGS = ("RCC Frame", "Steel Frame", "Load Bearing")
RANGES = (10, 15, 20)
NORTHS = ("top", "right", "bottom", "left")
ALLOWED_EXT = {"jpg", "jpeg", "png", "pdf", "dxf", "dwg"}
FLOOR_RE = re.compile(r"^G(\+[0-9])?$")
KNOWN = {"floors", "area", "zone", "soil", "grade", "framing", "rate", "range", "north", "rooms"}


def _number(value, lo, hi):
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    return n if math.isfinite(n) and lo <= n <= hi else None


def merge_inputs(old, patch):
    """Apply a partial update. An empty value clears that field."""
    new = dict(old)
    for key, value in patch.items():
        if key == "rooms" and isinstance(value, dict):
            rooms = dict(new.get("rooms") or {})
            for room, zone in value.items():
                if zone in ("", None):
                    rooms.pop(room, None)
                else:
                    rooms[room] = zone
            new["rooms"] = rooms
        elif value in ("", None):
            new.pop(key, None)
        else:
            new[key] = value
    return new


def clean_inputs(raw):
    """Return (clean, errors). Unknown or invalid fields are reported, never silently kept."""
    clean, errors = {}, {}
    for key, value in raw.items():
        if key not in KNOWN:
            errors[key] = "Unknown field."
        elif key == "floors":
            if isinstance(value, str) and FLOOR_RE.match(value):
                clean[key] = value
            else:
                errors[key] = "Use G, G+1 ... G+9."
        elif key == "area":
            n = _number(value, 1, 100000)
            clean[key], errors[key] = (n, None) if n else (None, "Enter an area from 1 to 100000 sq ft.")
        elif key == "rate":
            n = _number(value, 1, 1000000)
            clean[key], errors[key] = (n, None) if n else (None, "Enter a rate from 1 to 1000000 per sq ft.")
        elif key == "range":
            n = _number(value, 0, 100)
            clean[key], errors[key] = (int(n), None) if n in RANGES else (None, "Use 10, 15 or 20.")
        elif key == "zone":
            clean[key], errors[key] = (value, None) if value in ZONES else (None, "Use II, III, IV or V.")
        elif key == "soil":
            clean[key], errors[key] = (value, None) if value in SOILS else (None, "Unknown soil type.")
        elif key == "grade":
            clean[key], errors[key] = (value, None) if value in GRADES else (None, "Use M20, M25, M30 or M35.")
        elif key == "framing":
            clean[key], errors[key] = (value, None) if value in FRAMINGS else (None, "Use RCC Frame, Steel Frame or Load Bearing.")
        elif key == "north":
            clean[key], errors[key] = (value, None) if value in NORTHS else (None, "Use top, right, bottom or left.")
        elif key == "rooms":
            ok = isinstance(value, dict) and all(r in ROOM_RULES and z in COMPASS for r, z in value.items())
            clean[key], errors[key] = (value, None) if ok else (None, "Unknown room or zone.")
    errors = {k: v for k, v in errors.items() if v}
    clean = {k: v for k, v in clean.items() if k not in errors and v is not None}
    return clean, errors


_MAGIC = {"png": b"\x89PNG\r\n\x1a\n", "jpg": b"\xff\xd8\xff", "jpeg": b"\xff\xd8\xff", "pdf": b"%PDF", "dwg": b"AC"}


def validate_upload(filename, head):
    """Check the extension and that the first bytes match the claimed type."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXT:
        return None, "Choose a JPG, PNG, PDF, DXF or DWG file."
    if ext == "dxf":
        ok = b"SECTION" in head
    else:
        ok = head.startswith(_MAGIC[ext])
    return (ext, None) if ok else (None, "The file contents do not match its type.")

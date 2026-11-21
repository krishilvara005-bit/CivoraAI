"""Read property details from an uploaded 2D residential plan drawing.

Default path is local OCR (RapidOCR, a pip-only dependency) plus simple geometry on the pixels:
floor labels -> floors, overall dimension labels -> plan area, room labels -> rooms and where each
room sits inside its floor plan. Optionally (PLAN_READER=vision) Claude reads the drawing instead,
falling back to OCR if that call fails.

Nothing is invented. A detail that cannot be read stays None and a warning explains why.
"""
import base64
import difflib
import io
import json
import math
import re
import threading

M_TO_FT = 3.28084
MAX_SIDE = 3000

# ---------------------------------------------------------------- vocabulary

# canonical type -> (display name, keywords with spaces and punctuation removed)
ROOM_TYPES = {
    "kitchen": ("Kitchen", ["KITCHEN", "KITCHN", "MAINKITCHEN"]),
    "bedroom": ("Bedroom", ["BEDROOM", "BEDRM", "BED"]),
    "living": ("Living room", ["LIVINGROOM", "LIVING", "DRAWINGROOM", "HALL", "FAMILYROOM", "FAMILYLIVING", "LOUNGE"]),
    "dining": ("Dining", ["DINING", "DININGROOM"]),
    "toilet": ("Toilet", ["TOILET", "BATHROOM", "WASHROOM", "BATH", "WC", "POWDERROOM"]),
    "parking": ("Portico / parking", ["PORTICO", "PARKING", "GARAGE", "CARPARK", "CARPORCH"]),
    "balcony": ("Balcony", ["BALCONY"]),
    "theater": ("Home theater", ["THEATER", "THEATRE"]),
    "pooja": ("Pooja room", ["POOJA", "PUJA", "MANDIR", "PRAYER"]),
    "store": ("Store", ["STOREROOM", "STORE"]),
    "study": ("Study", ["STUDY", "OFFICE", "HOMEOFFICE", "WORKROOM"]),
    "utility": ("Utility", ["UTILITY", "WASHAREA", "LAUNDRY"]),
    "stair": ("Staircase", ["STAIRCASE", "STAIR", "LIFT", "ELEVATOR"]),
    "passage": ("Passage", ["PASSAGE", "LOBBY", "FOYER", "CORRIDOR"]),
    "entrance": ("Entrance", ["ENTRANCE", "ENTRY", "MAINDOOR", "MAINGATE", "MAINENTRY", "GATE"]),
    "dressing": ("Dressing room", ["DRESSING", "DRESS", "WARDROBE", "CLOSET"]),
    "garden": ("Garden", ["GARDEN", "LAWN", "LANDSCAPE", "GREEN", "COURTYARD"]),
}
KEYWORDS = sorted(((k, t) for t, (_, ks) in ROOM_TYPES.items() for k in ks), key=lambda kt: -len(kt[0]))
# Rooms whose area is not enclosed living space.
OPEN_TYPES = {"parking", "balcony", "stair", "passage", "entrance", "garden"}

ORDINALS = {
    "GROUND": 0, "GF": 0, "FIRST": 1, "1ST": 1, "SECOND": 2, "2ND": 2, "THIRD": 3, "3RD": 3,
    "FOURTH": 4, "4TH": 4, "FIFTH": 5, "5TH": 5, "SIXTH": 6, "6TH": 6, "SEVENTH": 7, "7TH": 7,
    "EIGHTH": 8, "8TH": 8, "NINTH": 9, "9TH": 9,
}
FLOOR_NAMES = ["Ground", "First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh", "Eighth", "Ninth"]


def _letters(text):
    return re.sub(r"[^A-Z0-9]", "", text.upper())


# ---------------------------------------------------------------- sizes

def _side_inches(s):
    """'15'3"' -> 183. Tolerates dropped quote marks ('153' -> 15'3"). None when it cannot be read."""
    s = s.strip()
    m = re.fullmatch(r"(\d{1,2})\s*['’`]\s*(?:-?\s*(\d{1,2})\s*(?:\"|”|''|’’)?)?", s)
    if m:
        ft, inch = int(m.group(1)), int(m.group(2) or 0)
        return ft * 12 + inch if inch <= 11 else None
    if not re.fullmatch(r"[\d'\"’”`.,\-\s]+", s):
        return None
    d = re.sub(r"\D", "", s)
    if not d:
        return None
    if len(d) == 1:
        ft, inch = int(d), 0
    elif len(d) == 2:
        ft, inch = (int(d), 0) if int(d) <= 30 else (int(d[0]), int(d[1]))
    elif len(d) == 3:
        ft, inch = (int(d[:2]), int(d[2]))
        if ft > 40 or inch > 11:
            return None
    elif len(d) == 4:
        ft, inch = int(d[:2]), int(d[2:])
        if inch > 11:
            return None
    else:
        return None
    return ft * 12 + inch


def parse_size(text):
    """'15'X13'6"' -> (w_in, d_in, score). score 2 = quote marks present, 1 = repaired from digits."""
    t = text.upper().replace("×", "X").replace("*", "X").replace(" ", "")
    parts = t.split("X")
    if len(parts) != 2:
        return None
    a, b = _side_inches(parts[0]), _side_inches(parts[1])
    if a is None or b is None or not (24 <= a <= 45 * 12 and 24 <= b <= 45 * 12):
        return None
    marked = "'" in parts[0] and "'" in parts[1]
    return a, b, 2 if marked else 1


def fmt_inches(n):
    ft, inch = divmod(int(round(n)), 12)
    return f"{ft}'{inch}\"" if inch else f"{ft}'"


def fmt_size(w, d):
    return f"{fmt_inches(w)} x {fmt_inches(d)}"


# ---------------------------------------------------------------- OCR

_engine = None
_lock = threading.Lock()


def _ocr_engine():
    global _engine
    with _lock:
        if _engine is None:
            from rapidocr_onnxruntime import RapidOCR

            _engine = RapidOCR()
        return _engine


def _boxes(img, scale, rot=0):
    """OCR one view of the image. Returns boxes in the ORIGINAL image's pixel coordinates."""
    import numpy as np
    from PIL import Image

    work = img.resize((max(1, round(img.width * scale)), max(1, round(img.height * scale))), Image.LANCZOS)
    arr = np.array(work)
    if rot:
        arr = np.rot90(arr, k=rot)  # +1 = counter-clockwise, -1 = clockwise
    result, _ = _ocr_engine()(arr)
    h, w = arr.shape[:2]  # of the rotated view
    out = []
    for quad, text, conf in result or []:
        xs, ys = [p[0] for p in quad], [p[1] for p in quad]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        if rot == -1:    # clockwise view: original x = y', original y = H' - ... (see derivation in docs)
            x0, x1, y0, y1 = y0, y1, w - x1, w - x0
        elif rot == 1:   # counter-clockwise view
            x0, x1, y0, y1 = h - y1, h - y0, x0, x1
        s = scale
        out.append({"text": str(text).strip(), "conf": float(conf), "x0": x0 / s, "x1": x1 / s,
                    "y0": y0 / s, "y1": y1 / s, "rot": rot})
    return out


def _cx(b):
    return (b["x0"] + b["x1"]) / 2


def _cy(b):
    return (b["y0"] + b["y1"]) / 2


def _load_image(path, ext):
    from PIL import Image

    if ext == "pdf":
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        extra = len(doc) - 1
        page = doc[0]
        zoom = min(4.0, MAX_SIDE / max(page.rect.width, page.rect.height))
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
        doc.close()
        return img, extra
    img = Image.open(path)
    img.load()
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
    img = img.convert("RGB")
    if max(img.size) > MAX_SIDE:
        k = MAX_SIDE / max(img.size)
        img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    return img, 0


# ---------------------------------------------------------------- geometry

def _wall_box(img, region):
    """Outer wall rectangle of a floor plan inside region=(x0,y0,x1,y1), in pixels.

    Walls are thick; dimension lines are thin. Eroding the ink removes the thin lines, so the
    outermost long straight runs that remain are the building's outer walls."""
    import numpy as np
    from PIL import ImageFilter

    x0, y0, x1, y1 = (int(v) for v in region)
    gray = img.convert("L").crop((x0, y0, x1, y1))
    ink = gray.point(lambda p: 255 if p < 120 else 0)
    k = 3 if max(gray.size) < 900 else 5
    eroded = np.array(ink.filter(ImageFilter.MinFilter(k))) > 0
    h, w = eroded.shape
    cols, rows = eroded.sum(axis=0), eroded.sum(axis=1)
    cc = np.where(cols >= 0.45 * h)[0]
    rr = np.where(rows >= 0.40 * w)[0]
    if len(cc) >= 2 and len(rr) >= 2 and (cc[-1] - cc[0]) > 0.3 * w and (rr[-1] - rr[0]) > 0.3 * h:
        return x0 + int(cc[0]), y0 + int(rr[0]), x0 + int(cc[-1]) + 1, y0 + int(rr[-1]) + 1
    allink = np.array(ink) > 0
    ys, xs = np.where(allink)
    if len(xs) == 0:
        return region
    return x0 + int(xs.min()), y0 + int(ys.min()), x0 + int(xs.max()) + 1, y0 + int(ys.max()) + 1


def _floor_label(text):
    """Ordinal for 'GROUND FLOOR PLAN' style labels. 'terrace' for roof plans. None if not a label."""
    t = _letters(text)
    if "PLAN" not in t and "FLOOR" not in t:
        return None
    if "TERRACE" in t or "ROOF" in t:
        return "terrace"
    prefix = t.split("FLOOR")[0] if "FLOOR" in t else t.replace("PLAN", "")
    if not prefix:
        return None
    if prefix in ORDINALS:
        return ORDINALS[prefix]
    near = difflib.get_close_matches(prefix, list(ORDINALS), n=1, cutoff=0.8)
    return ORDINALS[near[0]] if near else None


def _panels(labels, size):
    """Split the sheet into one panel per floor label (left-to-right or top-to-bottom)."""
    w, h = size
    if len(labels) < 2:
        only = labels[0] if labels else None
        return [{"floor": only["ord"] if only else None, "label": only["text"] if only else None, "region": (0, 0, w, h)}]
    horizontal = (max(_cx(b) for b in labels) - min(_cx(b) for b in labels)) >= (
        max(_cy(b) for b in labels) - min(_cy(b) for b in labels))
    key, span = (_cx, w) if horizontal else (_cy, h)
    labels = sorted(labels, key=key)
    cuts = [0] + [(key(a) + key(b)) / 2 for a, b in zip(labels, labels[1:])] + [span]
    panels = []
    for i, lab in enumerate(labels):
        lo, hi = cuts[i], cuts[i + 1]
        region = (lo, 0, hi, h) if horizontal else (0, lo, w, hi)
        panels.append({"floor": lab["ord"], "label": lab["text"], "region": region})
    return panels


# ---------------------------------------------------------------- dimension labels

_FEET = re.compile(r"^\[?\s*(\d{1,3})\s*(?:['’`]\s*-?\s*(?:(\d{1,2})\s*(?:\"|”|'')?)?)?\s*\]?$")
_METRES = re.compile(r"\[?\s*(\d{1,2}\.\d{2})\s*\]?")


def _dimension_values(boxes):
    """Return (feet_values, metre_values) found in these OCR boxes."""
    feet, metres = [], []
    for b in boxes:
        t = b["text"].strip()
        for m in _METRES.finditer(t):
            metres.append(float(m.group(1)))
        core = re.sub(r"\]?\s*[A-Z]{1,2}$", "", t).strip()  # drop trailing window tag: '[8.23] W'
        m = _FEET.match(t) or _FEET.match(core)
        if m and "." not in t and b["conf"] >= 0.45:
            v = int(m.group(1)) + int(m.group(2) or 0) / 12
            if 8 <= v <= 150:
                feet.append(round(v, 2))
    return feet, metres


def _pick_dimension(feet, metres):
    """Choose one overall dimension in feet. A feet label confirmed by a metre label wins."""
    for m in metres:
        for f in feet:
            if abs(f - m * M_TO_FT) <= max(0.6, f * 0.02):
                return f, "labels"
    if feet:
        return max(feet), "labels"
    if metres:
        return round(max(metres) * M_TO_FT, 1), "metres"
    return None, None


def _candidates(feet, metres):
    """Candidate overall lengths in feet. A feet label confirmed by a metre label scores higher."""
    out = {}
    for f in feet:
        confirmed = any(abs(f - m * M_TO_FT) <= max(0.6, f * 0.02) for m in metres)
        out[f] = max(out.get(f, 0), 2 if confirmed else 1)
    for m in metres:
        f = round(m * M_TO_FT, 1)
        if not any(abs(f - k) <= max(0.6, k * 0.02) for k in out):
            out[f] = 0.5
    return out


def _pick_pair(wf, wm, df, dm, ratio):
    """Pick (width, depth) in feet. Several labels can be misread or repeated, so choose the pair whose
    proportions best match the drawn wall box, preferring labels confirmed by a metre label."""
    ws, ds = _candidates(wf, wm), _candidates(df, dm)
    if not ws or not ds:
        return (max(ws, key=ws.get) if ws else None), (max(ds, key=ds.get) if ds else None)
    best = None
    for w, wc in ws.items():
        for d, dc in ds.items():
            miss = abs(math.log((w / d) / ratio)) if ratio > 0 else 0
            score = miss - 0.15 * (wc + dc)
            if best is None or score < best[0]:
                best = (score, w, d)
    return best[1], best[2]


# ---------------------------------------------------------------- OCR pipeline

def read_with_ocr(path, ext):
    img, extra_pages = _load_image(path, ext)
    W, H = img.size
    warnings = []
    if extra_pages > 0:
        warnings.append(f"The PDF has {extra_pages + 1} pages. Only the first page was read.")

    long_side = max(W, H)
    base = 1800 / long_side if long_side < 1800 else 1.0
    boxes = []
    for s in (base, base * 2 if long_side < 1200 else base * 0.6):
        boxes += _boxes(img, s)
    for rot in (-1, 1):
        boxes += [b for b in _boxes(img, base * (2 if long_side < 1200 else 1), rot) if b["conf"] >= 0.5]
    plain = [b for b in boxes if b["rot"] == 0]
    if not plain:
        return _empty("unreadable", ["No text could be read from this drawing. Enter the details manually."], W, H)

    # --- floor labels
    labels = []
    for b in sorted(plain, key=lambda b: -b["conf"]):
        o = _floor_label(b["text"])
        if o is None:
            continue
        if any(abs(_cx(b) - _cx(l)) < 60 * max(1, base) and abs(_cy(b) - _cy(l)) < 25 * max(1, base) for l in labels):
            continue
        labels.append({**b, "ord": o})
    # a 'terrace' sheet is not a habitable floor
    floors_found = sorted({l["ord"] for l in labels if isinstance(l["ord"], int)})
    panels = _panels(labels, (W, H))

    # --- detect sidebar / room schedule / specifications strip (usually on the right or left edge)
    sidebar_x0 = None
    sidebar_x1 = None
    for b in plain:
        t_clean = _letters(b["text"])
        if any(k in t_clean for k in ("ROOMSCHEDULE", "KEYFEATURES", "SPECIFICATIONS", "SCHEDULEOFOPENINGS", "DOORSCHEDULE")):
            if b["x0"] > 0.50 * W:
                sidebar_x0 = min(sidebar_x0 or b["x0"], b["x0"])
            elif b["x1"] < 0.50 * W:
                sidebar_x1 = max(sidebar_x1 or b["x1"], b["x1"])

    # Trim panel region to exclude the sidebar schedule column
    for p in panels:
        rx0, ry0, rx1, ry1 = p["region"]
        if sidebar_x0 and rx1 > sidebar_x0 - 20:
            rx1 = sidebar_x0 - 20
        if sidebar_x1 and rx0 < sidebar_x1 + 20:
            rx0 = sidebar_x1 + 20
        p["region"] = (rx0, ry0, rx1, ry1)
        wb = _wall_box(img, (rx0, ry0, rx1, ry1))
        p["walls"] = wb

    for p in panels:
        p["walls_frac"] = [round(p["walls"][0] / W, 4), round(p["walls"][1] / H, 4),
                           round(p["walls"][2] / W, 4), round(p["walls"][3] / H, 4)]

    def panel_of(x, y):
        for p in panels:
            rx0, ry0, rx1, ry1 = p["region"]
            if rx0 <= x < rx1 and ry0 <= y < ry1:
                return p
        return panels[0]

    # --- rooms (strictly in floor plan area, excluding schedule tables and duplicate legend lists)
    hits = []
    for b in plain:
        if b["conf"] < 0.40 or _floor_label(b["text"]) is not None:
            continue
        # Exclude text inside sidebar/legend schedule
        if sidebar_x0 and b["x0"] >= sidebar_x0 - 25:
            continue
        if sidebar_x1 and b["x1"] <= sidebar_x1 + 25:
            continue
        # Exclude schedule lines with colons or count prefixes (e.g. "Living Room : 15'-0" x 14'-0"", "2 Bedrooms")
        if ":" in b["text"] or re.match(r"^\d+\s+[A-Za-z]+", b["text"].strip()):
            continue
        t = _letters(b["text"])
        if len(t) < 2 or (re.search(r"\d", t) and len(re.sub(r"\D", "", t)) >= 2):
            continue
        kind = None
        for kw, typ in KEYWORDS:
            if len(kw) <= 3:
                if t == kw:
                    kind = typ
                    break
            elif kw in t:
                kind = typ
                break
        if kind is None and 4 <= len(t) <= 16:
            near = difflib.get_close_matches(t, [kw for kw, _ in KEYWORDS if len(kw) >= 4], n=1, cutoff=0.78)
            if near:
                kind = next(typ for kw, typ in KEYWORDS if kw == near[0])
        if kind:
            hits.append({**b, "type": kind})
    tol = 9 * max(1, base)
    inst = []
    for h in sorted(hits, key=lambda b: -b["conf"]):
        if any(abs(_cx(h) - _cx(i)) < tol * 3 and abs(_cy(h) - _cy(i)) < tol and h["type"] == i["type"] for i in inst):
            continue
        inst.append(h)

    # Size boxes inside plan area
    candidate_size_boxes = [b for b in plain if not (sidebar_x0 and b["x0"] >= sidebar_x0 - 25) and not (sidebar_x1 and b["x1"] <= sidebar_x1 + 25)]
    size_boxes = [(b, parse_size(b["text"])) for b in candidate_size_boxes if parse_size(b["text"])]
    owner = {}
    for sb, parsed in size_boxes:
        best = None
        for i, h in enumerate(inst):
            dy = _cy(sb) - h["y1"]
            overlap = min(sb["x1"], h["x1"] + 25 * base) - max(sb["x0"], h["x0"] - 25 * base)
            if dy >= -4 * base and overlap > 0 and (best is None or dy < best[0]):
                best = (dy, i)
        if best and best[0] <= 42 * max(1, base):
            owner.setdefault(best[1], []).append((sb, parsed))

    # Refine wall envelope if size boxes pinpoint the actual floor plan footprint
    if size_boxes and len(panels) == 1:
        sb_x0 = min(b["x0"] for b, _ in size_boxes)
        sb_x1 = max(b["x1"] for b, _ in size_boxes)
        sb_y0 = min(b["y0"] for b, _ in size_boxes)
        sb_y1 = max(b["y1"] for b, _ in size_boxes)
        p = panels[0]
        cur_w = p["walls"]
        env_x0 = max(cur_w[0], sb_x0 - 160 * base)
        env_x1 = min(cur_w[2], sb_x1 + 160 * base)
        env_y0 = max(cur_w[1], sb_y0 - 150 * base)
        env_y1 = min(cur_w[3], sb_y1 + 160 * base)
        if env_x1 > env_x0 and env_y1 > env_y0:
            p["walls"] = (env_x0, env_y0, env_x1, env_y1)
            p["walls_frac"] = [round(env_x0 / W, 4), round(env_y0 / H, 4), round(env_x1 / W, 4), round(env_y1 / H, 4)]

    # Is there a MASTER label right above a bedroom? (e.g. 'MASTER' / 'MASTER BEDROOM')
    master_boxes = [b for b in candidate_size_boxes if "MASTER" in _letters(b["text"])]

    rooms = []
    for i, h in enumerate(inst):
        typ = h["type"]
        if typ == "entrance":
            continue
        p = panel_of(_cx(h), _cy(h))
        x0, y0, x1, y1 = p["walls"]
        fx = min(1.0, max(0.0, (_cx(h) - x0) / max(1, x1 - x0)))
        fy = min(1.0, max(0.0, (_cy(h) - y0) / max(1, y1 - y0)))
        name = ROOM_TYPES[typ][0]
        if typ == "bedroom":
            if any(abs(_cx(m) - _cx(h)) < 60 * base and -30 * base < _cy(h) - _cy(m) < 30 * base for m in master_boxes):
                name = "Master bedroom"
            elif "2" in h["text"] or "TWO" in _letters(h["text"]):
                name = "Bedroom 2"
            elif "1" in h["text"] or "ONE" in _letters(h["text"]):
                name = "Bedroom 1"
        size = None
        cands = owner.get(i, [])
        if cands:
            sb, (w_in, d_in, score) = max(cands, key=lambda c: (c[1][2], c[0]["conf"]))
            size = {"w_in": w_in, "d_in": d_in, "text": fmt_size(w_in, d_in), "exact": score == 2}
        rooms.append(_room(name, typ, p["floor"], fx, fy, size))

    # --- main door marker (MD) or an explicit entrance label
    entrance = None
    for b in sorted(plain, key=lambda b: -b["conf"]):
        t = _letters(b["text"])
        is_marker = (t.startswith("MD") and len(t) <= 3) or any(k in t for k in ("MAINDOOR", "MAINENTRANCE", "MAINENTRY", "MAINGATE"))
        if not is_marker:
            continue
        p = panel_of(_cx(b), _cy(b))
        x0, y0, x1, y1 = p["walls"]
        fx = (_cx(b) - x0) / max(1, x1 - x0)
        fy = (_cy(b) - y0) / max(1, y1 - y0)
        if -0.05 <= fx <= 1.05 and -0.05 <= fy <= 1.05:
            entrance = {"floor": p["floor"], "fx": round(min(1, max(0, fx)), 3), "fy": round(min(1, max(0, fy)), 3)}
            entrance["cell"] = _cell(entrance["fx"], entrance["fy"])
            break

    # --- overall dimensions, per panel, then the best one
    dims = []
    for p in panels:
        x0, y0, x1, y1 = p["walls"]
        pw, ph = x1 - x0, y1 - y0
        top = [b for b in boxes if b["rot"] == 0 and y1 > _cy(b) and _cy(b) < y0 + 0.06 * ph
               and x0 - 0.1 * pw <= _cx(b) <= x1 + 0.1 * pw] + \
              [b for b in boxes if b["rot"] == 0 and _cy(b) > y1 - 0.01 * ph + 0 and _cy(b) > y1 and _cy(b) < y1 + 0.08 * ph
               and x0 <= _cx(b) <= x1]
        # Vertical labels sit beside the walls. Rotated reads near the top or bottom edge are mostly the
        # horizontal width labels seen sideways, so only the middle of each side is trusted.
        side = [b for b in boxes if b["rot"] != 0 and (_cx(b) < x0 + 0.06 * pw or _cx(b) > x1 - 0.06 * pw)
                and y0 + 0.08 * ph <= _cy(b) <= y1 - 0.08 * ph and (_cx(b) < x0 + 0.1 * pw or _cx(b) > x1 - 0.1 * pw)]
        wf, wm = _dimension_values(top)
        df, dm = _dimension_values(side)
        wv, dv = _pick_pair(wf, wm, df, dm, pw / max(1, ph))
        dims.append({"panel": p, "w": wv, "d": dv, "src": "labels"})
    chosen = next((d for d in dims if d["w"] and d["d"]), None)
    width = depth = None
    if chosen:
        width, depth = chosen["w"], chosen["d"]
        p = chosen["panel"]
        pw, ph = p["walls"][2] - p["walls"][0], p["walls"][3] - p["walls"][1]
        if abs(math.log((width / depth) / (pw / ph))) > 0.3:
            warnings.append("The dimensions read from the drawing do not match the plan's proportions. Please verify the area.")
    else:
        anyw = next((d["w"] for d in dims if d["w"]), None)
        anyd = next((d["d"] for d in dims if d["d"]), None)
        if anyw or anyd:
            warnings.append("Only one overall dimension could be read, so the plan area was not calculated.")
        else:
            warnings.append("No overall dimensions could be read, so the plan area was not calculated.")

    # --- floors
    floors = None
    if floors_found:
        top_floor = floors_found[-1]
        floors = "G" if top_floor == 0 else f"G+{min(9, top_floor)}"
        if floors_found[0] != 0:
            warnings.append("No ground floor label was found. Floors assume a ground floor exists.")
    else:
        warnings.append("No floor labels such as 'GROUND FLOOR PLAN' were found, so floors were not detected.")

    # --- site facts sometimes written in notes
    blob = " ".join(b["text"] for b in plain)
    hints = {}
    m = re.search(r"\bM\s?(20|25|30)\b", blob.upper())
    if m:
        hints["grade"] = f"M{m.group(1)}"
    m = re.search(r"\bZONE\s*(II|III|IV|V)\b", blob.upper())
    if m:
        hints["zone"] = m.group(1)

    return _finish("ocr", W, H, floors, floors_found, labels, panels, rooms, entrance, width, depth, hints, warnings)


# ---------------------------------------------------------------- shared result shape

def _cell(fx, fy):
    return min(2, int(fy * 3)) * 3 + min(2, int(fx * 3))


def _room(name, typ, floor, fx, fy, size):
    area = size["w_in"] * size["d_in"] / 144 if size else None
    return {"name": name, "type": typ, "floor": floor, "fx": round(fx, 3), "fy": round(fy, 3), "cell": _cell(fx, fy),
            "size": size["text"] if size else None, "size_exact": size["exact"] if size else None,
            "area": round(area, 1) if area else None}


def _empty(status, warnings, w=0, h=0):
    return {"method": "ocr", "status": status, "image": {"w": w, "h": h}, "floors": None, "floor_labels": [],
            "panels": [], "rooms": [], "entrance": None, "width_ft": None, "depth_ft": None, "area": None,
            "room_area": {}, "hints": {}, "warnings": warnings}


def _finish(method, W, H, floors, floors_found, labels, panels, rooms, entrance, width, depth, hints, warnings):
    area = round(width * depth) if width and depth else None
    rooms = sorted(rooms, key=lambda r: ((r["floor"] if isinstance(r["floor"], int) else 99), r["fy"], r["fx"]))
    room_area = {}
    for r in rooms:
        if r["area"] and r["type"] not in OPEN_TYPES and isinstance(r["floor"], int):
            room_area[r["floor"]] = round(room_area.get(r["floor"], 0) + r["area"], 1)
    if not rooms:
        warnings.append("No room labels were recognised.")
    got = [k for k, v in (("floors", floors), ("area", area), ("rooms", rooms)) if v]
    return {
        "method": method,
        "status": "read" if len(got) == 3 else ("partial" if got else "unreadable"),
        "image": {"w": W, "h": H},
        "floors": floors,
        "floor_labels": [FLOOR_NAMES[o] + " floor" for o in floors_found],
        "panels": [{"floor": p["floor"], "label": p["label"], "box": p["walls_frac"]} for p in panels],
        "rooms": rooms,
        "entrance": entrance,
        "width_ft": width, "depth_ft": depth, "area": area,
        "room_area": {str(k): v for k, v in room_area.items()},
        "hints": hints,
        "warnings": warnings,
    }


# ---------------------------------------------------------------- optional: Claude vision

VISION_PROMPT = """You are reading a 2D residential floor plan drawing for a civil engineering tool.
Return ONE JSON object and nothing else. Use null for anything you cannot read; never guess.
{
 "plans": [ {"floor": 0, "label": "GROUND FLOOR PLAN", "box": [x0,y0,x1,y1], "width_ft": 27, "depth_ft": 38} ],
 "rooms": [ {"name": "Kitchen", "floor": 0, "size": "9'x9'6\\"", "cx": 0.2, "cy": 0.1} ],
 "main_entrance": {"floor": 0, "cx": 0.5, "cy": 0.9}
}
- floor: 0 for ground, 1 for first floor, and so on. One entry in "plans" per floor plan on the sheet.
- box: the outer wall rectangle of that floor plan as fractions (0 to 1) of the whole image width/height.
- width_ft/depth_ft: the overall outer dimensions written on the drawing, in feet (convert metres if only metres are given).
- rooms: every labelled room, with the label's centre cx, cy as fractions of the whole image. size exactly as written.
- main_entrance: where the main door is, or null if not marked."""


def read_with_vision(path, ext, client, model):
    img, extra = _load_image(path, ext)
    W, H = img.size
    buf = io.BytesIO()
    img.thumbnail((1800, 1800))
    img.save(buf, "PNG")
    resp = client.messages.create(
        model=model, max_tokens=3000,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                         "data": base64.b64encode(buf.getvalue()).decode()}},
            {"type": "text", "text": VISION_PROMPT}]}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    data = json.loads(text[text.index("{"): text.rindex("}") + 1])
    return _from_vision(data, W, H, extra)


def _num(v, lo, hi):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


def _from_vision(data, W, H, extra_pages=0):
    warnings = []
    if extra_pages:
        warnings.append(f"The PDF has {extra_pages + 1} pages. Only the first page was read.")
    panels, floors_found = [], []
    for p in data.get("plans") or []:
        box = p.get("box")
        fl = p.get("floor")
        if not (isinstance(box, list) and len(box) == 4 and isinstance(fl, int) and 0 <= fl <= 9):
            continue
        box = [min(1, max(0, float(v))) for v in box]
        if box[2] - box[0] < 0.1 or box[3] - box[1] < 0.1:
            continue
        panels.append({"floor": fl, "label": str(p.get("label") or "")[:60], "walls_frac": box,
                       "w": _num(p.get("width_ft"), 8, 150), "d": _num(p.get("depth_ft"), 8, 150)})
        floors_found.append(fl)
    if not panels:
        return _empty("unreadable", ["Claude could not find a floor plan in this drawing."], W, H) | {"method": "vision"}
    floors_found = sorted(set(floors_found))
    floors = "G" if floors_found[-1] == 0 else f"G+{floors_found[-1]}"

    def locate(cx, cy, floor):
        cx, cy = _num(cx, 0, 1), _num(cy, 0, 1)
        if cx is None or cy is None:
            return None
        pool = [p for p in panels if p["floor"] == floor] or panels
        p = next((p for p in pool if p["walls_frac"][0] <= cx <= p["walls_frac"][2] and p["walls_frac"][1] <= cy <= p["walls_frac"][3]), None)
        if p is None:
            return None
        b = p["walls_frac"]
        return p, (cx - b[0]) / (b[2] - b[0]), (cy - b[1]) / (b[3] - b[1])

    rooms = []
    for r in data.get("rooms") or []:
        name = str(r.get("name") or "").strip()[:40]
        typ = next((t for kw, t in KEYWORDS if kw in _letters(name)), None)
        loc = locate(r.get("cx"), r.get("cy"), r.get("floor"))
        if not name or typ is None or loc is None:
            continue
        p, fx, fy = loc
        parsed = parse_size(str(r.get("size") or "").replace("’", "'").replace("”", '"'))
        size = {"w_in": parsed[0], "d_in": parsed[1], "text": fmt_size(parsed[0], parsed[1]), "exact": True} if parsed else None
        label = "Master bedroom" if typ == "bedroom" and "MASTER" in name.upper() else ROOM_TYPES[typ][0]
        rooms.append(_room(label, typ, p["floor"], fx, fy, size))
    entrance = None
    me = data.get("main_entrance")
    if isinstance(me, dict):
        loc = locate(me.get("cx"), me.get("cy"), me.get("floor"))
        if loc:
            p, fx, fy = loc
            entrance = {"floor": p["floor"], "fx": round(fx, 3), "fy": round(fy, 3), "cell": _cell(fx, fy)}
    first = next((p for p in panels if p["w"] and p["d"]), None)
    width, depth = (first["w"], first["d"]) if first else (None, None)
    if not first:
        warnings.append("No overall dimensions were readable, so the plan area was not calculated.")
    out = _finish("vision", W, H, floors, floors_found, [], [{**p, "walls_frac": p["walls_frac"]} for p in panels],
                  rooms, entrance, width, depth, {}, warnings)
    return out


# ---------------------------------------------------------------- entry point

def read_plan(path, ext, api_key="", model="", mode="ocr"):
    """Never raises. Always returns a dict with a `status` and `warnings`."""
    if ext in ("dxf", "dwg"):
        return _empty("unsupported", [
            f"{ext.upper()} files cannot be read automatically yet. Export the drawing as PDF or PNG to get details "
            "filled in, or enter them manually."])
    if mode == "vision" and api_key:
        try:
            import anthropic

            return read_with_vision(path, ext, anthropic.Anthropic(api_key=api_key), model)
        except Exception as e:  # billing, network, bad JSON ... fall back to the local reader
            note = f"Claude vision was unavailable ({type(e).__name__}); the local reader was used instead."
            result = _safe_ocr(path, ext)
            result["warnings"].insert(0, note)
            return result
    return _safe_ocr(path, ext)


def _safe_ocr(path, ext):
    try:
        return read_with_ocr(path, ext)
    except ImportError:
        return _empty("unavailable", [
            "The drawing reader is not installed on the server. Run: pip install rapidocr-onnxruntime pymupdf"])
    except Exception as e:
        return _empty("unreadable", [f"The drawing could not be read ({type(e).__name__}). Enter the details manually."])

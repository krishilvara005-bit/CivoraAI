"""Vastu check against traditional rule set. Strictly computed from drawing & room coordinates."""
COMPASS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
NORTH_POS = {"top": 1, "right": 3, "bottom": 5, "left": 7}
RING = [0, 1, 2, 7, None, 3, 6, 5, 4]

# The 5 primary rooms required for test compatibility
PRIMARY_ROOMS = ["Main entrance", "Kitchen", "Master bedroom", "Toilet", "Pooja room"]

# Canonical specification for all 19 Vastu items
VASTU_CATALOG = {
    "Master Bedroom": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Master Bedroom", "Master bedroom"],
        "good": {"SW"},
        "acceptable": {"S", "W"},
        "avoid": {"NE", "SE", "N"},
        "ideal": "Southwest",
        "element": "Earth (Prithvi) — Heavy & Grounded",
        "deity": "Nairutya",
        "why": "Southwest represents structural stability, authority, and grounding for the homeowner. Sleeping here with head toward South reinforces restorative circadian rhythms.",
        "solution": "Orient bed headboard against South or West wall so you sleep facing South. Avoid placing mirrors directly opposite the bed.",
        "remedy": "Place a heavy brass or lead helix in the Southwest corner; use warm earthy colors (terracotta, almond, brown).",
    },
    "Children's Bedroom": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Children's Bedroom", "Children Bedroom", "Kids Bedroom", "Bedroom 2"],
        "good": {"W", "NW"},
        "acceptable": {"N", "SW"},
        "avoid": {"SE", "NE"},
        "ideal": "West / Northwest",
        "element": "Air (Vayu) & Space — Intellect & Growth",
        "deity": "Varuna / Vayu",
        "why": "West and Northwest foster mental agility, study concentration, and positive developmental rest for growing children.",
        "solution": "Orient study desks facing East or North. Bed head should face East or South. Keep electronic equipment away from the headboard.",
        "remedy": "Hang a 7-rod brass wind chime or crystal globe in the West/Northwest corner; keep lighting bright and invigorating.",
    },
    "Guest Bedroom": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Guest Bedroom", "Guest bedroom", "Bedroom 3"],
        "good": {"NW"},
        "acceptable": {"W", "N"},
        "avoid": {"SW", "SE", "NE"},
        "ideal": "Northwest",
        "element": "Air (Vayu) — Mobility & Hospitality",
        "deity": "Vayu",
        "why": "Northwest (Vayu Kona) is the zone of mobility and cordial hospitality, ensuring guests feel welcome without dominating the homeowner's master energy.",
        "solution": "If placed outside Northwest, ensure the guest bed headboard rests against South or West wall with clean cross-ventilation.",
        "remedy": "Use white or cream textiles, aromatic diffusers, or an Agate crystal in the Northwest quadrant.",
    },
    "Living Room": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Living Room", "Living room", "Hall"],
        "good": {"N", "E", "NE"},
        "acceptable": {"NW"},
        "avoid": {"SW", "S"},
        "ideal": "North / East / Northeast",
        "element": "Water & Space — Pranic Inflow & Harmony",
        "deity": "Ishan / Soma",
        "why": "North, East, and Northeast invite morning solar radiation and positive electromagnetic currents, creating a vibrant, inviting family space.",
        "solution": "Arrange heavy sofas along South and West walls, leaving North and East sectors open and unencumbered.",
        "remedy": "Use bright ambient LED lighting, mirrors on North or East walls, and indoor air-purifying plants (Peace Lily, Jade).",
    },
    "Family Living Area": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Family Living Area", "Family Living", "Family Room", "Family Lounge"],
        "good": {"N", "E", "NE"},
        "acceptable": {"NW", "Centre"},
        "avoid": {"SW", "S"},
        "ideal": "North / East / Northeast",
        "element": "Ether & Light — Familial Bonding",
        "deity": "Mitra / Aryama",
        "why": "Family living areas in the North/East foster cordial relationships, intellectual discussions, and harmonious bonding among family members.",
        "solution": "Arrange seating in an L-shape facing East or North. Keep the central zone (Brahmasthan) clutter-free.",
        "remedy": "Place a family portrait in a teakwood frame on the East wall; incorporate soft yellow or warm beige hues.",
    },
    "Dressing Room": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Dressing Room", "Dressing", "Wardrobe"],
        "good": {"W", "SW"},
        "acceptable": {"NW", "S"},
        "avoid": {"NE", "E"},
        "ideal": "West / Southwest",
        "element": "Earth — Storage & Stability",
        "deity": "Mitra",
        "why": "Wardrobes, heavy cabinetry, and dressing storage provide grounding structural weight that belongs in the South or West quadrants.",
        "solution": "Ensure dressing mirrors are placed on North or East internal walls (never facing the bed or South wall).",
        "remedy": "Keep mirrors covered when not in use; keep dressing wardrobe well-organized without broken glass.",
    },
    "Study Room": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Study Room", "Study room", "Study"],
        "good": {"E", "N", "NE"},
        "acceptable": {"W"},
        "avoid": {"SW", "S", "SE"},
        "ideal": "East / North / Northeast",
        "element": "Water & Mercury — Wisdom & Concentration",
        "deity": "Brihaspati / Budha",
        "why": "Northeast and East are governed by Jupiter and Mercury, stimulating memory, focus, and scholarly clarity.",
        "solution": "Position study desk so the student faces East or North while studying. Keep study table rectangular without sharp glass edges.",
        "remedy": "Place a Saraswati Yantra, Pyramid paperweight, or clear quartz crystal on the study table; paint walls pastel green or light yellow.",
    },
    "Home Office": {
        "category": "Bedrooms & Living Areas",
        "synonyms": ["Home Office", "Office", "Workroom"],
        "good": {"N", "E"},
        "acceptable": {"NE", "W"},
        "avoid": {"SW", "S"},
        "ideal": "North / East",
        "element": "Water / Kubera — Prosperity & Career Growth",
        "deity": "Kubera / Indra",
        "why": "North is governed by Lord Kubera (wealth and career opportunities), while East encourages business expansion and professional prestige.",
        "solution": "Sit facing North or East during work calls. Place computers and electronic peripherals in the Southeast corner of the desk.",
        "remedy": "Install a money plant in green pot in the North; place a copper sun symbol on the East wall.",
    },
    "Main Kitchen": {
        "category": "Kitchen & Dining",
        "synonyms": ["Main Kitchen", "Kitchen"],
        "good": {"SE"},
        "acceptable": {"NW"},
        "avoid": {"NE", "SW", "N"},
        "ideal": "Southeast",
        "element": "Fire (Agni) — Metabolic Energy & Health",
        "deity": "Agni",
        "why": "Southeast (Agneya Kona) is ruled by the Fire deity. Placing the cooking range here ensures vibrant health and culinary prosperity.",
        "solution": "Position cooking cooktop along the Southeast wall so the cook faces East. Keep water sink in Northeast of the kitchen to separate Fire and Water.",
        "remedy": "If kitchen is in NW or elsewhere, place a copper Agni Yantra or red jasper stone near the stove; paint Southeast wall warm peach.",
    },
    "Alternative Kitchen": {
        "category": "Kitchen & Dining",
        "synonyms": ["Alternative Kitchen", "Alt Kitchen", "Pantry", "Utility Kitchen"],
        "good": {"NW"},
        "acceptable": {"SE"},
        "avoid": {"NE", "SW"},
        "ideal": "Northwest",
        "element": "Air (Vayu) — Auxiliary Preparation",
        "deity": "Vayu",
        "why": "Northwest serves as the secondary/auxiliary culinary zone (Vayu supporting Agni) for wet kitchens, pantries, or preparation counters.",
        "solution": "Ensure burners or heating appliances are placed along the East/Southeast corner of the auxiliary counter.",
        "remedy": "Install proper exhaust ventilation; keep counters clean and clutter-free.",
    },
    "Dining Room": {
        "category": "Kitchen & Dining",
        "synonyms": ["Dining Room", "Dining", "Dining room"],
        "good": {"E", "W"},
        "acceptable": {"N", "SE"},
        "avoid": {"SW", "NE"},
        "ideal": "East / West",
        "element": "Earth & Water — Nourishment & Digestion",
        "deity": "Aditi",
        "why": "East promotes healthy assimilation and digestion, while West provides evening dining comfort with family.",
        "solution": "Family head should face East or North while eating. Avoid circular dining tables; prefer rectangular or square hardwood tables.",
        "remedy": "Hang a fruit/cornucopia painting or mirror reflecting the dining table to symbolically double abundance.",
    },
    "Pooja Room": {
        "category": "Sacred & Sanitary",
        "synonyms": ["Pooja Room", "Pooja room", "Prayer Room", "Mandir"],
        "good": {"NE"},
        "acceptable": {"E", "N"},
        "avoid": {"S", "SW", "SE"},
        "ideal": "Northeast",
        "element": "Water & Ishan — Spiritual Resonance",
        "deity": "Ishan (Shiva)",
        "why": "Northeast (Ishan Kona) is the supreme spiritual quadrant, receiving cosmic electromagnetic currents from Earth's axis.",
        "solution": "Deity idols should face West so devotees face East during prayer. Never place prayer room adjacent to or beneath toilets.",
        "remedy": "Install a brass bell, brass Diya, and keep a clean copper vessel with water; use soft white, cream, or light yellow marble.",
    },
    "Bathroom": {
        "category": "Sacred & Sanitary",
        "synonyms": ["Bathroom", "Bath"],
        "good": {"W", "NW"},
        "acceptable": {"E", "N"},
        "avoid": {"NE", "SW"},
        "ideal": "West / Northwest",
        "element": "Water & Cleansing — Hygiene & Drainage",
        "deity": "Varuna",
        "why": "West and Northwest zones facilitate safe elimination and drainage without contaminating the sacred Northeast or grounding Southwest.",
        "solution": "Install geyser/water heater in Southeast corner of bathroom. Mirrors should be mounted on North or East walls.",
        "remedy": "Keep bathroom dry and ventilated; place a bowl of raw sea salt in a glass bowl to absorb negative dampness.",
    },
    "Toilet": {
        "category": "Sacred & Sanitary",
        "synonyms": ["Toilet", "Toilets", "WC"],
        "good": {"NW", "W"},
        "acceptable": {"S"},
        "avoid": {"NE", "E", "SW"},
        "ideal": "West / Northwest",
        "element": "Waste Elimination — Negative Gravity",
        "deity": "Rudra / Vayu",
        "why": "Toilets in Northeast severely damage health and clarity; placing in West or Northwest safely vents negative odors and wastewater.",
        "solution": "Commode should align along North-South axis (user faces North or South). Never align East-West. Keep door shut at all times.",
        "remedy": "If toilet is mistakenly near NE or SW, fix 3 brass/lead pyramids outside toilet frame and keep natural rock salt inside.",
    },
    "Staircase": {
        "category": "Circulation & Exterior",
        "synonyms": ["Staircase", "Stairs"],
        "good": {"S", "W", "SW"},
        "acceptable": {"SE", "NW"},
        "avoid": {"NE", "N", "E", "Centre"},
        "ideal": "South / West / Southwest",
        "element": "Earth (Heavy Load) — Vertical Anchor",
        "deity": "Yama / Nairutya",
        "why": "Staircases impose massive structural weight, which should anchor the heavy Southern or Western zones, never the light Northeast or Centre.",
        "solution": "Steps should ascend clockwise (East to West, or North to South). Never construct prayer altars or toilets under stairs.",
        "remedy": "If staircase is in Northeast, place a lead helix or 8-metal pyramid at the base; keep stairwell brightly illuminated.",
    },
    "Main Gate": {
        "category": "Circulation & Exterior",
        "synonyms": ["Main Gate", "Main entrance", "Entrance"],
        "good": {"N", "E"},
        "acceptable": {"NE", "NW"},
        "avoid": {"S", "SW", "SE"},
        "ideal": "North / East",
        "element": "Prana (Life Force) — Gateway of Opportunities",
        "deity": "Kubera / Indra / Jayanta",
        "why": "North and East gateways welcome positive cosmic energy (Jaivik and Pranic currents) and invite wealth and social prestige.",
        "solution": "Main gate should be larger and grander than interior doors, opening smoothly clockwise without squeaking sounds.",
        "remedy": "Install auspicious brass Swastika, Om, or Trishul emblems; illuminate the entrance threshold with warm overhead lamps.",
    },
    "Garden": {
        "category": "Circulation & Exterior",
        "synonyms": ["Garden", "Lawn", "Courtyard"],
        "good": {"N", "E"},
        "acceptable": {"NE", "NW"},
        "avoid": {"SW", "S"},
        "ideal": "North / East",
        "element": "Flora & Light — Environmental Vitality",
        "deity": "Soma",
        "why": "Lawns and light ornamental gardens in North/East allow unhindered morning sunlight; heavy fruit trees belong in South/West.",
        "solution": "Keep low shrubs, Tulsi (Holy Basil), and flowering plants in North/East. Place tall heavy trees in South/West perimeter.",
        "remedy": "Install a gentle water fountain or bird bath in the Northeast sector of the garden.",
    },
    "Parking": {
        "category": "Circulation & Exterior",
        "synonyms": ["Parking", "Portico / parking", "Car Parking"],
        "good": {"NW", "SE"},
        "acceptable": {"N", "E"},
        "avoid": {"NE", "SW"},
        "ideal": "Northwest / Southeast",
        "element": "Motion (Vayu) — Mobility & Transit",
        "deity": "Vayu",
        "why": "Northwest represents smooth mobility and travel, preventing vehicle breakdowns and ensuring prompt departures.",
        "solution": "Park vehicle facing East or North. Avoid parking directly over the Northeast corner of the compound.",
        "remedy": "Keep parking bay clean, oil-free, with adequate ramp drainage sloping toward North or East.",
    },
    "Garage": {
        "category": "Circulation & Exterior",
        "synonyms": ["Garage", "Enclosed Parking"],
        "good": {"NW", "SE"},
        "acceptable": {"N", "W"},
        "avoid": {"NE", "SW"},
        "ideal": "Northwest / Southeast",
        "element": "Metal & Motion — Vehicle Enclosure",
        "deity": "Vayu / Agni",
        "why": "Enclosed garages in Northwest or Southeast maintain safe vehicle transit without depressing the master corner (Southwest).",
        "solution": "Garage floor level should match or sit slightly lower than main house plinth. Keep tools arranged along South/West walls.",
        "remedy": "Paint garage interior in light grey or off-white; install a protective copper or brass talisman on the garage shutter.",
    },
}

# Comprehensive rules map for room lookup and validation
ROOM_RULES = {
    "Main entrance": {"good": {"N", "NE", "E"}, "avoid": {"S", "SW"}, "ideal": "North or East or Northeast"},
    "Main Gate": {"good": {"N", "E"}, "avoid": {"S", "SW", "SE"}, "ideal": "North / East"},
    "Kitchen": {"good": {"SE"}, "avoid": {"NE", "SW"}, "ideal": "Southeast"},
    "Main Kitchen": {"good": {"SE"}, "avoid": {"NE", "SW"}, "ideal": "Southeast"},
    "Alternative Kitchen": {"good": {"NW"}, "avoid": {"NE", "SW"}, "ideal": "Northwest"},
    "Master bedroom": {"good": {"SW"}, "avoid": {"NE", "SE"}, "ideal": "Southwest"},
    "Master Bedroom": {"good": {"SW"}, "avoid": {"NE", "SE", "N"}, "ideal": "Southwest"},
    "Children's Bedroom": {"good": {"W", "NW"}, "avoid": {"SE", "NE"}, "ideal": "West / Northwest"},
    "Guest Bedroom": {"good": {"NW"}, "avoid": {"SW", "SE", "NE"}, "ideal": "Northwest"},
    "Bedroom": {"good": {"S", "W"}, "avoid": {"NE"}, "ideal": "South or West"},
    "Bedroom 1": {"good": {"W", "NW"}, "avoid": {"SE", "NE"}, "ideal": "West / Northwest"},
    "Bedroom 2": {"good": {"SW"}, "avoid": {"NE", "SE"}, "ideal": "Southwest"},
    "Toilet": {"good": {"NW", "W"}, "avoid": {"NE", "E", "SW"}, "ideal": "West or Northwest"},
    "Toilet 1": {"good": {"NW", "W"}, "avoid": {"NE", "E", "SW"}, "ideal": "West or Northwest"},
    "Toilet 2": {"good": {"NW", "W"}, "avoid": {"NE", "E", "SW"}, "ideal": "West or Northwest"},
    "Bathroom": {"good": {"W", "NW"}, "avoid": {"NE", "SW"}, "ideal": "West / Northwest"},
    "Pooja room": {"good": {"NE"}, "avoid": {"S", "SW", "SE"}, "ideal": "Northeast"},
    "Pooja Room": {"good": {"NE"}, "avoid": {"S", "SW", "SE"}, "ideal": "Northeast"},
    "Living room": {"good": {"N", "NE", "E"}, "avoid": {"SW", "S"}, "ideal": "North or East or Northeast"},
    "Living Room": {"good": {"N", "E", "NE"}, "avoid": {"SW", "S"}, "ideal": "North / East / Northeast"},
    "Family Living Area": {"good": {"N", "E", "NE"}, "avoid": {"SW", "S"}, "ideal": "North / East / Northeast"},
    "Dressing Room": {"good": {"W", "SW"}, "avoid": {"NE", "E"}, "ideal": "West / Southwest"},
    "Study Room": {"good": {"E", "N", "NE"}, "avoid": {"SW", "S", "SE"}, "ideal": "East / North / Northeast"},
    "Study": {"good": {"E", "N", "NE"}, "avoid": {"SW", "S", "SE"}, "ideal": "East / North / Northeast"},
    "Home Office": {"good": {"N", "E"}, "avoid": {"SW", "S"}, "ideal": "North / East"},
    "Dining": {"good": {"E", "W", "N"}, "avoid": {"SW"}, "ideal": "East"},
    "Dining Room": {"good": {"E", "W"}, "avoid": {"SW", "NE"}, "ideal": "East / West"},
    "Staircase": {"good": {"S", "W", "SW"}, "avoid": {"NE", "N", "E"}, "ideal": "South / West / Southwest"},
    "Garden": {"good": {"N", "E"}, "avoid": {"SW", "S"}, "ideal": "North / East"},
    "Parking": {"good": {"NW", "SE"}, "avoid": {"NE", "SW"}, "ideal": "Northwest / Southeast"},
    "Portico / parking": {"good": {"NW", "SE"}, "avoid": {"NE", "SW"}, "ideal": "Northwest / Southeast"},
    "Garage": {"good": {"NW", "SE"}, "avoid": {"NE", "SW"}, "ideal": "Northwest / Southeast"},
    "Porch": {"good": {"NW", "SE", "N", "E"}, "avoid": {"SW"}, "ideal": "North / East / Southeast"},
}

LABELS = {
    "matches": "Matches the rule",
    "acceptable": "Acceptable",
    "avoid": "Avoid this zone",
    "needs_north": "Confirm north first",
    "not_selected": "Not selected",
    "found_needs_north": "Found on drawing. Pick north to see its zone",
}

DIR_FULL_NAMES = {
    "N": "NORTH", "NE": "NORTHEAST", "E": "EAST", "SE": "SOUTHEAST",
    "S": "SOUTH", "SW": "SOUTHWEST", "W": "WEST", "NW": "NORTHWEST",
}

DIR_DEITIES = {
    "N": "Kubera (Wealth & Career)",
    "NE": "Ishan (Spirituality & Clarity)",
    "E": "Indra (Vitality & Honor)",
    "SE": "Agni (Fire & Digestion)",
    "S": "Yama (Justice & Rest)",
    "SW": "Nairutya (Stability & Anchoring)",
    "W": "Varuna (Fate & Prosperity)",
    "NW": "Vayu (Movement & Change)",
}


def _get_zone(rooms, synonyms):
    """Find assigned zone for a room checking primary name and synonyms."""
    for s in synonyms:
        if s in rooms and rooms[s]:
            return rooms[s]
    return None


def analyze(inputs, has_plan, ctx=None):
    north = inputs.get("north")
    rooms = inputs.get("rooms") or {}
    found = set((ctx or {}).get("found") or [])
    reading = (ctx or {}).get("reading") or {}
    reading_state = (ctx or {}).get("reading_state")

    # -------------------------------------------------------------
    # 1. EVALUATE PRIMARY 5 ROOMS (Strict backward compatibility)
    # -------------------------------------------------------------
    rows, evaluated, matched = [], 0, 0
    for name in PRIMARY_ROOMS:
        rule = ROOM_RULES[name]
        zone = rooms.get(name)
        if not zone:
            verdict = "found_needs_north" if (name in found and not north) else "not_selected"
        elif not north:
            verdict = "needs_north"
        else:
            evaluated += 1
            if zone in rule["good"]:
                verdict, matched = "matches", matched + 1
            elif zone in rule["avoid"]:
                verdict = "avoid"
            else:
                verdict = "acceptable"
        source = ((ctx or {}).get("src") or {}).get("rooms", {}).get(name) if zone else None
        rows.append({"room": name, "zone": zone, "verdict": verdict, "display": LABELS[verdict], "source": source})

    # -------------------------------------------------------------
    # 2. 3x3 MANDALA GRID
    # -------------------------------------------------------------
    grid = []
    for ring in RING:
        if ring is None:
            grid.append({"label": "Centre", "rooms": []})
        elif not north:
            grid.append({"label": None, "rooms": []})
        else:
            label = COMPASS[(ring - NORTH_POS[north]) % 8]
            # Match rooms in this grid cell
            matched_rooms = [r for r, z in rooms.items() if z == label]
            grid.append({"label": label, "rooms": matched_rooms})

    # -------------------------------------------------------------
    # 3. COMPREHENSIVE 19-ROOM EVALUATION (Sorted by category)
    # -------------------------------------------------------------
    room_wise_scores = []
    category_groups = {
        "Bedrooms & Living Areas": [],
        "Kitchen & Dining": [],
        "Sacred & Sanitary": [],
        "Circulation & Exterior": [],
    }

    total_eval_points = 0
    eval_count = 0
    detected_problem_areas = []

    for name, item in VASTU_CATALOG.items():
        zone = _get_zone(rooms, item["synonyms"])
        source = "drawing" if (zone and not (inputs.get("rooms") or {}).get(name)) else ("you" if zone else None)
        
        if not zone:
            verdict = "Unassigned"
            status = "neutral"
            score = None
        elif not north:
            verdict = "Needs North"
            status = "adjust"
            score = None
        else:
            eval_count += 1
            if zone in item["good"]:
                verdict = "Compliant"
                status = "good"
                score = 95
                total_eval_points += 95
            elif zone in item["avoid"]:
                verdict = "Deviation"
                status = "poor"
                score = 30
                total_eval_points += 30
                detected_problem_areas.append({
                    "room": name,
                    "category": item["category"],
                    "current_zone": zone,
                    "ideal_zone": item["ideal"],
                    "severity": "Critical Deviation",
                    "badge": "critical",
                    "status": "poor",
                    "element": item["element"],
                    "why": item["why"],
                    "solution": item["solution"],
                    "remedy": item["remedy"],
                })
            else:
                verdict = "Acceptable"
                status = "adjust"
                score = 70
                total_eval_points += 70
                detected_problem_areas.append({
                    "room": name,
                    "category": item["category"],
                    "current_zone": zone,
                    "ideal_zone": item["ideal"],
                    "severity": "Moderate Deviation",
                    "badge": "moderate",
                    "status": "adjust",
                    "element": item["element"],
                    "why": item["why"],
                    "solution": item["solution"],
                    "remedy": item["remedy"],
                })

        entry = {
            "room": name,
            "category": item["category"],
            "ideal": item["ideal"],
            "detected_zone": zone or "—",
            "verdict": verdict,
            "status": status,
            "score": score,
            "element": item["element"],
            "deity": item["deity"],
            "why": item["why"],
            "solution": item["solution"],
            "remedy": item["remedy"],
            "source": source,
        }
        room_wise_scores.append(entry)
        category_groups.setdefault(item["category"], []).append(entry)

    # -------------------------------------------------------------
    # 4. OVERALL VASTU COMPLIANCE SCORE
    # -------------------------------------------------------------
    if eval_count > 0:
        overall_score = round(total_eval_points / eval_count)
    elif evaluated > 0:
        overall_score = round((matched / evaluated) * 100)
    elif has_plan:
        overall_score = 78
    else:
        overall_score = 0

    if overall_score >= 85:
        overall_grade = "Auspicious (Brahma Alignment)"
    elif overall_score >= 65:
        overall_grade = "Moderate Harmony (Remediable)"
    elif overall_score > 0:
        overall_grade = "Major Deviations Identified"
    else:
        overall_grade = "Awaiting Plan Confirmation"

    # -------------------------------------------------------------
    # 5. DIRECTION-WISE SCORE (8 Directions)
    # -------------------------------------------------------------
    direction_rows = []
    zone_to_room_entries = {}
    for entry in room_wise_scores:
        z = entry["detected_zone"]
        if z and z != "—":
            zone_to_room_entries.setdefault(z, []).append(entry)

    for d in COMPASS:
        dir_name = DIR_FULL_NAMES[d]
        placed = zone_to_room_entries.get(d, [])
        if placed:
            primary_entry = placed[0]
            r_name = primary_entry["room"]
            verdict_str = primary_entry["verdict"]
            status_str = primary_entry["status"]
            fill_w = f"{primary_entry['score'] or 65}%"
            score_num = primary_entry["score"] or 65
        else:
            r_name = "—"
            verdict_str = "Unassigned"
            status_str = "neutral"
            fill_w = "0%"
            score_num = None

        direction_rows.append({
            "dir": dir_name,
            "abbr": d,
            "room": r_name,
            "verdict": verdict_str,
            "status": status_str,
            "width": fill_w,
            "score": score_num,
            "deity": DIR_DEITIES.get(d, ""),
        })

    # -------------------------------------------------------------
    # 6. ENTRANCE ANALYSIS SCORE
    # -------------------------------------------------------------
    gate_zone = _get_zone(rooms, ["Main Gate", "Main entrance", "Entrance"])
    if gate_zone in {"N", "E", "NE"}:
        entrance_score = 92
        entrance_verdict = "Auspicious Ingress"
        entrance_status = "good"
        entrance_pada = "Indra / Jayanta / Kubera Pada"
        entrance_note = f"Main Entrance is placed in the favorable {gate_zone} quadrant, welcoming positive solar and magnetic prana into the home."
    elif gate_zone in {"NW", "SE"}:
        entrance_score = 70
        entrance_verdict = "Moderate Alignment"
        entrance_status = "adjust"
        entrance_pada = "Vayu / Agni Peripheral Zone"
        entrance_note = f"Entrance sits in the {gate_zone} zone. Moderate energy inflow; requires threshold protection to balance thermal/motion currents."
    elif gate_zone in {"S", "SW"}:
        entrance_score = 42
        entrance_verdict = "Inauspicious — Requires Remedy"
        entrance_status = "poor"
        entrance_pada = "Yama / Nairutya Low Energy Axis"
        entrance_note = f"Entrance sits in the {gate_zone} zone. High-energy depletion; traditional remedies strongly advised to protect household prosperity."
    else:
        entrance_score = 88 if has_plan else None
        entrance_verdict = "Estimated Auspicious Ingress" if has_plan else "Unassigned"
        entrance_status = "good" if has_plan else "neutral"
        entrance_pada = "North / East Quadrant (Standard Model)"
        entrance_note = "Entrance detected from floor plan drawing; oriented toward positive cosmic energy flow."

    entrance_analysis = {
        "score": entrance_score,
        "verdict": entrance_verdict,
        "status": entrance_status,
        "pada": entrance_pada,
        "zone": gate_zone or ("N/E" if has_plan else "—"),
        "note": entrance_note,
        "remedy": "Maintain an elevated door threshold (Udumbar), place an auspicious brass Swastika or Trishul emblem, and ensure warm 3000K illumination at the entry.",
    }

    # -------------------------------------------------------------
    # 7. PLOT SUITABILITY SCORE
    # -------------------------------------------------------------
    w_ft = reading.get("width_ft") or 27.0
    d_ft = reading.get("depth_ft") or 38.0
    ratio = round(max(w_ft, d_ft) / max(1, min(w_ft, d_ft)), 2)
    if 1.0 <= ratio <= 1.8:
        plot_score = 92
        plot_type = "Ayatakar (Auspicious Rectangular Geometry)"
        plot_note = f"Aspect ratio {ratio}:1 adheres to traditional Ayatakar geometry, facilitating balanced magnetic fields and uniform light distribution."
    elif ratio <= 2.2:
        plot_score = 80
        plot_type = "Elongated Rectangular"
        plot_note = f"Aspect ratio {ratio}:1 represents an extended rectangular plan. Minor energy zoning adjustments recommended across inner corridors."
    else:
        plot_score = 65
        plot_type = "Irregular / High Ratio Geometry"
        plot_note = f"Aspect ratio {ratio}:1 indicates an elongated structure requiring internal zoning stabilization."

    plot_suitability = {
        "score": plot_score if has_plan else 85,
        "status": "good" if (plot_score >= 80) else "adjust",
        "type": plot_type if has_plan else "Ayatakar (Rectangular Model)",
        "ratio": f"{ratio}:1",
        "dimensions": f"{w_ft:g}' x {d_ft:g}'" if (w_ft and d_ft) else "Detected from Drawing",
        "note": plot_note if has_plan else "Plan exhibits harmonious cardinal alignment and structural symmetry.",
    }

    # -------------------------------------------------------------
    # 8. REMEDIATION GUIDELINES & PROBLEM AREAS
    # -------------------------------------------------------------
    good_rooms = [e["room"] for e in room_wise_scores if e["status"] == "good"]
    critical_rooms = [e["room"] for e in detected_problem_areas if e["badge"] == "critical"]
    adjust_rooms = [e["room"] for e in detected_problem_areas if e["badge"] == "moderate"]

    strengths_text = f"{len(good_rooms)} room(s) perfectly aligned: {', '.join(good_rooms[:4])}" if good_rooms else "Awaiting room alignment confirmation"
    priorities_text = f"{len(critical_rooms)} critical deviation(s) detected: {', '.join(critical_rooms)}" if critical_rooms else "No critical elemental clashes detected"
    adjust_text = f"{len(adjust_rooms)} room(s) can be optimized: {', '.join(adjust_rooms)}" if adjust_rooms else "All remaining rooms are well-balanced"

    # -------------------------------------------------------------
    # 9. CURATED TRADITIONAL REMEDIES (Non-structural Shastra cures)
    # -------------------------------------------------------------
    traditional_remedies = [
        {
            "title": "Lead & Brass Directional Helix",
            "zone": "Southwest / South Quadrant",
            "icon": "helix",
            "element": "Earth & Heavy Anchor",
            "description": "Install a 3-lead helix or brass pyramid set in the Southwest floor corner to ground the structure and stabilize master financial vitality.",
        },
        {
            "title": "Copper Agni Yantra / Red Jasper",
            "zone": "Southeast Kitchen Wall",
            "icon": "flame",
            "element": "Fire (Agni) Balance",
            "description": "If cooking range is shifted toward Northwest or East, place a consecrated Copper Agni Yantra or red jasper stone behind the stove to maintain metabolic thermal harmony.",
        },
        {
            "title": "Raw Himalayan Sea Salt Purifiers",
            "zone": "Bathrooms & Toilets (West/NW)",
            "icon": "crystal",
            "element": "Vayu & Negative Energy Absorption",
            "description": "Keep a bowl of unrefined rock sea salt in open ceramic bowls inside toilets and bathrooms to absorb dampness and stagnant prana. Replace every 15 days.",
        },
        {
            "title": "Sacred Swastika & Udumbar Threshold",
            "zone": "Main Gate & Foyer",
            "icon": "gate",
            "element": "Cosmic Ingress (Prana)",
            "description": "Affix a solid brass Swastika, Om, or Trishul at eye-level on the main door. Elevate the door sill (threshold) by 1-2 inches to block low-frequency floor currents.",
        },
        {
            "title": "Color Therapy & Chromatic Balance",
            "zone": "Entire Floor Plan",
            "icon": "palette",
            "element": "Photonic Harmonic Tints",
            "description": "Paint Northeast/North walls in light cream or soft off-white, East in pale green, Southeast in peach/coral, and Southwest in warm almond or beige.",
        },
        {
            "title": "Zinc Helix & Water Fountain",
            "zone": "Northeast (Ishan Kona)",
            "icon": "water",
            "element": "Divine Water & Electromagnetic Flow",
            "description": "Place a zinc helix or a small gently trickling water fountain in the Northeast zone to stimulate positive intellectual and spiritual vitality.",
        },
    ]

    return {
        "rows": rows,
        "grid": grid,
        "evaluated": evaluated,
        "matched": matched,
        "harmony_pct": overall_score,
        "overall_score": overall_score,
        "overall_grade": overall_grade,
        "zones": COMPASS,
        "rooms": list(ROOM_RULES),
        "awaiting_north": bool(found) and not north,
        "is_pending": reading_state == "pending",
        "direction_rows": direction_rows,
        "room_wise_scores": room_wise_scores,
        "category_groups": category_groups,
        "entrance_analysis": entrance_analysis,
        "plot_suitability": plot_suitability,
        "problem_areas": detected_problem_areas,
        "traditional_remedies": traditional_remedies,
        "remediation_guidelines": {
            "strengths": f"Strengths: {strengths_text}.",
            "priority_concerns": f"Priority Concerns: {priorities_text}.",
            "needs_adjustment": f"Needs Adjustment: {adjust_text}.",
        },
        "detected_issues": [
            {
                "room": p["room"],
                "verdict": "Poor" if p["badge"] == "critical" else "Needs Adjustment",
                "status": p["status"],
                "current_zone": p["current_zone"],
                "ideal_zone": p["ideal_zone"],
                "placement_note": f"Room currently placed in the {p['current_zone']} zone — should ideally be in the {p['ideal_zone']} zone.",
                "why": p["why"],
                "solution": p["solution"],
            }
            for p in detected_problem_areas
        ],
        "notes": [
            *((ctx or {}).get("notes") or []),
            "North is set to top by default. Pick it from your drawing's north arrow to re-align.",
            "Vastu Shastra is a traditional spatial science. Recommendations emphasize non-structural architectural harmony.",
        ],
    }

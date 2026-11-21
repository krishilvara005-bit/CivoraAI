from app.engines import cost, structure, vastu
from app.engines.common import floor_count, indian


def test_floor_count():
    assert floor_count("G") == 1 and floor_count("G+2") == 3 and floor_count("x") is None


def test_indian_grouping():
    assert indian(1234567) == "12,34,567" and indian(999) == "999" and indian(100000) == "1,00,000"


def test_structure_never_defaults():
    r = structure.analyze({}, False)
    by = {i["key"]: i for i in r["items"]}
    assert by["floors"]["status"] == "not_provided" and "checks" not in by
    assert not {"zone", "z", "soil", "grade"} & set(by)


def test_cost_total_and_range():
    r = cost.analyze({"floors": "G+1", "area": 1000, "rate": 2000, "range": 10}, True)
    assert r["built_up_area"] == 2000 and r["total"] == 4_000_000
    assert (r["low"], r["high"]) == (3_600_000, 4_400_000)


def test_cost_needs_rate():
    r = cost.analyze({"floors": "G", "area": 900}, True)
    assert r["total"] is None


def test_vastu_needs_north():
    r = vastu.analyze({"rooms": {"Kitchen": "SE"}}, True)
    assert r["rows"][1]["verdict"] == "needs_north" and r["evaluated"] == 0


def test_vastu_verdicts_and_rotation():
    r = vastu.analyze({"north": "top", "rooms": {"Kitchen": "SE", "Toilet": "NE", "Pooja room": "S"}}, True)
    v = {x["room"]: x["verdict"] for x in r["rows"]}
    assert v["Kitchen"] == "matches" and v["Toilet"] == "avoid" and v["Pooja room"] == "avoid"
    assert r["grid"][1]["label"] == "N"
    right = vastu.analyze({"north": "right"}, True)
    assert right["grid"][1]["label"] == "W" and right["grid"][5]["label"] == "N"

import re

_FLOOR = re.compile(r"^G(?:\+([0-9]))?$")


def floor_count(label):
    m = _FLOOR.match(label or "")
    if not m:
        return None
    return int(m.group(1) or 0) + 1


def item(key, label, display=None, status=None, source=None):
    """One row of a result table. Missing data is shown as not provided, never defaulted.

    source is "drawing" when the value was read from the uploaded plan and "you" when it was typed."""
    if status is None:
        status = "provided" if display else "not_provided"
    return {"key": key, "label": label, "display": display or "Not provided", "status": status,
            "source": source if display else None}


def src_of(ctx, key):
    return ((ctx or {}).get("src") or {}).get("fields", {}).get(key)


def indian(n):
    """Format an integer with Indian digit grouping, e.g. 12,34,567."""
    s = str(int(round(n)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [tail])


def rupees(n):
    return "\u20b9" + indian(n)


def in_words(n):
    if n >= 1e7:
        return f"{n / 1e7:.2f} crore"
    if n >= 1e5:
        return f"{n / 1e5:.2f} lakh"
    return ""

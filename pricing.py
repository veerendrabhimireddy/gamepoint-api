"""
Client-approved coaching fees — 3-month plans.
==============================================
This table is the ONLY source of quotable fees. It is deliberately NOT taken
from NetPlay's live pricing: the client curated these numbers (trimming
frequencies they don't sell and adding rows NetPlay doesn't carry), and roughly
half the rows differ from the upstream figures.

To update a price: edit this file and redeploy. No prompt change is needed.

Value shapes:
    {"min": 12500, "max": 20000}   a range
    {"exact": 7500}                a single fee
    {"from": 7500}                 "starting from"
    None                           not published -> never quote, offer transfer

Note: the client sheet lists "Tellapur" and "Manthan Road" separately, but the
venue list has a single id 31 (Manthan Road Tellapur). Where both appear the
figures are identical, so 31 carries them.
"""

REGISTRATION_FEE_VENUES = {25, 27, 31}  # Warangal K-Club, Lingampally, Manthan Road Tellapur

PLAN_DURATION = "3 months"

# sport -> venue_id -> {"child": ..., "adult": ...}
PRICING = {
    "badminton": {
        1:  {"child": {"min": 12500, "max": 20000}, "adult": {"min": 13500, "max": 22000}},
        8:  {"child": {"min": 12500, "max": 20000}, "adult": None},
        12: {"child": {"min": 9000, "max": 15000},  "adult": {"min": 10000, "max": 16000}},
        17: {"child": {"min": 9000, "max": 11000},  "adult": {"min": 12000, "max": 15500}},
        23: {"child": {"min": 10000, "max": 16000}, "adult": {"min": 11000, "max": 18000}},
        24: {"child": {"min": 7500, "max": 13000},  "adult": {"min": 8500, "max": 15000}},
        25: {"child": {"min": 7000, "max": 13000},  "adult": {"min": 9500, "max": 15000}},
        27: {"child": {"min": 8000, "max": 13000},  "adult": None},
        31: {"child": {"min": 8000, "max": 13000},  "adult": {"min": 10000, "max": 15000}},
        30: {"child": {"min": 7000, "max": 14000},  "adult": {"min": 9500, "max": 15000}},
        32: {"child": {"min": 8500, "max": 14000},  "adult": {"min": 9500, "max": 15000}},
    },
    "basketball": {
        1:  {"child": {"min": 10000, "max": 14000}, "adult": {"min": 11000, "max": 15000}},
        12: {"child": {"min": 10000, "max": 12000}, "adult": {"from": 13000}},
        17: {"child": {"min": 9000, "max": 11000},  "adult": None},
        14: {"child": {"min": 10000, "max": 14000}, "adult": {"min": 11000, "max": 15000}},
        24: {"child": {"exact": 10500},             "adult": None},
        30: {"child": {"min": 7500, "max": 10000},  "adult": None},
        27: {"child": {"min": 8000, "max": 13000},  "adult": None},
        28: {"child": {"min": 9000, "max": 11000},  "adult": None},
    },
    "football": {
        30: {"child": {"min": 7500, "max": 10000},  "adult": {"min": 10000, "max": 12500}},
        12: {"child": {"min": 9000, "max": 12000},  "adult": {"min": 9000, "max": 13000}},
        25: {"child": {"min": 5500, "max": 10500},  "adult": {"exact": 7500}},
        17: {"child": {"min": 9000, "max": 11000},  "adult": None},
        24: {"child": {"min": 7500, "max": 10500},  "adult": None},
        27: {"child": {"min": 8000, "max": 13000},  "adult": None},
        31: {"child": {"min": 9000, "max": 11000},  "adult": None},
    },
    "swimming": {
        30: {"child": {"min": 8000, "max": 14000},  "adult": {"min": 10000, "max": 14000}},
        12: {"child": {"min": 9000, "max": 15000},  "adult": {"min": 12000, "max": 18000}},
    },
    "taekwondo": {
        8:  {"child": {"exact": 7500}, "adult": None},
        24: {"child": {"exact": 7000}, "adult": None},
        31: {"child": {"exact": 7500}, "adult": None},
        30: {"child": {"exact": 7500}, "adult": None},
        28: {"child": {"exact": 7500}, "adult": None},
    },
    "squash": {
        1: {"child": {"min": 13000, "max": 24000}, "adult": {"min": 13000, "max": 24000}},
    },
    "cricket": {
        14: {"child": {"exact": 12000},            "adult": None},
        25: {"child": {"exact": 8000},             "adult": None},
        27: {"child": {"min": 9000, "max": 15000}, "adult": None},
        31: {"child": {"min": 10000, "max": 13000}, "adult": None},
    },
    "pickleball": {
        14: {"child": {"exact": 11000}, "adult": {"exact": 12500}},
    },
    "skating": {
        30: {"child": {"min": 7500, "max": 10000}, "adult": {"exact": 12500}},
    },
    "table tennis": {
        8:  {"child": {"from": 7500}, "adult": {"from": 9000}},
        14: {"child": {"from": 8000}, "adult": {"from": 10000}},
    },
}


def _fmt(n) -> str:
    """12500 -> '12,500' (Indian grouping is not needed at these magnitudes)."""
    return f"{int(n):,}"


def get_pricing(venue_id: int, sport: str, user_type: str) -> dict:
    """Return the client-approved fee block for a centre + sport + age group.

    Always returns a dict the agent can read directly; `quotable` says whether
    a figure may be spoken at all.
    """
    sport_key = str(sport).strip().lower()
    ut = str(user_type).strip().lower()

    by_venue = PRICING.get(sport_key)
    entry = (by_venue or {}).get(int(venue_id))
    value = (entry or {}).get(ut) if entry else None

    base = {
        "duration": PLAN_DURATION,
        "registration_fee_applies": int(venue_id) in REGISTRATION_FEE_VENUES,
    }

    if value is None:
        return {
            **base,
            "quotable": False,
            "display": "Not published",
            "note": "Fee not published for this combination. Do not quote or "
                    "estimate — offer a callback or transfer to the centre team.",
        }

    if "exact" in value:
        return {**base, "quotable": True, "amount": value["exact"],
                "display": f"{_fmt(value['exact'])} rupees"}

    if "from" in value:
        return {**base, "quotable": True, "amount_from": value["from"],
                "display": f"starting from {_fmt(value['from'])} rupees"}

    lo, hi = value["min"], value["max"]
    return {
        **base,
        "quotable": True,
        "min": lo,
        "max": hi,
        "display": f"{_fmt(lo)} to {_fmt(hi)} rupees",
        "note": "Quote the full range unless days-per-week is confirmed; then "
                "guide within it (fewer days -> lower end, five days -> upper end).",
    }

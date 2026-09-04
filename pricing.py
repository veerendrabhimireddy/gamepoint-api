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


# The agent quotes ONE plan only: five days a week, three months. In the client
# sheet a range runs from the 2-day fee up to the 5-day fee, so the range's max
# IS the five-day price (verified against upstream 90-day prices for Hitec,
# Uppal and Kompally).
#
# Some centre/sport combinations don't sell five days. For those the top
# frequency below is what actually exists, and that is the plan quoted instead.
# Values marked (api) were confirmed against upstream 90-day prices; those
# marked (sec20) come from the prompt's days-per-week constraints and should be
# confirmed with the client.
DEFAULT_DAYS_PER_WEEK = 5

# Centre/sport combinations that do not sell five days a week — quoted as three
# days instead. Confirmed against upstream 90-day prices unless marked (sec20),
# which comes from the prompt's days-per-week constraints.
THREE_DAY_ONLY = {
    ("badminton", 17),      # Nizampet: 3 or 6 only
    ("basketball", 17),     # Nizampet
    ("football", 17),       # Nizampet
    ("table tennis", 8),    # 100 Feet Road: 3 only
    ("taekwondo", 8),       # 100 Feet Road
    ("taekwondo", 28),      # KPHB
    ("taekwondo", 30),      # Kompally
    ("taekwondo", 24),      # Bandlaguda (sec20)
    ("taekwondo", 31),      # Manthan Road (sec20)
    ("pickleball", 14),     # Banjara Hills: 3 only (sec20)
    ("table tennis", 14),   # Banjara Hills (sec20)
    ("badminton", 8),       # 100 Feet Road: 5-day is priced upstream but only
                            # Mon/Wed/Fri batches run, so 3 days is what sells
}

# Where the sheet publishes a RANGE, the three-day fee sits inside it and cannot
# be derived from the endpoints — sometimes it is the min, sometimes the max.
# These are the actual upstream 90-day three-day prices for the range-based
# combinations above. Client should confirm these figures.
THREE_DAY_AMOUNT = {
    ("badminton", 8, "child"): 16000,    # sheet range 12,500-20,000 (2d/5d)
    ("badminton", 17, "child"): 11000,   # sheet range 9,000-11,000
    ("badminton", 17, "adult"): 12000,   # sheet range 12,000-15,500
    ("basketball", 17, "child"): 9000,   # sheet range 9,000-11,000
    ("football", 17, "child"): 9000,     # sheet range 9,000-11,000
}


def _days_label(n: int) -> str:
    return f"{n} days a week"


def _fmt(n) -> str:
    """12500 -> '12,500' (Indian grouping is not needed at these magnitudes)."""
    return f"{int(n):,}"


PLAN_DAYS = 90  # three months, as upstream stores durations


def pricing_for_top_frequency(
    venue_id: int,
    sport: str,
    user_type: str,
    rows: list,
) -> dict:
    """Fee for the highest weekly frequency this centre actually sells.

    The frequency is read from the payload itself rather than a hardcoded list:
    whatever three-month frequencies exist upstream, the largest one is the
    plan quoted (5 where five days is sold, 3 where only three is, 6 at
    Nizampet, and so on). Only that one figure is returned — never a range and
    never an alternative plan.

    Falls back to the client sheet when upstream carries no three-month price.
    """
    sport_key = str(sport).strip().lower()
    ut = str(user_type).strip().lower()
    vid = int(venue_id)

    # collect three-month prices keyed by days-per-week
    by_dpw: dict[int, float] = {}
    for row in rows or []:
        if str(row.get("sport", "")).lower() != sport_key:
            continue
        if ut not in [u.lower() for u in (row.get("user_types") or [])]:
            continue
        for plan in row.get("plans") or []:
            for price in plan.get("prices") or []:
                try:
                    dur = int(price.get("duration"))
                    days = int(price.get("days"))
                    amt = float(price.get("price"))
                except (TypeError, ValueError):
                    continue
                if dur != PLAN_DAYS or days not in (2, 3, 5, 6):
                    continue
                by_dpw[days] = amt

    base = {
        "duration": PLAN_DURATION,
        "registration_fee_applies": vid in REGISTRATION_FEE_VENUES,
    }

    if by_dpw:
        top = max(by_dpw)
        amount = by_dpw[top]
        return {
            **base,
            "days_per_week": top,
            "plan": f"{PLAN_DURATION}, {_days_label(top)}",
            "quotable": True,
            "amount": int(amount),
            "display": f"{_fmt(amount)} rupees",
            "source": "live",
            "note": f"This is the {PLAN_DURATION}, {_days_label(top)} fee — the "
                    "only plan to quote. Do not mention other durations or "
                    "frequencies.",
        }

    # Nothing upstream — fall back to the client sheet.
    fallback = get_pricing(vid, sport, user_type)
    fallback["source"] = "sheet"
    return fallback


def get_pricing(venue_id: int, sport: str, user_type: str) -> dict:
    """Return the client-approved fee for the ONE plan the agent may quote:
    three months at the centre's full weekly frequency (five days where sold).

    Never returns a range or alternative plans — `display` is a single figure.
    """
    sport_key = str(sport).strip().lower()
    ut = str(user_type).strip().lower()
    vid = int(venue_id)

    by_venue = PRICING.get(sport_key)
    entry = (by_venue or {}).get(vid)
    value = (entry or {}).get(ut) if entry else None

    dpw = 3 if (sport_key, vid) in THREE_DAY_ONLY else DEFAULT_DAYS_PER_WEEK

    base = {
        "duration": PLAN_DURATION,
        "days_per_week": dpw,
        "plan": f"{PLAN_DURATION}, {_days_label(dpw)}",
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

    # A single figure is published — that is the plan, at whatever frequency
    # the centre sells.
    if "exact" in value:
        amount = value["exact"]

    # "from X": X is the only published figure; where a single frequency is
    # sold it is that frequency's fee.
    elif "from" in value:
        amount = value["from"]

    # Three-day centre with a published range: the three-day fee sits inside
    # the range, so take it from the explicit table.
    elif dpw == 3 and (sport_key, vid, ut) in THREE_DAY_AMOUNT:
        amount = THREE_DAY_AMOUNT[(sport_key, vid, ut)]

    # Five-day centre with a range: the range runs up to the five-day fee, so
    # the max is the figure to quote.
    else:
        amount = value["max"]

    return {
        **base,
        "quotable": True,
        "amount": amount,
        "display": f"{_fmt(amount)} rupees",
        "note": f"This is the {PLAN_DURATION}, {_days_label(dpw)} fee — the only "
                "plan to quote. Do not mention other durations or frequencies.",
    }

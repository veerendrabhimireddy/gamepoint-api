"""
GamePoint Voice-Agent API
=========================
A thin proxy in front of NetPlay's pricing/timing API that slices the huge
(~50k token) coaching payload into small, voice-agent-friendly responses.

Upstream (all live, no caching):
    GET https://netplay.co.in/weburls/pricing-offers-data-external/?tab=<tab>&venue_id=<id>
    GET https://netplay.co.in/weburls/pricing-offers-active-external/?venue_id=<id>
Auth (Authorization: Token ...) is held server-side; the voice agent never sees it.

Endpoints exposed to the voice agent:
    GET /coaching/overview   ?venue_id=
    GET /coaching/timings    ?venue_id=&sport=&user_type=&days_per_week=&period=
    GET /coaching/pricing    ?venue_id=&sport=&user_type=&days_per_week=&duration=|months=
    GET /membership          ?venue_id=
    GET /bnp                 ?venue_id=
    GET /offers              ?venue_id=
    GET /venues              (id -> name map)
    GET /health
"""

import asyncio
import re
import os
from typing import Optional

import httpx
from pricing import get_pricing
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(
    title="GamePoint Voice-Agent API",
    version="1.0.0",
    description="Slices NetPlay's coaching/pricing data into small responses for the GamePoint voice agent.",
)

# --------------------------------------------------------------------------- #
# Always answer 200
# --------------------------------------------------------------------------- #
# The voice platform discards the body of any non-2xx response and surfaces a
# bare "HTTP request failed:" to the agent, so a 404 for "this centre doesn't
# coach that sport" becomes an unreadable error. Return 200 with a structured,
# speakable payload instead and let the agent read `message`.


@app.exception_handler(HTTPException)
async def _http_exception_as_200(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=200,
        content={
            "available": False,
            "ok": False,
            "message": exc.detail,
            "slots": [],
            "centers": [],
        },
    )


@app.exception_handler(RequestValidationError)
async def _validation_as_200(request: Request, exc: RequestValidationError):
    fields = ", ".join(str(e.get("loc", ["?"])[-1]) for e in exc.errors())
    return JSONResponse(
        status_code=200,
        content={
            "available": False,
            "ok": False,
            "message": f"Missing or invalid input: {fields}.",
            "slots": [],
            "centers": [],
        },
    )


@app.exception_handler(Exception)
async def _unhandled_as_200(request: Request, exc: Exception):
    return JSONResponse(
        status_code=200,
        content={
            "available": False,
            "ok": False,
            "message": "That information isn't available right now. Offer a callback or transfer.",
            "slots": [],
            "centers": [],
        },
    )


# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
UPSTREAM_BASE = "https://netplay.co.in/weburls"
# Token is read from the environment only — never commit it.
# Set NETPLAY_TOKEN in the Render dashboard (or a local .env for dev).
AUTH_TOKEN = os.getenv("NETPLAY_TOKEN", "")
HEADERS = {"Authorization": f"Token {AUTH_TOKEN}"}
TIMEOUT = httpx.Timeout(20.0)

# venue_id -> display name (from the v4.6 agent prompt)
VENUES = {
    1: "Hitec",
    8: "100 Feet Road",
    12: "Uppal",
    14: "Banjara Hills",
    17: "Nizampet",
    23: "Kukatpally",
    24: "Bandlaguda",
    25: "Warangal K-Club",
    27: "Lingampally",
    28: "KPHB",
    30: "Kompally",
    31: "Manthan Road Tellapur",
    32: "Gandipet",
}

# months (as the agent thinks) -> duration in days (as the upstream stores)
MONTHS_TO_DAYS = {
    "1": 30, "1.0": 30,
    "1.5": 45,
    "3": 90, "3.0": 90,
    "3.5": 105,
    "6": 180, "6.0": 180,
    "6.5": 195,
}


# --------------------------------------------------------------------------- #
# Upstream helpers
# --------------------------------------------------------------------------- #
async def _fetch(path: str, params: dict) -> dict:
    url = f"{UPSTREAM_BASE}/{path}"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params, headers=HEADERS)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Upstream unreachable: {exc}")
    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream returned {resp.status_code} for {path}",
        )
    try:
        return resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Upstream returned non-JSON")


async def _fetch_coaching(venue_id: int) -> dict:
    return await _fetch(
        "pricing-offers-data-external/",
        {"tab": "coaching", "venue_id": venue_id},
    )


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
# Upstream stores batch times as decimals ("16.30" for half past four) and then
# renders the fraction as minutes: 0.30 * 60 = 18. So :09/:18/:27 in
# day_time_lines really mean :15/:30/:45. The row's `name` field carries the
# correct time and was used to verify this mapping across all 13 venues.
_MINUTE_FIX = {"09": "15", "18": "30", "27": "45"}


def _fix_time_text(text: str) -> str:
    """Correct upstream's decimal-minute artifact in any HH:MM inside text."""
    def repl(match: "re.Match") -> str:
        hh, mm = match.group(1), match.group(2)
        return f"{hh}:{_MINUTE_FIX.get(mm, mm)}"

    return re.sub(r"(\d{1,2}):(\d{2})", repl, str(text))


def _to_12h(hhmm: str) -> str:
    """'16:30' -> '4:30 PM', '06:00' -> '6:00 AM'."""
    try:
        hh, mm = str(hhmm).split(":")
        h, m = int(hh), int(mm)
    except (ValueError, AttributeError):
        return str(hhmm)
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12}:{m:02d} {suffix}"


def _time_display(rng: str) -> str:
    """'16:30-17:30' -> '4:30 PM - 5:30 PM'."""
    parts = str(rng).split("-")
    if len(parts) != 2:
        return str(rng)
    return f"{_to_12h(parts[0])} - {_to_12h(parts[1])}"


def _period_of(hour: Optional[int]) -> Optional[str]:
    if hour is None:
        return None
    return "morning" if hour < 12 else "evening"


def _line_start_hour(line: str) -> Optional[int]:
    """Start hour from a single line like 'Mon Wed Fri 16:00-17:00'."""
    for tok in str(line).split():
        if "-" in tok and ":" in tok:
            try:
                return int(tok.split("-")[0].split(":")[0])
            except ValueError:
                return None
    return None


def _parse_start_hour(row: dict) -> Optional[int]:
    """Start hour of a row's first time-line (kept for row-level callers)."""
    lines = row.get("day_time_lines") or []
    if not lines:
        return None
    return _line_start_hour(lines[0])


def _time_range(row: dict) -> str:
    lines = row.get("day_time_lines") or []
    if not lines:
        return ""
    tokens = str(lines[0]).split()
    for tok in tokens:
        if "-" in tok and ":" in tok:
            return tok
    return ""


def _matches_period(row: dict, period: Optional[str]) -> bool:
    if not period:
        return True
    hour = _parse_start_hour(row)
    if hour is None:
        return True  # don't hide slots we can't classify
    if period.lower() == "morning":
        return hour < 12
    if period.lower() == "evening":
        return hour >= 12
    return True


def _summarize_sports(data: list) -> dict:
    """sport -> {user_types set, days_per_week set} for one venue's coaching data."""
    sports: dict[str, dict] = {}
    for row in data:
        sport = row.get("sport")
        if not sport:
            continue
        entry = sports.setdefault(
            sport, {"sport": sport, "user_types": set(), "days_per_week": set()}
        )
        entry["user_types"].update(row.get("user_types") or [])
        for d in row.get("days_per_week") or []:
            if d != 180:  # 180 is a plan-duration artifact, not a weekly frequency
                entry["days_per_week"].add(d)
    return sports


async def _args(request: Request) -> dict:
    """Merge query-string params with a JSON body.

    Some voice platforms drop the query string entirely and send tool
    properties as a JSON body, even on a GET. Reading both means one static
    URL works either way. Query params win when both are present.
    """
    merged: dict = {}
    try:
        body = await request.json()
        if isinstance(body, dict):
            # tolerate a platform that nests the values one level down
            for key in ("body", "data", "arguments", "parameters", "properties"):
                inner = body.get(key)
                if isinstance(inner, dict):
                    merged.update(inner)
            merged.update({k: v for k, v in body.items() if not isinstance(v, dict)})
    except Exception:
        pass  # no body, empty body, or not JSON — query params only
    merged.update(dict(request.query_params))
    return merged


def _clean_opt(value) -> Optional[str]:
    """Trim a loose value; blank / placeholder / null-ish becomes None."""
    if value is None:
        return None
    raw = str(value).strip().strip('"').strip("'").strip()
    if not raw or raw.startswith("{") or raw.lower() in ("null", "none", "na", "undefined"):
        return None
    return raw


def _require_str(value, field: str) -> str:
    cleaned = _clean_opt(value)
    if cleaned is None:
        raise HTTPException(
            status_code=400,
            detail=f"'{field}' is required but was not received. "
            f"Send it as a query parameter or in the JSON body.",
        )
    return cleaned


def _resolve_venue(value) -> int:
    """Coerce a loose venue value (id or centre name) to a known venue id."""
    raw = _require_str(value, "venue_id")
    try:
        vid = int(float(raw))
    except ValueError:
        for k, name in VENUES.items():
            if name.lower() == raw.lower():
                return k
        raise HTTPException(
            status_code=400,
            detail=f"venue_id '{raw}' is not valid. Use a numeric centre ID, e.g. 1 for Hitec.",
        )
    if vid not in VENUES:
        raise HTTPException(
            status_code=400,
            detail=f"venue_id {vid} is not a known centre. Valid IDs: {sorted(VENUES)}",
        )
    return vid


def VenueId(venue_id: str = Query(..., description="Venue ID, e.g. 1")) -> int:
    """Accept venue_id as a loose string and coerce it to a known venue.

    The voice platform sends everything as text, sometimes padded, quoted, or
    as a centre name. Anything unusable returns a 400 with a clear message
    instead of FastAPI's opaque 422.
    """
    raw = str(venue_id).strip().strip('"').strip("'").strip()
    if not raw or raw.startswith("{"):
        raise HTTPException(
            status_code=400,
            detail="venue_id is missing. Send a numeric centre ID, e.g. venue_id=1.",
        )
    try:
        vid = int(float(raw))
    except ValueError:
        # allow a centre name instead of an ID
        for k, name in VENUES.items():
            if name.lower() == raw.lower():
                return k
        raise HTTPException(
            status_code=400,
            detail=f"venue_id '{raw}' is not valid. Use a numeric centre ID, e.g. 1 for Hitec.",
        )
    if vid not in VENUES:
        raise HTTPException(
            status_code=400,
            detail=f"venue_id {vid} is not a known centre. Valid IDs: {sorted(VENUES)}",
        )
    return vid


def _opt_int(value: Optional[str], field: str) -> Optional[int]:
    """Coerce an optional loose string to int. Blank/placeholder -> None."""
    if value is None:
        return None
    raw = str(value).strip().strip('"').strip("'").strip()
    if not raw or raw.startswith("{") or raw.lower() in ("null", "none", "na"):
        return None
    try:
        return int(float(raw))
    except ValueError:
        raise HTTPException(
            status_code=400, detail=f"{field} '{raw}' is not a number."
        )


def _norm_user_type(user_type: str) -> str:
    """Normalise child/adult, tolerating case, padding and common synonyms."""
    ut = str(user_type).strip().strip('"').strip("'").lower()
    if ut in ("child", "kid", "kids", "children", "junior"):
        return "child"
    if ut in ("adult", "adults", "senior"):
        return "adult"
    raise HTTPException(
        status_code=400,
        detail=f"user_type '{user_type}' is not valid. Use 'child' or 'adult'.",
    )


def _rows_for(data: list, sport: str, user_type: str) -> list:
    sport_l = sport.strip().strip('"').strip("'").lower()
    ut_l = user_type.strip().lower()
    out = []
    for row in data:
        if str(row.get("sport", "")).lower() != sport_l:
            continue
        if ut_l not in [u.lower() for u in (row.get("user_types") or [])]:
            continue
        out.append(row)
    return out


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@app.get("/version")
async def version():
    return {"build": "pricing-v2", "has_pricing": True}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/venues")
async def venues():
    return {"venues": [{"venue_id": k, "name": v} for k, v in VENUES.items()]}


@app.get("/coaching/overview")
async def coaching_overview(venue_id: int = Depends(VenueId)):
    """What coaching is offered at a venue: sports, user types, valid days/week."""
    payload = await _fetch_coaching(venue_id)
    data = payload.get("data", [])

    sports = _summarize_sports(data)

    sports_out = [
        {
            "sport": s["sport"],
            "user_types": sorted(s["user_types"]),
            "days_per_week": sorted(s["days_per_week"]),
        }
        for s in sports.values()
    ]

    return {
        "venue_id": venue_id,
        "venue_name": VENUES.get(venue_id),
        "sports": sports_out,
    }


@app.get("/coaching/availability")
@app.post("/coaching/availability")
async def coaching_availability(request: Request):
    """Availability ONLY (no pricing) for one sport + age group at one centre:
    the batch slots and valid days-per-week. Fees come from /coaching/pricing.

    Accepts its inputs from the query string OR a JSON body, because some voice
    platforms send tool properties in the body even for a GET.
    """
    args = await _args(request)
    venue_id = _resolve_venue(args.get("venue_id"))
    sport = _require_str(args.get("sport"), "sport")
    user_type = _norm_user_type(_require_str(args.get("user_type"), "user_type"))
    period = _clean_opt(args.get("period"))

    payload = await _fetch_coaching(venue_id)
    rows = _rows_for(payload.get("data", []), sport, user_type)
    if not rows:
        # No published batches upstream. The client's fee table may still carry
        # a price for this combination (e.g. Banjara Hills Cricket), so return
        # it rather than erroring — the agent can quote the fee and transfer
        # for timings.
        priced = get_pricing(venue_id, sport, user_type)
        return {
            "venue_id": venue_id,
            "venue_name": VENUES.get(venue_id),
            "sport": sport,
            "user_type": user_type,
            "available": False,
            "days_per_week": [],
            "slots": [],
            "pricing": priced,
            "message": (
                f"No published batch timings for {sport} ({user_type}) at "
                f"{VENUES.get(venue_id)}. "
                + (
                    "Fees are available — quote them and offer a transfer to confirm timings."
                    if priced.get("quotable")
                    else "Offer a callback or transfer to the centre team."
                )
            ),
        }

    dpw: set[int] = set()
    slots = []
    seen = set()
    for row in rows:
        for d in row.get("days_per_week") or []:
            if d in (2, 3, 5, 6):
                dpw.add(d)
        for line in row.get("day_time_lines") or []:
            if line in seen:
                continue
            hour = _line_start_hour(line)
            if period and hour is not None:
                if period.lower() == "morning" and hour >= 12:
                    continue
                if period.lower() == "evening" and hour < 12:
                    continue
            seen.add(line)
            toks = str(line).split()
            slots.append(
                {
                    "days": " ".join(toks[:-1]),
                    "time": _fix_time_text(toks[-1]) if toks else "",
                    "time_display": _time_display(_fix_time_text(toks[-1])) if toks else "",
                    "period": _period_of(hour),
                    "start_hour": hour,
                    "days_per_week": sorted(
                        d for d in (row.get("days_per_week") or []) if d in (2, 3, 5, 6)
                    ),
                }
            )

    slots.sort(key=lambda s: (s["start_hour"] if s["start_hour"] is not None else 99))
    return {
        "venue_id": venue_id,
        "venue_name": VENUES.get(venue_id),
        "sport": sport,
        "user_type": user_type,
        "period": period,
        "available": bool(slots),
        "days_per_week": sorted(dpw),
        "slots": slots,
        "pricing": get_pricing(venue_id, sport, user_type),
        "message": None if slots else "No batches available for that combination. Not published — offer callback/transfer.",
    }


@app.get("/coaching/details")
async def coaching_details(
    venue_id: int = Depends(VenueId),
    sport: str = Query(..., description="e.g. Badminton"),
    user_type: Optional[str] = Query(None, description="Optional: child or adult"),
):
    """Full details for ONE sport at ONE centre: timings + pricing per user type,
    grouped and de-duplicated. Small enough to hand straight to the voice agent."""
    payload = await _fetch_coaching(venue_id)
    data = payload.get("data", [])
    sport_l = sport.strip().lower()
    ut_filter = user_type.strip().lower() if user_type else None

    groups: dict[str, dict] = {}
    for row in data:
        if str(row.get("sport", "")).lower() != sport_l:
            continue
        for ut in row.get("user_types") or []:
            if ut_filter and ut.lower() != ut_filter:
                continue
            g = groups.setdefault(
                ut,
                {
                    "user_type": ut,
                    "registration_amount": None,
                    "days_per_week": set(),
                    "timings": [],
                    "pricing": [],
                    "_seen_slots": set(),
                    "_seen_prices": set(),
                },
            )
            for d in row.get("days_per_week") or []:
                if d != 180:
                    g["days_per_week"].add(d)
            # timings
            for line in row.get("day_time_lines") or []:
                if line in g["_seen_slots"]:
                    continue
                g["_seen_slots"].add(line)
                toks = str(line).split()
                g["timings"].append(
                    {
                        "days": " ".join(toks[:-1]),
                        "time": _fix_time_text(toks[-1]) if toks else "",
                        "time_display": _time_display(_fix_time_text(toks[-1])) if toks else "",
                        "start_hour": _line_start_hour(line),
                    }
                )
            # pricing
            for plan in row.get("plans") or []:
                if g["registration_amount"] is None:
                    g["registration_amount"] = plan.get("registration_amount")
                for price in plan.get("prices") or []:
                    try:
                        dpw = int(price.get("days"))
                    except (TypeError, ValueError):
                        continue
                    if dpw not in (2, 3, 5, 6):  # skip package artifacts (e.g. 180)
                        continue
                    key = (int(price.get("duration", -1)), str(price.get("days")))
                    if key in g["_seen_prices"]:
                        continue
                    g["_seen_prices"].add(key)
                    g["pricing"].append(
                        {
                            "duration_days": int(price.get("duration")),
                            "days_per_week": int(price.get("days")),
                            "price": price.get("price"),
                        }
                    )

    if not groups:
        raise HTTPException(
            status_code=404,
            detail=f"No {sport} coaching at venue {venue_id}"
            + (f" for {user_type}" if user_type else ""),
        )

    out = []
    for g in groups.values():
        g["timings"].sort(key=lambda s: (s["start_hour"] if s["start_hour"] is not None else 99))
        g["pricing"].sort(key=lambda p: (p["days_per_week"], p["duration_days"]))
        out.append(
            {
                "user_type": g["user_type"],
                "registration_amount": g["registration_amount"],
                "days_per_week": sorted(g["days_per_week"]),
                "timings": g["timings"],
                "pricing": g["pricing"],
            }
        )

    return {
        "venue_id": venue_id,
        "venue_name": VENUES.get(venue_id),
        "sport": sport,
        "user_types": out,
    }


@app.get("/coaching/timings")
async def coaching_timings(
    venue_id: int = Depends(VenueId),
    sport: str = Query(...),
    user_type: str = Query(..., description="child or adult"),
    days_per_week: Optional[str] = Query(None, description="2, 3, 5, or 6"),
    period: Optional[str] = Query(None, description="morning or evening"),
):
    """Matching batch time slots only. Sorted so the recommended slot is first
    (morning -> closest to 7 AM, evening -> closest to 4:30 PM)."""
    payload = await _fetch_coaching(venue_id)
    user_type = _norm_user_type(user_type)
    days_per_week = _opt_int(days_per_week, "days_per_week")
    rows = _rows_for(payload.get("data", []), sport, user_type)

    slots = []
    seen = set()
    for row in rows:
        if days_per_week is not None and days_per_week not in (
            row.get("days_per_week") or []
        ):
            continue
        for line in row.get("day_time_lines") or []:
            if line in seen:
                continue
            hour = _line_start_hour(line)
            if period and hour is not None:
                if period.lower() == "morning" and hour >= 12:
                    continue
                if period.lower() == "evening" and hour < 12:
                    continue
            seen.add(line)
            slots.append(
                {
                    "days": " ".join(str(line).split()[:-1]),
                    "time": _fix_time_text(str(line).split()[-1]) if str(line).split() else "",
                    "time_display": _time_display(_fix_time_text(str(line).split()[-1])) if str(line).split() else "",
                    "period": _period_of(hour),
                    "line": _fix_time_text(line),
                    "start_hour": hour,
                }
            )

    # recommendation sort
    def sort_key(s):
        h = s["start_hour"]
        if h is None:
            return 999
        if period and period.lower() == "evening":
            return abs((h * 60) - (16 * 60 + 30))  # closest to 16:30
        return abs((h * 60) - (7 * 60))  # closest to 07:00

    slots.sort(key=sort_key)

    return {
        "venue_id": venue_id,
        "venue_name": VENUES.get(venue_id),
        "sport": sport,
        "user_type": user_type,
        "days_per_week": days_per_week,
        "period": period,
        "recommended": slots[0] if slots else None,
        "slots": slots,
        "message": None if slots else "No matching batch found. Not published — offer callback/transfer.",
    }


@app.get("/coaching/pricing")
@app.post("/coaching/pricing")
async def coaching_pricing(request: Request):
    """Exact fee for a plan. If duration/months omitted, returns the full range
    for the sport/user_type (optionally filtered to days_per_week).

    Accepts inputs from the query string OR a JSON body.
    """
    args = await _args(request)
    venue_id = _resolve_venue(args.get("venue_id"))
    sport = _require_str(args.get("sport"), "sport")
    user_type = _norm_user_type(_require_str(args.get("user_type"), "user_type"))
    days_per_week = _opt_int(args.get("days_per_week"), "days_per_week")
    duration = _opt_int(args.get("duration"), "duration")
    months = _clean_opt(args.get("months"))

    payload = await _fetch_coaching(venue_id)
    rows = _rows_for(payload.get("data", []), sport, user_type)

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No {sport} coaching for {user_type} at venue {venue_id}",
        )

    # resolve duration in days
    duration_days = duration
    if duration_days is None and months is not None:
        duration_days = MONTHS_TO_DAYS.get(str(months).strip())
        if duration_days is None:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported months value '{months}'. Use one of {sorted(set(MONTHS_TO_DAYS))}.",
            )

    registration = None
    matches = []
    for row in rows:
        for plan in row.get("plans") or []:
            if registration is None:
                registration = plan.get("registration_amount")
            for price in plan.get("prices") or []:
                try:
                    dpw = int(price.get("days"))
                except (TypeError, ValueError):
                    continue
                if dpw not in (2, 3, 5, 6):  # skip package artifacts (e.g. 180)
                    continue
                if days_per_week is not None and str(price.get("days")) != str(days_per_week):
                    continue
                if duration_days is not None and int(price.get("duration", -1)) != int(duration_days):
                    continue
                item = {
                    "duration_days": int(price.get("duration")),
                    "days_per_week": int(price.get("days")),
                    "price": price.get("price"),
                }
                if item not in matches:
                    matches.append(item)

    matches.sort(key=lambda m: (m["days_per_week"], m["duration_days"]))

    # exact single hit
    if duration_days is not None and days_per_week is not None:
        exact = matches[0] if matches else None
        return {
            "venue_id": venue_id,
            "venue_name": VENUES.get(venue_id),
            "sport": sport,
            "user_type": user_type,
            "registration_amount": registration,
            "match": exact,
            "message": None if exact else "Not sold for that combination (dash). Offer callback/transfer.",
        }

    # range fallback
    prices = [m["price"] for m in matches if m.get("price") is not None]
    return {
        "venue_id": venue_id,
        "venue_name": VENUES.get(venue_id),
        "sport": sport,
        "user_type": user_type,
        "registration_amount": registration,
        "days_per_week": days_per_week,
        "price_range": {"min": min(prices), "max": max(prices)} if prices else None,
        "options": matches,
    }


async def _all_venue_sports() -> list[tuple[int, dict]]:
    """Fetch every venue's coaching data concurrently -> [(venue_id, sports_summary)]."""

    async def one(vid: int):
        try:
            payload = await _fetch_coaching(vid)
            return vid, _summarize_sports(payload.get("data", []))
        except HTTPException:
            return vid, None  # skip venues that error, don't fail the whole sweep

    results = await asyncio.gather(*(one(v) for v in VENUES))
    return [(vid, s) for vid, s in results if s is not None]


@app.get("/sports/centers")
@app.post("/sports/centers")
async def sports_centers(request: Request):
    """Which centres offer a given sport (live sweep across all venues).

    Accepts inputs from the query string OR a JSON body.
    """
    args = await _args(request)
    sport = _require_str(args.get("sport"), "sport")
    user_type = _clean_opt(args.get("user_type"))

    sport_l = sport.lower()
    ut_l = user_type.lower() if user_type else None

    centers = []
    for vid, summary in await _all_venue_sports():
        # case-insensitive sport match
        info = next(
            (v for k, v in summary.items() if k.lower() == sport_l), None
        )
        if not info:
            continue
        uts = sorted(info["user_types"])
        if ut_l and ut_l not in [u.lower() for u in uts]:
            continue
        centers.append(
            {
                "venue_id": vid,
                "venue_name": VENUES.get(vid),
                "user_types": uts,
                "days_per_week": sorted(info["days_per_week"]),
            }
        )

    centers.sort(key=lambda c: c["venue_id"])
    return {
        "sport": sport,
        "user_type": user_type,
        "count": len(centers),
        "centers": centers,
        "message": None if centers else f"No centre currently offers {sport} coaching.",
    }


@app.get("/sports")
async def sports_all():
    """Full matrix: every sport -> which centres offer it (live sweep)."""
    matrix: dict[str, list] = {}
    for vid, summary in await _all_venue_sports():
        for sport, info in summary.items():
            matrix.setdefault(sport, []).append(
                {"venue_id": vid, "venue_name": VENUES.get(vid)}
            )
    return {
        "sports": [
            {"sport": s, "centers": sorted(c, key=lambda x: x["venue_id"])}
            for s, c in sorted(matrix.items())
        ]
    }


@app.get("/membership")
async def membership(venue_id: int = Depends(VenueId)):
    return await _fetch(
        "pricing-offers-data-external/", {"tab": "membership", "venue_id": venue_id}
    )


@app.get("/bnp")
async def bnp(venue_id: int = Depends(VenueId)):
    return await _fetch(
        "pricing-offers-data-external/", {"tab": "bnp_pricing", "venue_id": venue_id}
    )


@app.get("/offers")
async def offers(venue_id: int = Depends(VenueId)):
    return await _fetch(
        "pricing-offers-active-external/", {"venue_id": venue_id}
    )

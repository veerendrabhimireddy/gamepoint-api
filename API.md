# GamePoint Voice-Agent API — Reference

**Base URL:** `https://YOUR-APP.onrender.com` (replace after Render deploy)
**Auth:** none for the caller — the NetPlay token is held server-side.
**Format:** JSON. All endpoints are `GET`.

## Venue IDs
| ID | Centre | ID | Centre |
|---|---|---|---|
| 1 | Hitec | 24 | Bandlaguda |
| 8 | 100 Feet Road | 25 | Warangal K-Club |
| 12 | Uppal | 27 | Lingampally |
| 14 | Banjara Hills | 28 | KPHB |
| 17 | Nizampet | 30 | Kompally |
| 23 | Kukatpally | 31 | Manthan Road Tellapur |
| | | 32 | Gandipet |

Enums: `user_type` = `child` | `adult` · `period` = `morning` | `evening` ·
`days_per_week` = `2` | `3` | `5` | `6` · `months` = `1` `1.5` `3` `3.5` `6` `6.5`
(mapped to plan days 30/45/90/105/180/195).

---

## 1. GET /sports/centers
Which centres coach a given sport (live sweep across all venues).

**Query:** `sport` (required), `user_type` (optional)

`GET /sports/centers?sport=Football`
```json
{
  "sport": "Football",
  "user_type": null,
  "count": 5,
  "centers": [
    {"venue_id": 12, "venue_name": "Uppal", "user_types": ["adult","child"], "days_per_week": [2,3,5]},
    {"venue_id": 17, "venue_name": "Nizampet", "user_types": ["child"], "days_per_week": [3,6]},
    {"venue_id": 27, "venue_name": "Lingampally", "user_types": ["adult","child"], "days_per_week": [2,3,5]},
    {"venue_id": 25, "venue_name": "Warangal K-Club", "user_types": ["child"], "days_per_week": [3,5]},
    {"venue_id": 30, "venue_name": "Kompally", "user_types": ["child"], "days_per_week": [3,5]}
  ],
  "message": null
}
```
Empty result → `count: 0`, `message: "No centre currently offers <sport> coaching."`

---

## 2. GET /sports
Full matrix of every sport → centres offering it.

`GET /sports`
```json
{
  "sports": [
    {"sport": "Football", "centers": [
      {"venue_id": 12, "venue_name": "Uppal"},
      {"venue_id": 17, "venue_name": "Nizampet"}
    ]}
  ]
}
```

---

## 3. GET /coaching/overview
What one centre offers.

**Query:** `venue_id` (required)

`GET /coaching/overview?venue_id=1`
```json
{
  "venue_id": 1,
  "venue_name": "Hitec",
  "sports": [
    {"sport": "Badminton", "user_types": ["adult","child"], "days_per_week": [2,3,5]},
    {"sport": "Basketball", "user_types": ["adult","child"], "days_per_week": [2,3,5]},
    {"sport": "Squash", "user_types": ["adult","child"], "days_per_week": [2,3,5]}
  ]
}
```

---

## 4. GET /coaching/availability
Batch slots + valid frequencies for one sport/age at one centre. **No pricing.**

**Query:** `venue_id` (req), `sport` (req), `user_type` (req), `period` (optional)

`GET /coaching/availability?venue_id=1&sport=Badminton&user_type=child`
```json
{
  "venue_id": 1,
  "venue_name": "Hitec",
  "sport": "Badminton",
  "user_type": "child",
  "period": null,
  "available": true,
  "days_per_week": [2,3,5],
  "slots": [
    {"days": "Mon Wed Fri", "time": "05:18-07:00", "start_hour": 5, "days_per_week": [2,3,5]},
    {"days": "Sat", "time": "07:00-08:00", "start_hour": 7, "days_per_week": [2,3,5]},
    {"days": "Mon Tue Wed Thu Fri", "time": "16:00-17:18", "start_hour": 16, "days_per_week": [2,3,5]},
    {"days": "Mon Wed Fri", "time": "17:18-19:00", "start_hour": 17, "days_per_week": [2,3,5]}
  ],
  "message": null
}
```
No match → `available: false`, empty `slots`, `message` set (treat as "Not published").

---

## 5. GET /coaching/pricing
Fee for a plan. **Separate call — only when the caller asks about fees.**

**Query:** `venue_id` (req), `sport` (req), `user_type` (req), `days_per_week`, `duration` (days) **or** `months`

**Exact match** — `GET /coaching/pricing?venue_id=1&sport=Badminton&user_type=child&days_per_week=3&months=3`
```json
{
  "venue_id": 1,
  "venue_name": "Hitec",
  "sport": "Badminton",
  "user_type": "child",
  "registration_amount": 2000.0,
  "match": {"duration_days": 90, "days_per_week": 3, "price": 16000.0},
  "message": null
}
```
Not sold → `match: null`, `message` set (the "dash" rule — do not quote).

**Range** (omit `months`/`days_per_week`) — `GET /coaching/pricing?venue_id=1&sport=Badminton&user_type=child`
```json
{
  "venue_id": 1, "venue_name": "Hitec", "sport": "Badminton", "user_type": "child",
  "registration_amount": 2000.0,
  "days_per_week": null,
  "price_range": {"min": 5000.0, "max": 43000.0},
  "options": [
    {"duration_days": 30, "days_per_week": 2, "price": 5000.0},
    {"duration_days": 90, "days_per_week": 3, "price": 16000.0}
  ]
}
```

---

## 6. GET /coaching/details
Everything for one sport at one centre (timings **and** pricing), grouped by age.

**Query:** `venue_id` (req), `sport` (req), `user_type` (optional)

`GET /coaching/details?venue_id=1&sport=Badminton&user_type=child`
```json
{
  "venue_id": 1, "venue_name": "Hitec", "sport": "Badminton",
  "user_types": [
    {
      "user_type": "child",
      "registration_amount": 2000.0,
      "days_per_week": [2,3,5],
      "timings": [
        {"days": "Mon Wed Fri", "time": "05:18-07:00", "start_hour": 5}
      ],
      "pricing": [
        {"duration_days": 30, "days_per_week": 2, "price": 5000.0},
        {"duration_days": 90, "days_per_week": 3, "price": 16000.0}
      ]
    }
  ]
}
```

---

## 7. GET /membership · GET /bnp · GET /offers
Thin pass-throughs to NetPlay (already small).

**Query:** `venue_id` (required) — returns NetPlay's raw JSON for that tab.

---

## 8. GET /venues · GET /health
- `GET /venues` → `{"venues": [{"venue_id": 1, "name": "Hitec"}, ...]}`
- `GET /health` → `{"status": "ok"}`

---

## Errors
| Code | Meaning |
|---|---|
| 400 | Bad param (e.g. unsupported `months`) |
| 404 | No coaching for that sport/age at that venue |
| 502 | NetPlay upstream unreachable / non-JSON |

Response shape: `{"detail": "<message>"}`.

# GamePoint Voice-Agent API

A thin FastAPI proxy in front of NetPlay's pricing/timing API. It slices the huge
(~26k token) `tab=coaching` payload into small, voice-agent-friendly responses so
the GamePoint voice agent doesn't have to ingest 50k tokens per lookup.

- **Live every call** — no caching; every request hits NetPlay fresh.
- **Auth stays server-side** — the `Authorization: Token ...` header is held by
  this service (env var `NETPLAY_TOKEN`); the voice agent never sees it.

## Size win (venue 1, Hitec)

| | chars |
|---|---|
| Upstream `tab=coaching` blob | 105,914 |
| `/coaching/overview` | ~1,600 |
| `/coaching/timings` | ~280 |
| `/coaching/pricing` | ~270 |

## Endpoints

| Method | Path | Query params |
|---|---|---|
| GET | `/sports/centers` | `sport`, `user_type` (optional) — which centres offer a sport |
| GET | `/sports` | — full sport → centres matrix |
| GET | `/coaching/overview` | `venue_id` — what one centre offers |
| GET | `/coaching/availability` | `venue_id`, `sport`, `user_type`, `period` (optional) — **slots + valid frequencies, NO pricing** |
| GET | `/coaching/details` | `venue_id`, `sport`, `user_type` (optional) — full timings + pricing for one sport at one centre |
| GET | `/coaching/timings` | `venue_id`, `sport`, `user_type`, `days_per_week`, `period` |
| GET | `/coaching/pricing` | `venue_id`, `sport`, `user_type`, `days_per_week`, `duration` **or** `months` |
| GET | `/membership` | `venue_id` (pass-through) |
| GET | `/bnp` | `venue_id` (pass-through) |
| GET | `/offers` | `venue_id` (pass-through) |
| GET | `/venues` | — (id → name map) |
| GET | `/health` | — |

- `user_type` = `child` or `adult`
- `period` = `morning` or `evening`
- `days_per_week` = `2`, `3`, `5`, or `6`
- `months` accepts `1, 1.5, 3, 3.5, 6, 6.5` → converted to upstream day durations
  (30, 45, 90, 105, 180, 195)

### Examples

```
GET /coaching/overview?venue_id=1
GET /coaching/timings?venue_id=1&sport=Badminton&user_type=child&days_per_week=3&period=morning
GET /coaching/pricing?venue_id=1&sport=Badminton&user_type=child&days_per_week=3&months=3
```

`/coaching/pricing` with both `days_per_week` and a duration returns a single
`match`. Omit them and it returns a `price_range` + `options` list (for the
agent's "give a range" fallback).

## Run locally

Requires Python 3.11+.

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then open http://127.0.0.1:8000/docs for interactive testing.

## Deploy to Render (free)

1. Push this folder to a GitHub repo.
2. Render → **New → Blueprint**, point at the repo (`render.yaml` is included).
3. In the service **Environment**, set `NETPLAY_TOKEN` to the real token.
4. Deploy. Your base URL will be `https://<service-name>.onrender.com`.

> Free tier sleeps after ~15 min idle; the first call after sleep takes a few
> seconds to wake. Fine for a voice agent, but expect that cold-start once.

## Notes / upstream quirks

- The real batch time is in `day_time_lines` (e.g. `Mon Wed Fri 16:00-17:00`),
  not the row-level `start_time`/`end_time` (which are `00:00`/`11:59`). Parsing
  uses `day_time_lines`.
- Upstream `days_per_week` on a row lists the *frequencies its price supports*,
  which can differ from the batch's actual weekday pattern. Timings filter on
  this field to stay consistent with upstream.

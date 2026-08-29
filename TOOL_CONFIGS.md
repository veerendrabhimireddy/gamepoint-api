# Voice-Platform Tool Configs — GamePoint API

Base URL used below: `https://gamepoint-api.onrender.com` (replace with your real Render URL).

**Common settings for ALL tools:**
- Timeout: `20`
- HTTP Method: `GET`
- Authorization: `No authentication`
- Request Headers: none
- Request Body: none (GET) — dynamic values are defined as **Properties** and templated into the URL as `{{name}}`

> Placeholder syntax: this guide uses `{{var}}`. If your platform uses `{var}` or `${var}`, swap accordingly. Each `{{var}}` in a Request URL must have a matching Property below it.

---

## 1) getCentersBySport
**Description:**
Returns the GamePoint centres that offer coaching for a given sport. Use ONLY when the caller names a sport but has not chosen a centre (e.g. "where can I play football?"). Read back the centre names, then let the caller pick one before any other coaching call.

**Request URL:**
`https://gamepoint-api.onrender.com/sports/centers?sport={{sport}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| sport | string | yes | Sport name, e.g. Football, Badminton, Basketball |

**Response Body (extract):**
| Variable | Path | Description |
|---|---|---|
| centers | centers | List of centres offering the sport |
| centerCount | count | How many centres offer it |

**Messages:** Executing → "Let me check which of our centres offer that."

---

## 2) getCoachingAvailability
**Description:**
Returns available batch time slots and valid days-per-week for one sport and age group at one centre. NO pricing. Call only after centre, sport, and child/adult are all confirmed. Recommend a slot from slots[] (morning = closest to 7 AM, evening = closest to 4:30 PM).

**Request URL:**
`https://gamepoint-api.onrender.com/coaching/availability?venue_id={{venue_id}}&sport={{sport}}&user_type={{user_type}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| venue_id | number | yes | Centre ID (Hitec 1, 100 Feet Road 8, Uppal 12, Banjara Hills 14, Nizampet 17, Kukatpally 23, Bandlaguda 24, Warangal K-Club 25, Lingampally 27, KPHB 28, Kompally 30, Manthan Road Tellapur 31, Gandipet 32) |
| sport | string | yes | Confirmed sport |
| user_type | string | yes | child or adult |

**Response Body (extract):**
| Variable | Path | Description |
|---|---|---|
| available | available | true if any batch exists |
| slots | slots | Available batch slots |
| daysPerWeek | days_per_week | Valid weekly frequencies |

**Messages:** Executing → "Let me check the batch timings for you."

---

## 3) getCoachingPricing
**Description:**
Returns the exact coaching fee and registration amount for one sport, age group, frequency, and plan duration at one centre. Call ONLY when the caller asks about fees, and only after days-per-week and duration (in months) are confirmed. If match is null, the plan is not sold — do not invent a price.

**Request URL:**
`https://gamepoint-api.onrender.com/coaching/pricing?venue_id={{venue_id}}&sport={{sport}}&user_type={{user_type}}&days_per_week={{days_per_week}}&months={{months}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| venue_id | number | yes | Centre ID |
| sport | string | yes | Confirmed sport |
| user_type | string | yes | child or adult |
| days_per_week | number | yes | 2, 3, 5, or 6 |
| months | string | yes | 1, 1.5, 3, 3.5, 6, or 6.5 |

**Response Body (extract):**
| Variable | Path | Description |
|---|---|---|
| price | match.price | Exact plan fee in rupees |
| registration | registration_amount | Registration fee (quote if non-zero) |

**Messages:** Executing → "Let me pull up the fee for that plan."

---

## 4) getCoachingOverview
**Description:**
Returns which sports a specific centre coaches, the age groups per sport, and valid days-per-week. Use to confirm a centre actually offers the caller's sport before proceeding.

**Request URL:**
`https://gamepoint-api.onrender.com/coaching/overview?venue_id={{venue_id}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| venue_id | number | yes | Centre ID |

**Response Body (extract):**
| Variable | Path | Description |
|---|---|---|
| sports | sports | Sports offered at the centre |

**Messages:** Executing → "Let me see what that centre offers."

---

## 5) getCoachingPriceRange  (optional — for "roughly how much?")
**Description:**
Returns the full price range and all plan options for a sport and age group at a centre, when the caller won't commit to a specific duration. Do not call if a specific plan is known — use getCoachingPricing instead.

**Request URL:**
`https://gamepoint-api.onrender.com/coaching/pricing?venue_id={{venue_id}}&sport={{sport}}&user_type={{user_type}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| venue_id | number | yes | Centre ID |
| sport | string | yes | Confirmed sport |
| user_type | string | yes | child or adult |

**Response Body (extract):**
| Variable | Path | Description |
|---|---|---|
| priceRange | price_range | min and max fee across plans |
| registration | registration_amount | Registration fee |

**Messages:** Executing → "Let me get you the price range."

---

## 6) getOffers
**Description:**
Returns currently active offers and discounts for a centre. Always call before mentioning any discount — never quote offers from memory.

**Request URL:**
`https://gamepoint-api.onrender.com/offers?venue_id={{venue_id}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| venue_id | number | yes | Centre ID |

**Messages:** Executing → "Let me check for any current offers."

---

## 7) getMembership
**Description:**
Returns membership / court-package plans for a centre. Call only for membership enquiries (Flow D).

**Request URL:**
`https://gamepoint-api.onrender.com/membership?venue_id={{venue_id}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| venue_id | number | yes | Centre ID |

---

## 8) getBookNPlayPricing
**Description:**
Returns pay-and-play (Book-N-Play) court pricing for a centre. Call only if a caller specifically asks for pay-and-play court rates.

**Request URL:**
`https://gamepoint-api.onrender.com/bnp?venue_id={{venue_id}}`

**Properties (inputs):**
| Name | Type | Required | Description |
|---|---|---|---|
| venue_id | number | yes | Centre ID |

---

## Notes
- **Aliases:** none needed — response field names are already clean.
- **First call after idle** may take a few seconds (Render free tier cold start); the "Executing" message covers that gap.
- If your platform cannot template `{{var}}` into the URL for GET, tell me and I'll give you a version where the base URL is fixed and the params are defined as tool parameters the platform appends automatically.

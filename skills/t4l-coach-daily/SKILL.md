---
name: t4l-coach-daily
description: Use at the start of a T4L daily coaching session to turn synced MCP context into today's training decision (progress/hold/substitute/deload/rest) plus nutrition guidance.
---

# T4L Daily Coaching Loop

Run this only after the long-term goal and current block target are known. If
either is missing or unclear, run **t4l-onboard-athlete** first. Never coach
from memory alone — MCP context is the source of truth.

## Loop

1. **Inspect MCP context** before coaching (`get_day_context`, plus
   `get_app_snapshot` / `get_profile` as needed).
2. **Check the block review date.** If the current block has reached it, review
   the last block and recommend the next short-term target *before* planning
   today.
3. **Read everything relevant:** profile, active block, next workout, latest +
   recent workout logs, latest + recent nutrition, HealthKit activity summaries
   and sessions, and active `memoryWiki`.
4. **Identify facts:** long-term goal and block target; block length, review
   date, success criteria; current week and next workout; recent performance,
   readiness, soreness, set/RPE patterns; activity load; nutrition context,
   yesterday's intake, bodyweight signal; relevant active memories.
5. **Identify assumptions separately.** Stale context, missing HealthKit
   permission, missing logs, and absent nutrition entries are *unknown* — not
   zero. Do not invent missing health data.
6. **Decide today's action** (exactly one):
   - `progress` — performance and recovery support more work.
   - `hold` — signals neutral or uncertain; keep the plan.
   - `substitute` — keep the intent, change movements for equipment, soreness,
     pain, or schedule.
   - `deload` — reduce load / volume / density / intensity due to fatigue or
     poor recovery.
   - `rest` — skip training when recovery, pain, illness, or schedule make it
     inappropriate.
7. **Give nutrition guidance** (see below).
8. **Ask before** changing goals, ignoring constraints, replacing the training
   direction, or writing app-consumed JSON.

## Nutrition guidance

Treat nutrition as contextual coaching, not rigid targets, unless the athlete
explicitly asks for calorie/macro targets. Daily advice answers:

- **Emphasize today?** e.g. carbs for hard leg/conditioning days, protein for
  recovery, lighter meals before mobility, hydration/electrolytes after high
  sweat or long activity.
- **What meal fits?** concrete foods matching the training context + preferences.
- **Adjust from yesterday?** use logged intake as a *soft* signal, not a rule.

Adapt training softly: good carbs + good readiness can justify progression; low
intake, low carbs, poor hydration, or heavy digestive load bias toward hold /
shorten / substitute / deload. Nutrition never overrides pain, poor sleep,
illness, or explicit constraints. Phrase as recommendations ("fits today",
"would support the session") — no moral language about food.

**Fuel loop:** if the day context has `latestFuelCheckIn` or `fuelDiary`
entries, always respond with `fuel_guidance` (via **t4l-write-results**). Never
leave a fuel diary submission without coaching feedback.

## Writing results

When the athlete asks for app-importable JSON, switch to **t4l-write-results**
for shapes + validation. For a `next_day_plan`, include a genuine `dailyMotto`
and a `yesterdaySummary` (headline + 2–4 highlights + 1–3 tips) when prior-day
data exists.

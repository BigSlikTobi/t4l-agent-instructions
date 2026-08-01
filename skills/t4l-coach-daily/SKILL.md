---
name: t4l-coach-daily
description: Use at the start of a T4L daily coaching session to turn synced MCP context into today's training decision (progress/hold/substitute/deload/rest) plus nutrition guidance.
---

# T4L Daily Coaching Loop

Run this only after the long-term goal and current block target are known. If
either is missing or unclear, run **t4l-onboard-athlete** first. Never coach
from memory alone — MCP context is the source of truth.

## Loop

1. **Inspect MCP context** before coaching. Call `get_planning_context` for the
   full working set in one read — day context, recent logs, profile, active
   block, next workout, fuel/nutrition, pending requests, **coaching notes, and
   recent chat**. Coaching notes + recent chat are how the athlete's in-app chat
   intent reaches planning — honor them, don't plan around them.
2. **Check the block review date.** If the current block has reached it, review
   the last block and recommend the next short-term target *before* planning
   today.
3. **Read what the bundle does not cover:** HealthKit activity summaries and
   sessions, and active `memoryWiki`; pull a fuller artifact (`get_app_snapshot`)
   when a latest payload is not enough.
4. **Identify facts:** long-term goal and block target; block length, review
   date, success criteria; current week and next workout; recent performance,
   readiness, soreness, set/RPE patterns; activity load; nutrition context,
   yesterday's intake, bodyweight signal; relevant active memories; explicit
   athlete requests and open questions from coaching notes — mark a request
   `addressed` (`write_coaching_notes`) once a written plan reflects it.
5. **Build a recent-comparison map.** Use recent logs, the accepted block, the
   prior next-day plan, coaching notes, and recent chat. Note exercise exposure
   and order, prescriptions, session formats, titles, mottos, cues, summary
   wording, and fuel advice. Compare the candidate with this map; do not read
   history and then ignore it.
6. **Identify assumptions separately.** Stale context, missing HealthKit
   permission, missing logs, and absent nutrition entries are *unknown* — not
   zero. Do not invent missing health data.
7. **Decide today's action** (exactly one):
   - `progress` — performance and recovery support more work.
   - `hold` — signals neutral or uncertain; keep the intended stress and
     anchors, not necessarily the prior session or wording.
   - `substitute` — keep the intent, change movements for equipment, soreness,
     pain, or schedule.
   - `deload` — reduce load / volume / density / intensity due to fatigue or
     poor recovery.
   - `rest` — skip training when recovery, pain, illness, or schedule make it
     inappropriate.
8. **Apply safe novelty.** Keep block intent, primary anchors, progression,
   recovery, injury limits, equipment, schedule, and preferences stable. On a
   normal training day, require at least one meaningful fresh element when safe:
   a log-backed progression challenge; 1–2 pattern-matched accessory variants;
   a format/sequence/tempo/density change; or a short skill, carry, mobility, or
   conditioning element. Do not combine an unfamiliar element with a large
   increase in load, volume, density, or impact. On rest/deload days, use a new
   observation or safe recovery option rather than adding training stress.
9. **Give nutrition guidance** (see below).
10. **Ask before** changing goals, ignoring constraints, replacing the training
   direction, or writing app-consumed JSON.

## Novelty guardrails

- Do not send the same exercise order and prescription as a recent
  same-purpose session unless it is a deliberate benchmark, technique, rehab,
  taper, or recovery repeat. If it is, explain why and what is being measured.
- Do not rotate primary lifts just to look creative. Usually keep the anchors
  and vary 1–2 accessories or one format lever.
- In a multi-week block, plan a small accessory/format rotation around stable
  anchors. Check the whole block for copy-pasted sessions; do not replace every
  exercise every week.
- New wording alone is not meaningful training novelty. Do not reuse recent
  titles, mottos, openings, summaries, or fuel lines word for word, and do not
  hide stale advice behind synonyms. Exact safety/form cues may repeat when
  consistency protects the athlete.
- Keep the workout `rationale` short but name the retained anchor, the fresh
  element, and why it fits today's context.

## Nutrition guidance

Treat nutrition as contextual coaching, not rigid targets, unless the athlete
explicitly asks for calorie/macro targets. Daily advice answers:

- **Emphasize today?** e.g. carbs for hard leg/conditioning days, protein for
  recovery, lighter meals before mobility, hydration/electrolytes after high
  sweat or long activity.
- **What meal fits?** concrete foods matching the training context + preferences.
- **Adjust from yesterday?** use logged intake as a *soft* signal, not a rule.

Compare with recent fuel guidance. Do not recycle the same macro sentence or
meal idea each day. Rotate foods/timing only within known preferences and
digestion constraints. A preferred routine meal can stay; make today's portion,
timing, or reason specific instead of forcing novelty.

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
data exists. Compare both with recent plans before writing them.

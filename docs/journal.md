# Journal

Read this file after the setup sequence. It documents contract changes and new
capabilities so you can use them immediately.

---

## 2026-05-27 — Contract v2: Tracking Modes, Daily Coaching Context, Fuel Round-Trip

### Exercise tracking modes

Exercises now carry an optional `trackingMode` field. Set it when prescribing:

- `"weightAndReps"` (default, can be omitted) — weighted exercises.
- `"repsOnly"` — bodyweight exercises (push-ups, pull-ups, dips, planks).
  The app hides the weight input.
- `"timeOnly"` — cardio, stretching, easy walks, foam rolling. The app shows
  a duration stepper instead of weight/reps. Include `targetDurationSeconds`
  (integer) and set `reps` to a human-readable label like `"20 min"`.

Old agents that omit `trackingMode` still work — the app defaults to
`weightAndReps`.

### Daily coaching context in next-day plans

`write_next_day_plan` now accepts optional coaching metadata alongside the
workout object:

- `dailyMotto` (string) — short motivational phrase. The app shows it inside
  the Today hero card as an italic quote.
- `yesterdaySummary` (object) — previous-day performance review:
  - `headline`: one-line summary.
  - `highlights`: 2-4 bullet observations.
  - `tips`: 1-3 actionable watch-outs for today.
  The app displays this in the Coach > Plan tab.
- `goals` (object) — current coaching goals:
  - `longTerm`: the athlete's overarching goal.
  - `shortTerm`: the current block target.
  - `blockReviewDate`: ISO date when the block should be reviewed.
  The app displays this at the top of the Coach > Plan tab with a countdown
  badge. Include `goals` in both `write_next_day_plan` and
  `write_training_block_plan` payloads.

All fields are optional. The app hides the corresponding UI when they are
absent, so old agents are unaffected.

### Fuel guidance round-trip

The fuel feedback loop is now fully wired:

1. The athlete logs meals in the Fuel Diary and submits with a quality score.
2. The app pushes `latestFuelCheckIn` and `fuelDiary` entries via day context.
3. **You must respond** by writing `fuel_guidance` through MCP whenever the day
   context contains fuel diary data. The app polls for it shortly after
   submission — do not leave diary entries without a response.

The `fuel_guidance` schema is documented in `exchange_contract.md`. Key fields:
`signal` (`green`/`hold`/`fuel`/`deload`), `todayAdvice`, `mealSuggestion`,
`yesterdayRead`, `mealIdeas`.

### What to do differently starting now

1. Set `trackingMode` on every exercise. Default is fine for loaded work —
   explicitly set `"repsOnly"` or `"timeOnly"` when appropriate.
2. Include `dailyMotto`, `yesterdaySummary`, and `goals` in every
   `write_next_day_plan` call.
3. Include `goals` in every `write_training_block_plan` call.
4. Always write `fuel_guidance` when the day context has fuel diary entries.

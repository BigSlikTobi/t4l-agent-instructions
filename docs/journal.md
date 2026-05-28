# Journal

Read this file after the setup sequence. It documents contract changes and new
capabilities so you can use them immediately.

---

## 2026-05-28 — Server 0.2.0: write validation, no silent retries, complete tool list

The self-hosted server is now `t4l-server` 0.2.0. Install and run are unchanged
(`pipx install t4l-server`, then `t4l-server serve --data-dir ~/T4LServerData`).
Add `--log-level DEBUG` when troubleshooting a connection.

### Results are validated and bad ones are dropped, not retried

This is the most important change. The app validates each result when it imports
it. A result it cannot read is **discarded once** and the user is told to ask you
to resend — there is no silent retry loop anymore. Send complete, valid payloads
the first time. The app rejects:

- `training_block_plan`: empty `workouts`, or `durationWeeks` below 1.
- `next_day_plan`: a workout with no `exercises`.
- `nutrition_analysis_result`: `calories` not greater than 0, or a negative macro.

`fuel_guidance` is always accepted. If you learn a result was discarded, fix the
payload and write it again.

### Always set a valid `schema`

The server now rejects a write whose `schema` field is present but not a
non-empty string. Set the correct `schema` on each result (e.g.
`"fuel_guidance.v1"`, `"nutrition_analysis_result.v1"`), or omit it to accept the
default `<kind>.v1`.

### Complete tool inventory (see `exchange_contract.md`)

- `write_next_day_plan` is a first-class write tool — earlier tool lists omitted
  it. Use it for single-day workouts.
- Read tools are now documented in full, including `get_training_block_request`,
  `get_nutrition_analysis_request`, and `get_blob_base64` (read a meal photo by
  the `name` from the request).
- The `nutrition_analysis_result` payload shape is now documented. Echo the
  request's `requestId` and keep `calories` above 0.

### `t4l-bridge` command removed

Older setups exposed a `t4l-bridge` alias. It is gone — start the server with
`t4l-server` only.

### What to do differently starting now

1. Send complete, valid result payloads — there is no retry safety net anymore.
2. Set a correct `schema` string on every result (or omit it for the default).
3. Use `write_next_day_plan` for single-day plans, and the documented
   `nutrition_analysis_result` shape for meal analyses.
4. Run the server with `t4l-server` (never `t4l-bridge`).

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

---
name: t4l-write-results
description: Use before writing any T4L app result via MCP. Provides the exact payload shapes and a validator script so the app won't silently discard the result.
---

# Write T4L App Results (Safely)

Use this whenever you are about to write an app-consumed result through an MCP
write tool. **The app imports a result exactly once; a result it cannot read is
discarded with no automatic retry** — the user is just told to ask you to
resend. So validate before you write.

## Which tool for which result

| Result | MCP write tool | Write when |
|---|---|---|
| Full training block | `write_training_block_plan` | producing a complete multi-week block |
| Single day | `write_next_day_plan` | one day's workout (+ optional `yesterdaySummary`, `dailyMotto`, `goals`) |
| Day fueling | `write_fuel_guidance` | day-level fueling advice; **required** if context has `latestFuelCheckIn` / `fuelDiary` |
| Meal analysis | `write_nutrition_analysis_result` | answering a pending nutrition-analysis request (echo its `requestId`) |

## Hard rules that make the app DISCARD the result

- `training_block_plan`: `workouts` must be non-empty; `durationWeeks` ≥ 1.
- `next_day_plan`: the `workout` must have non-empty `items` or non-empty
  `exercises`.
- `nutrition_analysis_result`: `calories` > 0; every macro ≥ 0.
- `fuel_guidance`: always accepted (but still send a useful, complete payload).
- Any result: `schema`, if present, must be a non-empty string — or omit it to
  accept the default `<kind>.v1`.

## Validate before writing

Run the bundled validator on your candidate payload first:

```bash
python scripts/validate_payload.py <kind> path/to/payload.json
# or:  cat payload.json | python scripts/validate_payload.py <kind>
# <kind> = training_block_plan | next_day_plan | fuel_guidance | nutrition_analysis_result
```

It prints `ERROR:` for anything the app would discard (exit code 1) and `WARN:`
for contract fields that are missing but not fatal. Fix every ERROR, then call
the matching MCP write tool. No Python available? Hand-check against the "Hard
rules" above and `reference/payload-shapes.md`.

## Payload shapes

Full field-by-field shapes, required fields, valid `style` values, mobile
display fields (`loadLabel`, `primaryCue`, `detailNote`, `warningCue`),
`trackingMode` (`weightAndReps` default / `repsOnly` / `timeOnly`), `media`,
supersets/circuits via workout `items`, and worked examples are in
**`reference/payload-shapes.md`** — read it when constructing a payload. Always
include `goals` (`longTerm`, `shortTerm`, `blockReviewDate`) in `next_day_plan`
and `training_block_plan`.

## Before you write

Ask the athlete first when the result changes goals, constraints, training
direction, or nutrition targets.

Plans produced by the **t4l-coach-committee** head coach are written through this
skill like any other result — committee deliberation never bypasses validation.

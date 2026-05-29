#!/usr/bin/env python3
"""Validate a T4L app-consumed result before writing it through an MCP tool.

The T4L app imports a pending result exactly once; a result it cannot read is
discarded with no automatic retry. This script reproduces the app's documented
import rules (and the contract shape) so the coaching agent can self-check a
payload BEFORE calling write_training_block_plan / write_next_day_plan /
write_fuel_guidance / write_nutrition_analysis_result.

Usage:
    python validate_payload.py <kind> path/to/payload.json
    cat payload.json | python validate_payload.py <kind>

<kind>: training_block_plan | next_day_plan | fuel_guidance | nutrition_analysis_result

ERROR lines = the app WILL discard this payload. Fix all of them.
WARN  lines = contract fields missing/odd but not fatal.

Exit code: 1 on any ERROR (or bad input), else 0.
Standard library only — no dependencies.
"""
from __future__ import annotations

import json
import sys

KINDS = (
    "training_block_plan",
    "next_day_plan",
    "fuel_guidance",
    "nutrition_analysis_result",
)

VALID_STYLES = {"rugby", "boxer", "hybrid", "strengthHypertrophy", "conditioning", "custom"}
VALID_TRACKING = {"weightAndReps", "repsOnly", "timeOnly"}
VALID_SIGNALS = {"green", "hold", "fuel", "deload"}

BLOCK_REQUIRED = ["id", "style", "title", "durationWeeks", "currentWeek", "weeklyFocus",
                  "measurableTargets", "workouts", "createdBy", "createdAt"]
WORKOUT_REQUIRED = ["id", "week", "day", "title", "focus", "rationale", "conditioning", "exercises"]
EXERCISE_REQUIRED = ["exerciseId", "name", "sets", "reps", "targetLoad", "targetRpe",
                     "restSeconds", "coachCue"]


class Report:
    def __init__(self):
        self.errors = []
        self.warns = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


def is_number(v):
    # Reject bool, which is an int subclass in Python.
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_nonempty_list(v):
    return isinstance(v, list) and len(v) > 0


def check_schema(payload, r):
    schema = payload.get("schema")
    if schema is not None and (not isinstance(schema, str) or not schema.strip()):
        r.error("'schema' must be a non-empty string when present (or omit it).")


def validate_exercise(ex, where, r):
    if not isinstance(ex, dict):
        r.error(f"{where}: exercise must be an object.")
        return
    for f in EXERCISE_REQUIRED:
        if f not in ex or ex[f] in (None, ""):
            r.warn(f"{where}: exercise missing '{f}'.")
    tm = ex.get("trackingMode")
    if tm is not None and tm not in VALID_TRACKING:
        r.warn(f"{where}: trackingMode '{tm}' not in {sorted(VALID_TRACKING)}.")
    if tm == "timeOnly" and not ex.get("targetDurationSeconds"):
        r.warn(f"{where}: timeOnly exercise should set 'targetDurationSeconds'.")


def validate_workout(w, where, r):
    if not isinstance(w, dict):
        r.error(f"{where}: workout must be an object.")
        return
    for f in WORKOUT_REQUIRED:
        if f == "exercises":
            continue
        if f not in w or w[f] in (None, ""):
            r.warn(f"{where}: workout missing '{f}'.")
    exercises = w.get("exercises")
    if not is_nonempty_list(exercises):
        r.error(f"{where}: workout has no exercises (app discards this).")
        return
    for i, ex in enumerate(exercises):
        validate_exercise(ex, f"{where} exercise[{i}]", r)


def validate_goals(goals, r):
    if goals is None:
        return
    if not isinstance(goals, dict):
        r.warn("'goals' should be an object with longTerm / shortTerm / blockReviewDate.")
        return
    for f in ("longTerm", "shortTerm", "blockReviewDate"):
        if not goals.get(f):
            r.warn(f"goals missing '{f}'.")


def validate_training_block_plan(payload, r):
    block = payload.get("block") if isinstance(payload.get("block"), dict) else payload
    for f in BLOCK_REQUIRED:
        if f in ("durationWeeks", "workouts"):
            continue  # checked as hard rules below
        if f not in block or block[f] in (None, ""):
            r.warn(f"block missing '{f}'.")
    style = block.get("style")
    if style is not None and style not in VALID_STYLES:
        r.warn(f"block style '{style}' not in {sorted(VALID_STYLES)}.")
    dw = block.get("durationWeeks")
    if not is_number(dw) or dw < 1:
        r.error("block 'durationWeeks' must be a number >= 1 (app discards this).")
    workouts = block.get("workouts")
    if not is_nonempty_list(workouts):
        r.error("block 'workouts' must be a non-empty list (app discards this).")
    else:
        for i, w in enumerate(workouts):
            validate_workout(w, f"workout[{i}]", r)
    validate_goals(payload.get("goals") or block.get("goals"), r)


def validate_next_day_plan(payload, r):
    workout = payload.get("workout")
    if not isinstance(workout, dict):
        r.error("next_day_plan must have a 'workout' object (app discards this).")
    else:
        validate_workout(workout, "workout", r)
    ys = payload.get("yesterdaySummary")
    if ys is not None:
        if not isinstance(ys, dict):
            r.warn("'yesterdaySummary' should be an object.")
        elif not ys.get("headline"):
            r.warn("yesterdaySummary missing 'headline'.")
    validate_goals(payload.get("goals"), r)


def validate_fuel_guidance(payload, r):
    # Always accepted by the app; still sanity-check for usefulness.
    signal = payload.get("signal")
    if signal is not None and signal not in VALID_SIGNALS:
        r.warn(f"fuel_guidance signal '{signal}' not in {sorted(VALID_SIGNALS)}.")
    if not payload.get("todayAdvice"):
        r.warn("fuel_guidance has no 'todayAdvice' — the athlete expects feedback.")


def validate_nutrition_analysis_result(payload, r):
    cal = payload.get("calories")
    if not is_number(cal) or cal <= 0:
        r.error("nutrition_analysis_result 'calories' must be a number > 0 (app discards this).")
    for m in ("protein", "carbs", "fat"):
        v = payload.get(m)
        if v is not None and is_number(v) and v < 0:
            r.error(f"nutrition_analysis_result '{m}' is negative (app discards this).")
    conf = payload.get("confidence")
    if conf is not None and (not is_number(conf) or not 0 <= conf <= 1):
        r.warn("'confidence' should be a number within 0..1.")
    if not payload.get("requestId"):
        r.warn("nutrition_analysis_result should echo the request's 'requestId'.")


VALIDATORS = {
    "training_block_plan": validate_training_block_plan,
    "next_day_plan": validate_next_day_plan,
    "fuel_guidance": validate_fuel_guidance,
    "nutrition_analysis_result": validate_nutrition_analysis_result,
}


def main(argv):
    if len(argv) < 2 or argv[1] not in KINDS:
        sys.stderr.write("usage: validate_payload.py <" + " | ".join(KINDS) + "> [payload.json]\n")
        return 2
    kind = argv[1]

    if len(argv) >= 3:
        try:
            with open(argv[2], "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as e:
            sys.stderr.write(f"ERROR: cannot read {argv[2]}: {e}\n")
            return 1
    else:
        raw = sys.stdin.read()

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"ERROR: payload is not valid JSON: {e}\n")
        return 1
    if not isinstance(payload, dict):
        sys.stderr.write("ERROR: payload must be a JSON object.\n")
        return 1

    r = Report()
    check_schema(payload, r)
    VALIDATORS[kind](payload, r)

    for w in r.warns:
        print(f"WARN:  {w}")
    for e in r.errors:
        print(f"ERROR: {e}")

    if r.errors:
        print(f"\n{len(r.errors)} error(s) — the app would discard this {kind}. Fix and re-validate.")
        return 1
    suffix = f" ({len(r.warns)} warning(s))." if r.warns else "."
    print(f"OK: {kind} passes the app's import rules{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

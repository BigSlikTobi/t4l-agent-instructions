#!/usr/bin/env python3
"""Validate a T4L app-consumed result before writing it through an MCP tool.

The T4L app imports a pending result exactly once; a result it cannot read is
discarded with no automatic retry. This script reproduces the app's documented
import rules (and the contract shape) so the coaching agent can self-check a
payload BEFORE calling write_training_block_plan / write_next_day_plan /
write_fuel_guidance / write_nutrition_analysis_result.

Usage:
    python validate_payload.py <kind> path/to/payload.json [--recent-context context.json]
    cat payload.json | python validate_payload.py <kind>

<kind>: training_block_plan | next_day_plan | fuel_guidance | nutrition_analysis_result

ERROR lines = the app WILL discard this payload. Fix all of them.
WARN  lines = contract or coaching-quality concerns that need review but are not fatal.

Exit code: 1 on any ERROR (or bad input), else 0.
Standard library only — no dependencies.
"""
from __future__ import annotations

import argparse
import json
import re
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
GROUP_TYPES = {"superset", "circuit"}
REUSED_COPY_FIELDS = {
    "dailyMotto": "daily motto",
    "headline": "summary headline",
    "highlights": "summary highlight",
    "tips": "summary tip",
    "todayAdvice": "fuel advice",
    "yesterdayRead": "fuel recap",
    "signalSub": "fuel signal copy",
}

BLOCK_REQUIRED = ["id", "style", "title", "durationWeeks", "currentWeek", "weeklyFocus",
                  "measurableTargets", "workouts", "createdBy", "createdAt"]
WORKOUT_REQUIRED = ["id", "week", "day", "title", "focus", "rationale", "conditioning"]
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


def validate_workout_item(item, where, r):
    if not isinstance(item, dict):
        r.error(f"{where}: workout item must be an object.")
        return
    item_type = item.get("type", "exercise")
    if item_type in (None, "", "exercise"):
        validate_exercise(item.get("exercise") if isinstance(item.get("exercise"), dict) else item,
                          where, r)
        return
    if item_type == "circle":
        r.error(f'{where}: use "circuit", not "circle".')
        return
    if item_type not in GROUP_TYPES:
        r.error(f"{where}: item type must be exercise, superset, or circuit.")
        return

    exercises = item.get("exercises")
    if not is_nonempty_list(exercises):
        r.error(f"{where}: {item_type} must contain child exercises.")
        return
    rounds = item.get("rounds")
    if not is_number(rounds) or rounds < 1:
        r.error(f"{where}: {item_type} 'rounds' must be a number >= 1.")
    if item_type == "superset" and len(exercises) != 2:
        r.error(f"{where}: superset must contain exactly 2 exercises.")
    if item_type == "circuit" and len(exercises) < 3:
        r.error(f"{where}: circuit must contain at least 3 exercises.")
    if not item.get("groupId"):
        r.warn(f"{where}: grouped item should include stable 'groupId'.")
    for i, ex in enumerate(exercises):
        validate_exercise(ex, f"{where} {item_type}.exercise[{i}]", r)


def validate_workout(w, where, r):
    if not isinstance(w, dict):
        r.error(f"{where}: workout must be an object.")
        return
    for f in WORKOUT_REQUIRED:
        if f not in w or w[f] in (None, ""):
            r.warn(f"{where}: workout missing '{f}'.")
    items = w.get("items")
    exercises = w.get("exercises")
    if is_nonempty_list(items):
        for i, item in enumerate(items):
            validate_workout_item(item, f"{where} item[{i}]", r)
        return
    if not is_nonempty_list(exercises):
        r.error(f"{where}: workout has no items/exercises (app discards this).")
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


def normalize_text(value):
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value.strip().casefold())


def exercise_identity(ex):
    if not isinstance(ex, dict):
        return ""
    return normalize_text(ex.get("exerciseId") or ex.get("name"))


def exercise_signature(ex, include_prescription):
    identity = exercise_identity(ex)
    if not include_prescription:
        return ("exercise", identity)
    return (
        "exercise",
        identity,
        ex.get("sets"),
        normalize_text(str(ex.get("reps", ""))),
        normalize_text(str(ex.get("targetLoad", ""))),
        ex.get("targetRpe"),
        ex.get("restSeconds"),
        ex.get("trackingMode"),
        ex.get("targetDurationSeconds"),
    )


def workout_signature(workout, include_prescription):
    if not isinstance(workout, dict):
        return ()
    signature = []
    items = workout.get("items")
    if is_nonempty_list(items):
        for item in items:
            if not isinstance(item, dict):
                continue
            item_type = item.get("type", "exercise") or "exercise"
            if item_type in GROUP_TYPES:
                group = ["group", item_type]
                if include_prescription:
                    group.extend((item.get("rounds"), item.get("restSeconds")))
                signature.append(tuple(group))
                for ex in item.get("exercises", []):
                    signature.append(exercise_signature(ex, include_prescription))
            else:
                ex = item.get("exercise") if isinstance(item.get("exercise"), dict) else item
                signature.append(exercise_signature(ex, include_prescription))
        return tuple(signature)
    for ex in workout.get("exercises", []):
        signature.append(exercise_signature(ex, include_prescription))
    return tuple(signature)


def looks_like_workout(value):
    if not isinstance(value, dict) or value.get("type") in GROUP_TYPES:
        return False
    if is_nonempty_list(value.get("items")):
        return True
    return is_nonempty_list(value.get("exercises")) and any(
        key in value for key in ("id", "title", "focus", "conditioning", "week", "day", "date")
    )


def find_workouts(value):
    found = []

    def visit(node):
        if isinstance(node, dict):
            if looks_like_workout(node):
                found.append(node)
                return
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return found


def candidate_workouts(kind, payload):
    if kind == "training_block_plan":
        block = payload.get("block") if isinstance(payload.get("block"), dict) else payload
        return block.get("workouts", []) if isinstance(block.get("workouts"), list) else []
    if kind == "next_day_plan" and isinstance(payload.get("workout"), dict):
        return [payload["workout"]]
    return []


def collect_keyed_text(value, key, output):
    if isinstance(value, dict):
        for child_key, child in value.items():
            if child_key == key:
                if isinstance(child, str):
                    text = normalize_text(child)
                    if text:
                        output.add(text)
                elif isinstance(child, list):
                    output.update(normalize_text(item) for item in child if normalize_text(item))
            collect_keyed_text(child, key, output)
    elif isinstance(value, list):
        for child in value:
            collect_keyed_text(child, key, output)


def collect_meal_names(value, output):
    if isinstance(value, dict):
        suggestion = value.get("mealSuggestion")
        if isinstance(suggestion, dict):
            name = normalize_text(suggestion.get("name"))
            if name:
                output.add(name)
        ideas = value.get("mealIdeas")
        if isinstance(ideas, list):
            for idea in ideas:
                if isinstance(idea, dict):
                    name = normalize_text(idea.get("name"))
                    if name:
                        output.add(name)
        for child in value.values():
            collect_meal_names(child, output)
    elif isinstance(value, list):
        for child in value:
            collect_meal_names(child, output)


def validate_recent_comparison(kind, payload, recent_context, r):
    """Warn about obvious stale repeats. Human judgment still owns safe novelty."""
    candidates = candidate_workouts(kind, payload)
    recent_workouts = find_workouts(recent_context)

    for index, workout in enumerate(candidates):
        label = workout.get("title") or workout.get("id") or f"workout[{index}]"
        exact = workout_signature(workout, include_prescription=True)
        sequence = workout_signature(workout, include_prescription=False)
        if exact and any(exact == workout_signature(old, True) for old in recent_workouts):
            r.warn(
                f"{label!r} matches a recent exercise order and prescription; "
                "confirm this is a deliberate repeat and explain the reason/metric in rationale."
            )
        elif sequence and any(sequence == workout_signature(old, False) for old in recent_workouts):
            r.warn(
                f"{label!r} repeats a recent exercise order; confirm the changed prescription "
                "is meaningful progression or add one safe fresh element."
            )

    for left in range(len(candidates)):
        for right in range(left + 1, len(candidates)):
            left_sig = workout_signature(candidates[left], include_prescription=True)
            right_sig = workout_signature(candidates[right], include_prescription=True)
            if left_sig and left_sig == right_sig:
                r.warn(
                    f"candidate workouts {left} and {right} use the same exercise order and "
                    "prescription; confirm the duplicate is deliberate."
                )

    recent_titles = {
        normalize_text(workout.get("title")) for workout in recent_workouts
        if normalize_text(workout.get("title"))
    }
    for workout in candidates:
        title = normalize_text(workout.get("title"))
        if title and title in recent_titles:
            r.warn(f"workout title {workout.get('title')!r} was used recently; make today's title current.")

    for field, label in REUSED_COPY_FIELDS.items():
        recent_values = set()
        candidate_values = set()
        collect_keyed_text(recent_context, field, recent_values)
        collect_keyed_text(payload, field, candidate_values)
        if candidate_values & recent_values:
            r.warn(f"candidate reuses recent {label} word for word; tie the copy to today's context.")

    recent_meals = set()
    candidate_meals = set()
    collect_meal_names(recent_context, recent_meals)
    collect_meal_names(payload, candidate_meals)
    if candidate_meals & recent_meals:
        r.warn(
            "candidate repeats a recent meal suggestion; keep it only when it is a preferred "
            "routine and make today's timing, portion, or reason specific."
        )


VALIDATORS = {
    "training_block_plan": validate_training_block_plan,
    "next_day_plan": validate_next_day_plan,
    "fuel_guidance": validate_fuel_guidance,
    "nutrition_analysis_result": validate_nutrition_analysis_result,
}


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=KINDS)
    parser.add_argument("payload", nargs="?", help="candidate JSON file; omit to read stdin")
    parser.add_argument(
        "--recent-context",
        help="optional fresh planning-context JSON used for coaching-quality repeat checks",
    )
    args = parser.parse_args(argv[1:])
    kind = args.kind

    if args.payload:
        try:
            with open(args.payload, "r", encoding="utf-8") as fh:
                raw = fh.read()
        except OSError as e:
            sys.stderr.write(f"ERROR: cannot read {args.payload}: {e}\n")
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

    if args.recent_context:
        try:
            with open(args.recent_context, "r", encoding="utf-8") as fh:
                recent_context = json.load(fh)
        except (OSError, json.JSONDecodeError) as e:
            sys.stderr.write(f"ERROR: cannot read recent context {args.recent_context}: {e}\n")
            return 1
        if not isinstance(recent_context, (dict, list)):
            sys.stderr.write("ERROR: recent context must be a JSON object or list.\n")
            return 1
        validate_recent_comparison(kind, payload, recent_context, r)

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

#!/usr/bin/env python3
"""Validate a legacy T4L result payload body before an MCP proposal write.

This script checks the documented legacy body rules. It does not validate the
coaching-contract envelope and cannot prove review, import, or phone application.

Usage:
    python validate_payload.py <kind> path/to/payload.json [--recent-context context.json]
    cat payload.json | python validate_payload.py <kind>

<kind>: training_block_plan | next_day_plan | fuel_guidance | nutrition_analysis_result

ERROR lines = the body violates a known legacy import rule. Fix all of them.
WARN  lines = compatibility or coaching-quality concerns that need review.

Exit code: 1 on any ERROR (or bad input), else 0.
Standard library only — no dependencies.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
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
EXPECTED_SCHEMAS = {
    "training_block_plan": "training_block_plan.v1",
    "next_day_plan": "next_day_plan.v1",
    "fuel_guidance": "fuel_guidance.v1",
    "nutrition_analysis_result": "nutrition_analysis_result.v1",
}
GROUP_TYPES = {"superset", "circuit"}
YOUTUBE_SHORT_URL_RE = re.compile(
    r"^https://www\.youtube\.com/shorts/[A-Za-z0-9_-]{11}$"
)
REUSED_COPY_FIELDS = {
    "dailyMotto": "daily motto",
    "headline": "summary headline",
    "highlights": "summary highlight",
    "tips": "summary tip",
    "todayAdvice": "fuel advice",
    "yesterdayRead": "fuel recap",
    "signalSub": "fuel signal copy",
}

CONTRACT_SCHEMA = "t4l.coaching-contract.v1"
CONTRACT_VERSION = "1.0.0"
ACCEPTED_STATE_KEYS = {
    "schema",
    "contractVersion",
    "messageType",
    "producer",
    "contextRevision",
    "generatedAt",
    "sources",
    "target",
    "activeSessionId",
    "activeSession",
    "state",
}
PLANNING_CONTEXT_KEYS = {
    "schema",
    "contractVersion",
    "messageType",
    "producer",
    "generatedAt",
    "acceptedState",
    "proposals",
    "appliedReceipts",
    "currentRequests",
    "requestHistory",
}
SOURCE_KEYS = {
    "sourceId",
    "kind",
    "path",
    "fields",
    "sourceRevision",
    "artifactId",
    "sourceTime",
    "receivedAt",
    "availability",
    "freshness",
}
SOURCE_KINDS = {
    "phone_state",
    "training_log",
    "nutrition_log",
    "health_activity",
    "athlete_profile",
    "athlete_request",
    "athlete_chat",
    "other",
}
CONTEXT_REVISION_RE = re.compile(r"^ctx_[0-9]{1,20}_[a-f0-9]{8,64}$")
SOURCE_ID_RE = re.compile(r"^src_[a-z0-9]{8,64}$")
SOURCE_REVISION_RE = re.compile(r"^(?:ctx_[0-9]{1,20}_[a-f0-9]{8,64}|srcv_[a-z0-9]{8,64})$")
ARTIFACT_ID_RE = re.compile(r"^art_[a-z0-9][a-z0-9:._-]{7,127}$")
SESSION_ID_RE = re.compile(r"^ses_[a-z0-9]{16,64}$")
TIME_ZONE_RE = re.compile(r"^(?:UTC|[A-Za-z][A-Za-z0-9_+-]*(?:/[A-Za-z0-9_+-]+)+)$")
JSON_POINTER_RE = re.compile(r"^(?:/(?:[^~/]|~[01])*)+$")

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


def is_nonempty_string_list(v):
    return is_nonempty_list(v) and all(
        isinstance(item, str) and bool(item.strip()) for item in v
    )


def check_schema(kind, payload, r):
    schema = payload.get("schema")
    if schema is not None and (not isinstance(schema, str) or not schema.strip()):
        r.error("'schema' must be a non-empty string when present (or omit it).")
    elif schema is not None and schema != EXPECTED_SCHEMAS[kind]:
        r.error(
            f"schema {schema!r} is not the documented legacy schema "
            f"{EXPECTED_SCHEMAS[kind]!r}."
        )


def validate_media(media, where, r):
    if not isinstance(media, dict):
        r.error(f"{where}: exercise must include a 'media' object with video guidance.")
        return

    url = media.get("explainerUrl")
    if not isinstance(url, str) or not url.strip():
        r.error(f"{where}.media: missing YouTube Shorts 'explainerUrl'.")
    elif YOUTUBE_SHORT_URL_RE.fullmatch(url.strip()) is None:
        r.error(
            f"{where}.media.explainerUrl: must be a canonical YouTube Shorts URL "
            "like https://www.youtube.com/shorts/AbCdEf123_-."
        )
    if "youtubeUrl" in media or "videoUrl" in media:
        r.error(
            f"{where}.media: use only canonical 'explainerUrl'; "
            "youtubeUrl/videoUrl aliases are invalid for generated plans."
        )

    if not isinstance(media.get("setup"), str) or not media["setup"].strip():
        r.error(f"{where}.media: 'setup' must be a non-empty string.")
    for field in ("cues", "commonMistakes"):
        if not is_nonempty_string_list(media.get(field)):
            r.error(f"{where}.media: '{field}' must be a non-empty string list.")


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
    validate_media(ex.get("media"), where, r)


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
    if not isinstance(rounds, int) or isinstance(rounds, bool) or rounds < 1:
        r.error(f"{where}: {item_type} 'rounds' must be an integer >= 1.")
    group_rest = item.get("restSeconds")
    if (
        not isinstance(group_rest, int)
        or isinstance(group_rest, bool)
        or group_rest < 0
    ):
        r.error(f"{where}: {item_type} 'restSeconds' must be an integer >= 0.")
    if item_type == "superset" and len(exercises) != 2:
        r.error(f"{where}: superset must contain exactly 2 exercises.")
    if item_type == "circuit" and len(exercises) < 3:
        r.error(f"{where}: circuit must contain at least 3 exercises.")
    if not item.get("groupId"):
        r.warn(f"{where}: grouped item should include stable 'groupId'.")
    for i, ex in enumerate(exercises):
        if isinstance(ex, dict):
            child_sets = ex.get("sets")
            if child_sets not in (None, 1) or isinstance(child_sets, bool):
                r.error(
                    f"{where} {item_type}.exercise[{i}]: child 'sets' must be 1 "
                    "or omitted; group 'rounds' owns repetition."
                )
            child_rest = ex.get("restSeconds")
            if (
                not isinstance(child_rest, int)
                or isinstance(child_rest, bool)
                or child_rest < 0
            ):
                r.error(
                    f"{where} {item_type}.exercise[{i}]: child 'restSeconds' "
                    "must be an integer >= 0."
                )
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
    valid_duration = isinstance(dw, int) and not isinstance(dw, bool) and dw >= 1
    if not valid_duration:
        r.error("block 'durationWeeks' must be an integer >= 1 (app discards this).")
    current_week = block.get("currentWeek")
    if (
        not isinstance(current_week, int)
        or isinstance(current_week, bool)
        or current_week < 1
        or (valid_duration and current_week > dw)
    ):
        r.error("block 'currentWeek' must be an integer within the declared block.")
    for field in ("weeklyFocus", "measurableTargets"):
        if not is_nonempty_string_list(block.get(field)):
            r.error(f"block '{field}' must be a non-empty string list.")
    workouts = block.get("workouts")
    if not is_nonempty_list(workouts):
        r.error("block 'workouts' must be a non-empty list (app discards this).")
    else:
        covered_weeks = set()
        for i, w in enumerate(workouts):
            validate_workout(w, f"workout[{i}]", r)
            if not isinstance(w, dict):
                continue
            week = w.get("week")
            if not isinstance(week, int) or isinstance(week, bool):
                r.error(f"workout[{i}]: 'week' must be an integer.")
            elif not valid_duration or not 1 <= week <= dw:
                r.error(f"workout[{i}]: 'week' is outside the declared block.")
            else:
                covered_weeks.add(week)
        if valid_duration:
            missing_weeks = sorted(set(range(1, dw + 1)) - covered_weeks)
            if missing_weeks:
                r.error(
                    "block has no workout for declared week(s): "
                    + ", ".join(str(week) for week in missing_weeks)
                    + "."
                )
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
    # The legacy body has no hard import fields documented here. Check usefulness.
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


def parse_contract_time(value):
    if not isinstance(value, str):
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def is_contract_integer(value, minimum=None, maximum=None):
    if not isinstance(value, int) or isinstance(value, bool):
        return False
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def require_exact_keys(value, expected, where, errors):
    if not isinstance(value, dict):
        errors.append(f"{where} must be an object")
        return False
    missing = sorted(expected - set(value), key=str)
    unexpected = sorted(set(value) - expected, key=str)
    if missing:
        errors.append(f"{where} is missing {', '.join(missing)}")
    if unexpected:
        errors.append(f"{where} has unexpected fields {', '.join(unexpected)}")
    return not missing and not unexpected


def source_record_errors(source, generated_at, index):
    where = f"sources[{index}]"
    errors = []
    if not require_exact_keys(source, SOURCE_KEYS, where, errors):
        return errors

    if not isinstance(source["kind"], str) or source["kind"] not in SOURCE_KINDS:
        errors.append(f"{where}.kind is invalid")
    if (
        not isinstance(source["path"], str)
        or not 1 <= len(source["path"]) <= 256
        or JSON_POINTER_RE.fullmatch(source["path"]) is None
    ):
        errors.append(f"{where}.path must be an RFC 6901 JSON Pointer")
    fields = source["fields"]
    if (
        not is_nonempty_list(fields)
        or any(
            not isinstance(field, str)
            or not 1 <= len(field) <= 160
            or JSON_POINTER_RE.fullmatch(field) is None
            for field in fields
        )
        or len(set(fields)) != len(fields)
    ):
        errors.append(f"{where}.fields must contain unique RFC 6901 JSON Pointers")

    freshness = source["freshness"]
    if not require_exact_keys(
        freshness,
        {"evaluatedAt", "maxAgeSeconds", "status"},
        f"{where}.freshness",
        errors,
    ):
        return errors
    evaluated_at = parse_contract_time(freshness["evaluatedAt"])
    received_at = parse_contract_time(source["receivedAt"])
    max_age = freshness["maxAgeSeconds"]
    if evaluated_at is None:
        errors.append(f"{where}.freshness.evaluatedAt is not a timezone-aware timestamp")
    if received_at is None:
        errors.append(f"{where}.receivedAt is not a timezone-aware timestamp")
    if not is_contract_integer(max_age, 1, 86400):
        errors.append(f"{where}.freshness.maxAgeSeconds must be within 1..86400")

    availability = source["availability"]
    if not isinstance(availability, str) or availability not in {"available", "missing", "unknown"}:
        errors.append(f"{where}.availability is invalid")
        return errors

    if availability == "available":
        source_time = parse_contract_time(source["sourceTime"])
        if not isinstance(source["sourceId"], str) or SOURCE_ID_RE.fullmatch(source["sourceId"]) is None:
            errors.append(f"{where}.sourceId is invalid for an available source")
        if source_time is None:
            errors.append(f"{where}.sourceTime is required and must be timezone-aware")
        source_revision = source["sourceRevision"]
        artifact_id = source["artifactId"]
        valid_revision = (
            isinstance(source_revision, str)
            and SOURCE_REVISION_RE.fullmatch(source_revision) is not None
        )
        valid_artifact = (
            isinstance(artifact_id, str)
            and ARTIFACT_ID_RE.fullmatch(artifact_id) is not None
        )
        if source_revision is not None and not valid_revision:
            errors.append(f"{where}.sourceRevision is invalid")
        if artifact_id is not None and not valid_artifact:
            errors.append(f"{where}.artifactId is invalid")
        if not valid_revision:
            errors.append(f"{where} needs an immutable sourceRevision")
        if (
            not isinstance(freshness["status"], str)
            or freshness["status"] not in {"fresh", "stale"}
        ):
            errors.append(f"{where}.freshness.status is invalid for an available source")
        if source_time is not None and received_at is not None and evaluated_at is not None and generated_at:
            if not source_time <= received_at <= evaluated_at <= generated_at:
                errors.append(f"{where} source/received/evaluated/generated order is invalid")
            elif is_contract_integer(max_age, 1, 86400):
                expected = "fresh" if (evaluated_at - source_time).total_seconds() <= max_age else "stale"
                if freshness["status"] != expected:
                    errors.append(f"{where}.freshness.status does not match source age")
    else:
        for field in ("sourceId", "sourceRevision", "artifactId", "sourceTime"):
            if source[field] is not None:
                errors.append(f"{where}.{field} must be null when the source is not available")
        if freshness["status"] != "unknown":
            errors.append(f"{where}.freshness.status must be unknown when unavailable")
        if received_at is not None and evaluated_at is not None and generated_at:
            if not received_at <= evaluated_at <= generated_at:
                errors.append(f"{where} received/evaluated/generated order is invalid")
    return errors


def target_errors(target):
    errors = []
    if not require_exact_keys(target, {"localDate", "timeZone", "sessionId"}, "target", errors):
        return errors
    try:
        valid_date = (
            isinstance(target["localDate"], str)
            and date.fromisoformat(target["localDate"]).isoformat() == target["localDate"]
        )
    except ValueError:
        valid_date = False
    if not valid_date:
        errors.append("target.localDate is not a canonical ISO date")
    if not isinstance(target["timeZone"], str) or TIME_ZONE_RE.fullmatch(target["timeZone"]) is None:
        errors.append("target.timeZone is not an IANA time zone")
    session_id = target["sessionId"]
    if session_id is not None and (
        not isinstance(session_id, str) or SESSION_ID_RE.fullmatch(session_id) is None
    ):
        errors.append("target.sessionId is invalid")
    return errors


def accepted_state_comparison_errors(document):
    errors = []
    if not require_exact_keys(document, ACCEPTED_STATE_KEYS, "accepted_state", errors):
        return errors
    if document["schema"] != CONTRACT_SCHEMA or document["contractVersion"] != CONTRACT_VERSION:
        errors.append("accepted_state contract identity is invalid")
    if document["messageType"] != "accepted_state" or document["producer"] != "phone":
        errors.append("accepted_state must be phone-authored")
    if (
        not isinstance(document["contextRevision"], str)
        or CONTEXT_REVISION_RE.fullmatch(document["contextRevision"]) is None
    ):
        errors.append("accepted_state.contextRevision is invalid")
    generated_at = parse_contract_time(document["generatedAt"])
    if generated_at is None:
        errors.append("accepted_state.generatedAt is not a timezone-aware timestamp")
    errors.extend(target_errors(document["target"]))

    active_id = document["activeSessionId"]
    active = document["activeSession"]
    if active_id is None:
        if active is not None:
            errors.append("activeSession must be null when activeSessionId is null")
    elif not isinstance(active_id, str) or SESSION_ID_RE.fullmatch(active_id) is None:
        errors.append("activeSessionId is invalid")
    elif not isinstance(active, dict) or set(active) != {"sessionId", "startedAt"}:
        errors.append("activeSession must contain sessionId and startedAt")
    else:
        if active["sessionId"] != active_id:
            errors.append("activeSessionId does not match activeSession.sessionId")
        if parse_contract_time(active["startedAt"]) is None:
            errors.append("activeSession.startedAt is not a timezone-aware timestamp")

    state = document["state"]
    if not isinstance(state, dict):
        errors.append("accepted_state.state must be an object")
        return errors
    required_state = {"activeBlock", "nextWorkout", "goals", "constraints", "standingConsents"}
    missing_state = sorted(required_state - set(state))
    if missing_state:
        errors.append(f"accepted_state.state is missing {', '.join(missing_state)}")
    for field in ("activeBlock", "nextWorkout", "goals"):
        if field in state and state[field] is not None and not isinstance(state[field], dict):
            errors.append(f"accepted_state.state.{field} must be an object or null")
    if "constraints" in state and (
        not isinstance(state["constraints"], list)
        or any(not isinstance(item, dict) for item in state["constraints"])
    ):
        errors.append("accepted_state.state.constraints must be an array of objects")
    if "standingConsents" in state and (
        not isinstance(state["standingConsents"], list)
        or any(not isinstance(item, dict) for item in state["standingConsents"])
    ):
        errors.append("accepted_state.state.standingConsents must be an array of objects")

    sources = document["sources"]
    if not is_nonempty_list(sources):
        errors.append("accepted_state.sources must be a non-empty array")
        return errors
    for index, source in enumerate(sources):
        errors.extend(source_record_errors(source, generated_at, index))

    for field, value in state.items():
        escaped = field.replace("~", "~0").replace("/", "~1")
        pointer = f"/state/{escaped}"
        covering = [
            source for source in sources
            if isinstance(source, dict)
            and isinstance(source.get("fields"), list)
            and pointer in source["fields"]
        ]
        if not covering:
            errors.append(f"accepted_state{pointer} has no field-level provenance")
        elif value is not None and not any(source.get("availability") == "available" for source in covering):
            errors.append(f"accepted_state{pointer} has no available provenance source")
    return errors


def planning_context_comparison_errors(document):
    errors = []
    if not require_exact_keys(document, PLANNING_CONTEXT_KEYS, "planning_context", errors):
        return errors
    if document["schema"] != CONTRACT_SCHEMA or document["contractVersion"] != CONTRACT_VERSION:
        errors.append("planning_context contract identity is invalid")
    if document["messageType"] != "planning_context" or document["producer"] != "server":
        errors.append("planning_context must be server-authored")
    generated_at = parse_contract_time(document["generatedAt"])
    if generated_at is None:
        errors.append("planning_context.generatedAt is not a timezone-aware timestamp")
    for field in ("proposals", "appliedReceipts", "currentRequests", "requestHistory"):
        if not isinstance(document[field], list):
            errors.append(f"planning_context.{field} must be an array")
    accepted = document["acceptedState"]
    errors.extend(accepted_state_comparison_errors(accepted))
    accepted_generated = parse_contract_time(accepted.get("generatedAt")) if isinstance(accepted, dict) else None
    if generated_at is not None and accepted_generated is not None and accepted_generated > generated_at:
        errors.append("accepted_state cannot be newer than its planning_context")
    return errors


def accepted_comparison_scope(recent_context, r):
    """Return only structurally valid, provenance-covered phone-accepted state."""
    if not isinstance(recent_context, dict):
        r.warn("recent comparison input is not a contract object; comparison skipped.")
        return {}

    is_contract_v1 = (
        recent_context.get("schema") == "t4l.coaching-contract.v1"
        and recent_context.get("contractVersion") == "1.0.0"
    )
    if is_contract_v1 and recent_context.get("messageType") == "accepted_state":
        errors = accepted_state_comparison_errors(recent_context)
        if not errors:
            return recent_context["state"]
        r.warn(
            "recent comparison accepted_state has invalid contract structure or provenance; "
            f"comparison skipped ({errors[0]})."
        )
        return {}

    if is_contract_v1 and recent_context.get("messageType") == "planning_context":
        errors = planning_context_comparison_errors(recent_context)
        if not errors:
            return recent_context["acceptedState"]["state"]
        r.warn(
            "recent comparison planning_context has invalid contract structure or provenance; "
            f"comparison skipped ({errors[0]})."
        )
        return {}

    if recent_context.get("schema") == "planning_context.v1":
        r.warn(
            "legacy planning_context.v1 does not prove accepted-state provenance; "
            "comparison is skipped and agent result slots are ignored."
        )
        return {}

    r.warn("recent comparison input is not coaching contract v1 accepted state; comparison skipped.")
    return {}


def validate_recent_comparison(kind, payload, recent_context, r):
    """Warn about obvious stale repeats. Human judgment still owns safe novelty."""
    recent_context = accepted_comparison_scope(recent_context, r)
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
    check_schema(kind, payload, r)
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
        print(f"\n{len(r.errors)} error(s) — this {kind} violates legacy body rules. Fix and re-validate.")
        return 1
    suffix = f" ({len(r.warns)} warning(s))." if r.warns else "."
    print(f"OK: {kind} passes legacy payload-body checks{suffix} Phone application is unconfirmed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

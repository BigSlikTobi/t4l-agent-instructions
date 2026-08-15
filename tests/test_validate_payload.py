import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "t4l-write-results" / "scripts" / "validate_payload.py"
ACCEPTED_STATE_FIXTURE = (
    ROOT / "tests" / "fixtures" / "coaching_contract" / "must_accept" / "accepted_state_fresh.json"
)
SPEC = importlib.util.spec_from_file_location("validate_payload", SCRIPT)
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def exercise(exercise_id, reps="8", load="moderate"):
    return {
        "exerciseId": exercise_id,
        "name": exercise_id.replace("_", " ").title(),
        "sets": 3,
        "reps": reps,
        "targetLoad": load,
        "targetRpe": 7,
        "restSeconds": 90,
        "coachCue": "Move with control.",
        "media": {
            "explainerUrl": "https://www.youtube.com/shorts/C_VtOYc6j5c",
            "setup": "Set a stable start position.",
            "cues": ["Move with control"],
            "commonMistakes": ["Rushing the movement"],
        },
    }


def group_exercise(exercise_id, reps="8", load="moderate"):
    child = exercise(exercise_id, reps=reps, load=load)
    child["sets"] = 1
    return child


def workout(title="Lower Build", exercises=None):
    return {
        "id": title.lower().replace(" ", "_"),
        "week": 1,
        "day": 1,
        "title": title,
        "focus": "Lower-body strength",
        "rationale": "Keep the squat anchor and add a new carry challenge.",
        "conditioning": "",
        "exercises": exercises or [exercise("goblet_squat"), exercise("split_squat")],
    }


def accepted_context(state):
    context = json.loads(ACCEPTED_STATE_FIXTURE.read_text(encoding="utf-8"))
    context["state"].update(state)
    available_source = next(
        source for source in context["sources"] if source["availability"] == "available"
    )
    covered_fields = {
        field
        for source in context["sources"]
        for field in source["fields"]
    }
    required_pointers = {
        "/state/" + field.replace("~", "~0").replace("/", "~1")
        for field in context["state"]
    }
    available_source["fields"].extend(sorted(required_pointers - covered_fields))
    return context


def planning_context(accepted_state):
    return {
        "schema": "t4l.coaching-contract.v1",
        "contractVersion": "1.0.0",
        "messageType": "planning_context",
        "producer": "server",
        "generatedAt": "2026-08-01T08:01:00Z",
        "acceptedState": accepted_state,
        "proposals": [],
        "appliedReceipts": [],
        "currentRequests": [],
        "requestHistory": [],
    }


class TrainingPayloadQualityTests(unittest.TestCase):
    def test_exercise_requires_complete_https_video_media(self):
        candidate = exercise("goblet_squat")
        candidate.pop("media")
        report = VALIDATOR.Report()

        VALIDATOR.validate_next_day_plan({"workout": workout(exercises=[candidate])}, report)

        self.assertTrue(any("media" in error for error in report.errors))

        candidate["media"] = {
            "explainerUrl": "https://www.youtube.com/watch?v=C_VtOYc6j5c",
            "setup": "",
            "cues": [],
            "commonMistakes": [],
        }
        report = VALIDATOR.Report()
        VALIDATOR.validate_next_day_plan({"workout": workout(exercises=[candidate])}, report)

        self.assertTrue(any("canonical YouTube Shorts URL" in error for error in report.errors))
        self.assertTrue(any("'setup'" in error for error in report.errors))
        self.assertTrue(any("'cues'" in error for error in report.errors))
        self.assertTrue(any("'commonMistakes'" in error for error in report.errors))

    def test_exercise_rejects_web_pages_and_legacy_video_aliases(self):
        for invalid_url in (
            "https://www.nasm.org/exercises/goblet-squat",
            "https://youtu.be/C_VtOYc6j5c",
            "https://www.youtube.com/watch?v=C_VtOYc6j5c",
            "https://www.youtube.com/shorts/not-a-valid-id",
        ):
            with self.subTest(invalid_url=invalid_url):
                candidate = exercise("goblet_squat")
                candidate["media"]["explainerUrl"] = invalid_url
                report = VALIDATOR.Report()

                VALIDATOR.validate_next_day_plan(
                    {"workout": workout(exercises=[candidate])}, report
                )

                self.assertTrue(
                    any("canonical YouTube Shorts URL" in error for error in report.errors)
                )

        candidate = exercise("goblet_squat")
        candidate["media"]["youtubeUrl"] = "https://www.youtube.com/shorts/C_VtOYc6j5c"
        report = VALIDATOR.Report()

        VALIDATOR.validate_next_day_plan({"workout": workout(exercises=[candidate])}, report)

        self.assertTrue(any("aliases are invalid" in error for error in report.errors))

    def test_full_block_requires_array_metadata_and_every_declared_week(self):
        candidate = {
            "id": "four_week_block",
            "style": "hybrid",
            "title": "Four Week Block",
            "durationWeeks": 4,
            "currentWeek": 1,
            "weeklyFocus": "Build the base",
            "measurableTargets": [],
            "workouts": [workout()],
            "createdBy": "T4L Gym Bro",
            "createdAt": "2026-08-11T08:00:00Z",
        }
        report = VALIDATOR.Report()

        VALIDATOR.validate_training_block_plan(candidate, report)

        self.assertTrue(any("weeklyFocus" in error for error in report.errors))
        self.assertTrue(any("measurableTargets" in error for error in report.errors))
        self.assertTrue(any("2, 3, 4" in error for error in report.errors))

    def test_mixed_flat_superset_and_circuit_items_are_valid(self):
        flat = exercise("deadlift")
        flat["type"] = "exercise"
        superset = {
            "type": "superset",
            "groupId": "ss_1",
            "rounds": 3,
            "restSeconds": 90,
            "exercises": [group_exercise("push_up"), group_exercise("dumbbell_row")],
        }
        circuit = {
            "type": "circuit",
            "groupId": "circuit_1",
            "rounds": 3,
            "restSeconds": 90,
            "exercises": [
                group_exercise("air_squat"),
                group_exercise("mountain_climber"),
                group_exercise("farmer_carry"),
            ],
        }
        candidate = workout()
        candidate.pop("exercises")
        candidate["items"] = [flat, superset, circuit]
        report = VALIDATOR.Report()

        VALIDATOR.validate_next_day_plan({"workout": candidate}, report)

        self.assertFalse(report.errors)

    def test_group_rounds_own_repetition_and_rest_is_explicit(self):
        wrong_child = group_exercise("push_up")
        wrong_child["sets"] = 3
        candidate = workout()
        candidate.pop("exercises")
        candidate["items"] = [{
            "type": "superset",
            "groupId": "ss_wrong",
            "rounds": 3,
            "exercises": [wrong_child, group_exercise("dumbbell_row")],
        }]
        report = VALIDATOR.Report()

        VALIDATOR.validate_next_day_plan({"workout": candidate}, report)

        self.assertTrue(any("group 'rounds' owns repetition" in error for error in report.errors))
        self.assertTrue(any("'restSeconds' must be an integer" in error for error in report.errors))

    def test_circle_alias_is_rejected(self):
        candidate = workout()
        candidate.pop("exercises")
        candidate["items"] = [{"type": "circle", "exercises": []}]
        report = VALIDATOR.Report()

        VALIDATOR.validate_next_day_plan({"workout": candidate}, report)

        self.assertTrue(any('use "circuit", not "circle"' in error for error in report.errors))


class RecentComparisonTests(unittest.TestCase):
    def test_canonical_accepted_state_fixture_is_comparison_safe(self):
        recent = json.loads(ACCEPTED_STATE_FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(VALIDATOR.accepted_state_comparison_errors(recent), [])

    def test_identical_recent_plan_warns_without_failing(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = accepted_context({"acceptedHistory": [payload]})
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertTrue(any("matches a recent exercise order and prescription" in msg for msg in report.warns))
        self.assertTrue(any("workout title" in msg for msg in report.warns))
        self.assertTrue(any("daily motto" in msg for msg in report.warns))

    def test_changed_structure_and_copy_do_not_trigger_repeat_warning(self):
        payload = {
            "workout": workout(
                title="Carry And Climb",
                exercises=[exercise("goblet_squat", reps="10"), exercise("suitcase_carry")],
            ),
            "dailyMotto": "Strong feet, quiet reps.",
        }
        recent = accepted_context({
            "acceptedHistory": [{
                "workout": workout(),
                "dailyMotto": "Own the next rep.",
            }]
        })
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertFalse(report.warns)

    def test_changed_prescription_with_same_order_gets_review_warning(self):
        payload = {
            "workout": workout(
                title="Lower Rep Target",
                exercises=[exercise("goblet_squat", reps="10"), exercise("split_squat", reps="10")],
            ),
            "dailyMotto": "Ten clean reps, no drift.",
        }
        recent = accepted_context({
            "acceptedHistory": [
                {"workout": workout(), "dailyMotto": "Own the next rep."}
            ]
        })
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertTrue(any("repeats a recent exercise order" in msg for msg in report.warns))

    def test_cli_accepts_recent_context_flag_and_keeps_quality_warnings_nonfatal(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = accepted_context({"acceptedHistory": [payload]})
        with tempfile.TemporaryDirectory() as temp_dir:
            payload_path = Path(temp_dir) / "plan.json"
            recent_path = Path(temp_dir) / "planning.json"
            payload_path.write_text(json.dumps(payload), encoding="utf-8")
            recent_path.write_text(json.dumps(recent), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "next_day_plan",
                    str(payload_path),
                    "--recent-context",
                    str(recent_path),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN:", result.stdout)
        self.assertIn("passes legacy payload-body checks", result.stdout)
        self.assertIn("Phone application is unconfirmed", result.stdout)

    def test_repeated_meal_idea_gets_preference_aware_warning(self):
        payload = {
            "signal": "green",
            "todayAdvice": "Add an oat bowl before the evening session.",
            "mealSuggestion": {"name": "Banana oats", "timing": "Pre-workout"},
        }
        recent = accepted_context(
            {"acceptedFuelHistory": [{"mealIdeas": [{"name": "Banana oats"}]}]}
        )
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("fuel_guidance", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertTrue(any("preferred routine" in msg for msg in report.warns))

    def test_unknown_legacy_schema_is_rejected_instead_of_silently_passing(self):
        payload = {"schema": "garbage.v99", "workout": workout()}
        report = VALIDATOR.Report()

        VALIDATOR.check_schema("next_day_plan", payload, report)

        self.assertTrue(any("documented legacy schema" in msg for msg in report.errors))
        self.assertFalse(report.warns)

    def test_legacy_agent_result_slots_are_not_treated_as_accepted_history(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = {
            "schema": "planning_context.v1",
            "dayContext": {},
            "recentLogs": [],
            "nextDayPlan": payload,
            "activeBlock": {"workouts": [workout()]},
        }
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertTrue(any("does not prove accepted-state provenance" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))
        self.assertFalse(any("daily motto" in msg for msg in report.warns))

    def test_unprovenanced_accepted_state_label_is_not_trusted(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = {"messageType": "accepted_state", "state": {"acceptedHistory": [payload]}}
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertTrue(any("not coaching contract v1" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))

    def test_complete_contract_v1_planning_context_is_trusted(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = planning_context(accepted_context({"acceptedHistory": [payload]}))
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertTrue(any("matches a recent exercise order and prescription" in msg for msg in report.warns))
        self.assertFalse(any("invalid contract structure or provenance" in msg for msg in report.warns))

    def test_header_only_pseudo_accepted_state_is_not_trusted(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = {
            "schema": "t4l.coaching-contract.v1",
            "contractVersion": "1.0.0",
            "messageType": "accepted_state",
            "producer": "phone",
            "sources": [{"availability": "available"}],
            "state": {"acceptedHistory": [payload]},
        }
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertTrue(any("invalid contract structure or provenance" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))
        self.assertFalse(any("daily motto" in msg for msg in report.warns))

    def test_non_null_history_without_field_level_provenance_is_not_trusted(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = accepted_context({"acceptedHistory": [payload]})
        for source in recent["sources"]:
            if "/state/acceptedHistory" in source["fields"]:
                source["fields"].remove("/state/acceptedHistory")
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertTrue(any("no field-level provenance" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))

    def test_raw_field_name_is_not_accepted_as_provenance_pointer(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = accepted_context({"acceptedHistory": [payload]})
        available = next(source for source in recent["sources"] if source["availability"] == "available")
        available["fields"].remove("/state/acceptedHistory")
        available["fields"].append("acceptedHistory")
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertTrue(any("RFC 6901" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))

    def test_non_null_history_covered_only_by_unknown_source_is_not_trusted(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = accepted_context({"acceptedHistory": [payload]})
        available, unknown = recent["sources"]
        available["fields"].remove("/state/acceptedHistory")
        unknown["fields"].append("/state/acceptedHistory")
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertTrue(any("no available provenance source" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))

    def test_false_source_freshness_in_accepted_state_is_not_trusted(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = accepted_context({"acceptedHistory": [payload]})
        recent["sources"][0]["freshness"]["status"] = "stale"
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertTrue(any("does not match source age" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))

    def test_incomplete_planning_context_wrapper_is_not_trusted(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = {
            "schema": "t4l.coaching-contract.v1",
            "contractVersion": "1.0.0",
            "messageType": "planning_context",
            "producer": "server",
            "acceptedState": accepted_context({"acceptedHistory": [payload]}),
        }
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertTrue(any("invalid contract structure or provenance" in msg for msg in report.warns))
        self.assertFalse(any("matches a recent exercise" in msg for msg in report.warns))


if __name__ == "__main__":
    unittest.main()

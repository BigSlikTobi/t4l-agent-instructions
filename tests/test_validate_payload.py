import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "t4l-write-results" / "scripts" / "validate_payload.py"
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
    }


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


class RecentComparisonTests(unittest.TestCase):
    def test_identical_recent_plan_warns_without_failing(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = {"nextDayPlan": payload}
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
        recent = {
            "nextDayPlan": {
                "workout": workout(),
                "dailyMotto": "Own the next rep.",
            }
        }
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
        recent = {"nextDayPlan": {"workout": workout(), "dailyMotto": "Own the next rep."}}
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("next_day_plan", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertTrue(any("repeats a recent exercise order" in msg for msg in report.warns))

    def test_cli_accepts_recent_context_flag_and_keeps_quality_warnings_nonfatal(self):
        payload = {"workout": workout(), "dailyMotto": "Own the next rep."}
        recent = {"nextDayPlan": payload}
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
        self.assertIn("passes the app's import rules", result.stdout)

    def test_repeated_meal_idea_gets_preference_aware_warning(self):
        payload = {
            "signal": "green",
            "todayAdvice": "Add an oat bowl before the evening session.",
            "mealSuggestion": {"name": "Banana oats", "timing": "Pre-workout"},
        }
        recent = {"fuelGuidance": {"mealIdeas": [{"name": "Banana oats"}]}}
        report = VALIDATOR.Report()

        VALIDATOR.validate_recent_comparison("fuel_guidance", payload, recent, report)

        self.assertFalse(report.errors)
        self.assertTrue(any("preferred routine" in msg for msg in report.warns))


if __name__ == "__main__":
    unittest.main()

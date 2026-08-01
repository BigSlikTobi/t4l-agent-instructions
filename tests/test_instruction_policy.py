from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


class InstructionPolicyTests(unittest.TestCase):
    def test_canonical_and_portable_daily_rules_keep_safe_novelty(self):
        for relative_path in (
            "docs/coaching_setup.md",
            "skills/t4l-coach-daily/SKILL.md",
        ):
            content = read(relative_path)
            self.assertIn("recent-comparison", content, relative_path)
            self.assertIn("meaningful fresh element", content, relative_path)
            self.assertIn("primary anchors", content, relative_path)
            self.assertIn("injury", content, relative_path)
            self.assertIn("equipment", content, relative_path)
            self.assertIn("preferences", content, relative_path)

    def test_startup_freshness_and_write_paths_all_route_through_comparison(self):
        self.assertIn("Compare the candidate", read("docs/setup_instruction.md"))
        self.assertIn("get_planning_context", read("docs/freshness_rules.md"))
        self.assertIn("--recent-context", read("skills/t4l-write-results/SKILL.md"))

    def test_copyable_payload_examples_are_not_the_banned_stock_lines(self):
        for relative_path in (
            "docs/exchange_contract.md",
            "skills/t4l-write-results/reference/payload-shapes.md",
        ):
            content = read(relative_path)
            self.assertNotIn('"dailyMotto": "Consistency beats intensity."', content)
            self.assertNotIn(
                '"todayAdvice": "Focus on carbs before and protein after your leg session today."',
                content,
            )


if __name__ == "__main__":
    unittest.main()

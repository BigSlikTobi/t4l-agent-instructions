from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "contracts/coaching-contract.v1.schema.json"


def read(relative_path):
    return (ROOT / relative_path).read_text(encoding="utf-8")


class InstructionPolicyTests(unittest.TestCase):
    def test_runtime_loaded_bundle_enforces_training_recovery_only_scope(self):
        loaded_paths = (
            "docs/setup_instruction.md",
            "docs/coaching_setup.md",
            "skills/t4l-onboard-athlete/SKILL.md",
            "skills/t4l-answer-chat/SKILL.md",
            "skills/t4l-write-results/SKILL.md",
            "skills/t4l-write-results/reference/payload-shapes.md",
        )
        combined = "\n".join(read(path) for path in loaded_paths).lower()
        for prohibited_tool in (
            "write_fuel_guidance",
            "write_nutrition_analysis_result",
            "get_nutrition_analysis_request",
            "get_blob_base64",
        ):
            self.assertNotIn(prohibited_tool, combined)
        for prohibited_advice in (
            "add contextual nutrition advice",
            "prefer practical food advice",
            "build nutrition guidance",
            "focus macros",
        ):
            self.assertNotIn(prohibited_advice, combined)
        for boundary_term in (
            "training-and-recovery only",
            "calorie",
            "macro",
            "fluid",
            "electrolyte",
            "supplement",
            "body-composition",
            "registered dietitian or clinician",
        ):
            self.assertIn(boundary_term, combined)

        onboarding = read("skills/t4l-onboard-athlete/SKILL.md")
        self.assertIn('"nutritionPreferences": []', onboarding)
        self.assertIn("wire schema", onboarding)
        self.assertIn("Always send an empty array", onboarding)

    def test_all_active_docs_remove_legacy_nutrition_tool_instructions(self):
        active_paths = (
            "docs/setup_instruction.md",
            "docs/initial_setup.md",
            "docs/coaching_setup.md",
            "docs/exchange_contract.md",
            "skills/t4l-onboard-athlete/SKILL.md",
            "skills/t4l-coach-daily/SKILL.md",
            "skills/t4l-answer-chat/SKILL.md",
            "skills/t4l-write-results/SKILL.md",
            "skills/t4l-write-results/reference/payload-shapes.md",
        )
        for relative_path in active_paths:
            content = read(relative_path)
            self.assertNotIn("write_fuel_guidance", content, relative_path)
            self.assertNotIn(
                "write_nutrition_analysis_result", content, relative_path
            )

    def test_every_entrypoint_routes_to_one_normative_contract(self):
        entrypoints = (
            "README.md",
            "docs/setup_instruction.md",
            "docs/coaching_setup.md",
            "docs/exchange_contract.md",
            "agents/codex/SKILL.md",
            "agents/claude/CLAUDE.md",
            "agents/gemini/GEMINI.md",
            "skills/t4l-onboard-athlete/SKILL.md",
            "skills/t4l-coach-daily/SKILL.md",
            "skills/t4l-answer-chat/SKILL.md",
            "skills/t4l-write-results/SKILL.md",
        )
        for relative_path in entrypoints:
            self.assertIn("coaching-contract.v1.schema.json", read(relative_path), relative_path)

        self.assertTrue((ROOT / CONTRACT).is_file())

    def test_skill_references_resolve_in_the_preserved_repo_layout(self):
        references = {
            "skills/t4l-onboard-athlete/SKILL.md": (
                "../../contracts/coaching-contract.v1.schema.json",
            ),
            "skills/t4l-coach-daily/SKILL.md": (
                "../../contracts/coaching-contract.v1.schema.json",
                "../../docs/coaching_setup.md",
            ),
            "skills/t4l-answer-chat/SKILL.md": (
                "../../contracts/coaching-contract.v1.schema.json",
                "../../docs/exchange_contract.md",
            ),
            "skills/t4l-write-results/SKILL.md": (
                "../../contracts/coaching-contract.v1.schema.json",
                "reference/payload-shapes.md",
            ),
        }
        for relative_path, linked_paths in references.items():
            skill_path = ROOT / relative_path
            content = skill_path.read_text(encoding="utf-8")
            for linked_path in linked_paths:
                self.assertIn(linked_path, content, relative_path)
                self.assertTrue((skill_path.parent / linked_path).resolve().is_file(), linked_path)

        self.assertIn("Do not copy a skill folder by itself", read("docs/initial_setup.md"))

        with tempfile.TemporaryDirectory() as temp_dir:
            install_root = Path(temp_dir) / "skills"
            install_root.mkdir()
            source = ROOT / "skills" / "t4l-coach-daily"
            installed = install_root / source.name
            installed.symlink_to(source, target_is_directory=True)
            for linked_path in references["skills/t4l-coach-daily/SKILL.md"]:
                self.assertTrue((installed / linked_path).resolve().is_file(), linked_path)

    def test_personalized_context_uses_planning_context_not_fictional_direct_reads(self):
        active_paths = (
            "docs/setup_instruction.md",
            "docs/initial_setup.md",
            "docs/coaching_setup.md",
            "docs/freshness_rules.md",
            "skills/t4l-coach-daily/SKILL.md",
            "skills/t4l-answer-chat/SKILL.md",
        )
        banned_calls = (
            "`get_day_context`",
            "`get_app_snapshot`",
            "`get_profile`",
            "`get_daily_snapshot`",
            "`get_coaching_notes`",
            "`get_recent_chat_messages`",
            "`write_coaching_notes`",
        )
        for relative_path in active_paths:
            content = read(relative_path)
            self.assertIn("get_planning_context", content, relative_path)
            for banned_call in banned_calls:
                self.assertNotIn(banned_call, content, relative_path)

    def test_state_claims_keep_proposals_separate_from_phone_application(self):
        for relative_path in (
            "docs/coaching_setup.md",
            "docs/exchange_contract.md",
            "skills/t4l-coach-daily/SKILL.md",
            "skills/t4l-write-results/SKILL.md",
        ):
            content = read(relative_path)
            self.assertIn("proposal", content.lower(), relative_path)
            self.assertIn("applied receipt", content.lower(), relative_path)

        self.assertIn("proposal was stored", read("docs/coaching_setup.md"))
        self.assertIn("application cannot be confirmed", read("skills/t4l-write-results/SKILL.md"))

    def test_chat_policy_binds_exact_turn_and_fails_safe_without_claims(self):
        content = read("skills/t4l-answer-chat/SKILL.md")
        self.assertIn("externally serialized consumer", content)
        self.assertIn("If exclusive ownership cannot be proved, do not\nwrite", content)
        self.assertIn("original `seq` as `inReplyToSeq`", content)
        self.assertIn("Never omit `inReplyToSeq`", content)
        self.assertIn("newer,\nunrelated athlete message", content)
        self.assertIn("do not blindly retry an ambiguous timeout", content)

    def test_review_and_auto_apply_rules_are_consistent(self):
        content = read("docs/coaching_setup.md")
        self.assertIn("full training block always requires explicit review", content)
        self.assertIn("material daily change always requires explicit review", content)
        self.assertIn("Standing consent never waives review", content)
        self.assertIn("matching target local date and timezone", content)
        self.assertIn("unchanged base\n  revision", content)
        self.assertIn("no active-session conflict", content)
        self.assertIn("No proposal may be reviewed or applied at or after its `expiresAt`", content)

    def test_contract_compatibility_uses_exact_versions(self):
        initial = read("docs/initial_setup.md")
        exchange = read("docs/exchange_contract.md")
        self.assertIn("exact contract version", initial)
        self.assertNotIn("contract major version", initial)
        self.assertIn("exact version `1.0.0`", exchange)
        self.assertIn("reject any unadvertised exact version", exchange)

    def test_runtime_limits_are_honest(self):
        content = read("docs/coaching_setup.md")
        self.assertIn("There is no live mid-set guarantee", content)
        self.assertIn("Do not promise a nightly plan", content)
        self.assertIn("runner or heartbeat", content)

    def test_runtime_and_model_choice_remain_customer_configured_metadata(self):
        active_paths = (
            "README.md",
            "docs/setup_instruction.md",
            "docs/initial_setup.md",
            "docs/coaching_setup.md",
            "skills/t4l-onboard-athlete/SKILL.md",
            "skills/t4l-coach-daily/SKILL.md",
            "skills/t4l-answer-chat/SKILL.md",
            "skills/t4l-write-results/SKILL.md",
        )
        for relative_path in active_paths:
            lowered = read(relative_path).lower()
            for provider_specific in ("openai", "deepseek", "gpt-", "luna"):
                self.assertNotIn(provider_specific, lowered, relative_path)

        initial = read("docs/initial_setup.md")
        coaching = read("docs/coaching_setup.md")
        self.assertIn("runtime and model the customer already configured", initial)
        self.assertIn("runtime and model the customer already configured", coaching)
        self.assertIn("Do not switch models", coaching)
        self.assertIn("request provider credentials", coaching)
        self.assertIn("call a\nprovider API directly", coaching)
        self.assertIn("display\nmetadata", coaching)
        self.assertNotIn("Give the athlete the server URL and API key", initial)
        self.assertIn("legacy manual\nURL/API-key path", initial)

    def test_bootstrap_install_is_pinned_deterministic_and_model_free(self):
        initial = read("docs/initial_setup.md")
        root = read("README.md")
        for content in (initial, root):
            self.assertIn("signed release manifest", content)
            self.assertIn("model", content.lower())
        self.assertIn("Never clone or install a mutable branch", initial)
        self.assertIn("there is no T4L relay fallback", initial)
        self.assertIn("The model does not choose releases", initial)
        self.assertIn("one owner-approved, version-pinned", root)

    def test_journal_is_not_normative_or_in_the_required_read_order(self):
        journal = read("docs/journal.md")
        setup = read("docs/setup_instruction.md")
        self.assertIn("Non-Normative", journal)
        self.assertIn("Do not execute rules", journal)
        self.assertIn("Do not use `docs/journal.md` as instructions", setup)

    def test_copyable_payload_examples_are_not_the_banned_stock_lines(self):
        content = read("skills/t4l-write-results/reference/payload-shapes.md")
        self.assertNotIn('"dailyMotto": "Consistency beats intensity."', content)
        self.assertNotIn(
            '"todayAdvice": "Focus on carbs before and protein after your leg session today."',
            content,
        )

    def test_training_writes_require_video_media_and_deliberate_group_selection(self):
        coaching = read("docs/coaching_setup.md")
        writer = read("skills/t4l-write-results/SKILL.md")
        shapes = read("skills/t4l-write-results/reference/payload-shapes.md")

        for content in (coaching, writer, shapes):
            self.assertIn("superset", content)
            self.assertIn("circuit", content)
            self.assertIn("explainerUrl", content)
            self.assertIn("Never invent", content)
        self.assertIn("Every planned exercise", coaching)
        self.assertIn("Every exercise, including every group child", writer)
        self.assertIn("at least one workout for every declared week", writer)
        self.assertIn("it is not rest between sets", writer)
        self.assertIn("Group `restSeconds` applies after the final child", writer)
        self.assertIn("https://www.youtube.com/shorts/<videoId>", coaching)
        self.assertIn("https://www.youtube.com/shorts/<videoId>", writer)
        self.assertNotIn('"explainerUrl": "https://www.youtube.com/watch', shapes)
        self.assertNotIn('"explainerUrl": "https://www.nasm.org', shapes)

    def test_onboarding_writes_strict_pending_draft_and_never_claims_acceptance(self):
        onboarding = read("skills/t4l-onboard-athlete/SKILL.md")
        coaching = read("docs/coaching_setup.md")
        writer = read("skills/t4l-write-results/SKILL.md")
        exchange = read("docs/exchange_contract.md")

        for content in (onboarding, writer, exchange):
            self.assertIn("write_athlete_setup_draft", content)
            self.assertIn("athlete_setup_draft.v1", content)
            self.assertIn("athlete_setup_draft", content)
            self.assertIn("not accepted state", content)
        for required in (
            '"draftId"',
            '"createdAt"',
            '"source"',
            '"profile"',
            '"goals"',
            '"hardLimits"',
            '"nutritionPreferences"',
            '"coachingStyle"',
            '"confirmation"',
        ):
            self.assertIn(required, onboarding)
        self.assertIn("explicitly confirms the summary", onboarding)
        self.assertIn("AgentDescriptor.displayName", coaching)
        self.assertIn("phone controls accepted state", coaching)
        self.assertIn("review-only proposal", coaching)
        self.assertIn("fresh `contextRevision`", coaching)


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path
import re
import json


ROOT = Path(__file__).resolve().parents[1]


def normalized(text):
    return re.sub(r"\s+", " ", text).strip()


def section(text, heading, next_heading):
    start = text.index(heading)
    end = text.index(next_heading, start)
    return normalized(text[start:end])


class ReviewEnvelopeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.implement_skill = (ROOT / "skills/spec-implement/SKILL.md").read_text()

    def test_every_review_uses_a_self_contained_envelope(self):
        required = (
            "review mode",
            "review ID",
            "governing spec path",
            "exact spec slug",
            "governing plan path",
            "spec fingerprint",
            "plan fingerprint",
            "diff base",
            "current review fingerprint",
            "complete changed-file list",
            "stable acceptance criteria",
            "affected criteria",
            "previous spec result",
            "prior quality finding IDs and dispositions",
            "integrated or ad hoc",
            "observed verification commands and proof",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)
                self.assertIn(phrase, self.implement_skill)

    def test_fingerprints_and_changed_files_are_deterministic_and_session_local(self):
        for phrase in (
            "SHA-256",
            "sorted changed-file",
            "session-local",
            "Do not persist",
            "immutable baseline",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)
                self.assertIn(phrase, self.implement_skill)

    def test_current_fingerprint_has_one_tagged_canonical_payload(self):
        for document in (self.review_skill, self.implement_skill):
            contract = normalized(document)
            self.assertIn("canonical payload", contract)
            self.assertIn("review-diff-v1\\0", contract)
            self.assertIn("exact reviewed diff bytes", contract)
            self.assertIn("NUL-delimited sorted changed-file paths", contract)
            self.assertNotIn("revision, tree, or diff", contract)

    def test_invalid_envelopes_block_without_guessing(self):
        for phrase in (
            "missing",
            "internally inconsistent",
            "stale",
            "wrong-spec",
            "BLOCKED",
            "Do not reconstruct",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)

    def test_verification_evidence_is_observed_or_marked_unobserved(self):
        self.assertIn("unobserved", self.review_skill)
        self.assertIn("unobserved", self.implement_skill)
        self.assertIn("described as passing", self.review_skill)


class IncrementalSpecReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.implement_skill = (ROOT / "skills/spec-implement/SKILL.md").read_text()

    def test_initial_mode_is_complete_and_security_preserving(self):
        for phrase in (
            "Mode: initial",
            "every acceptance criterion",
            "complete feature diff",
            "extra scope",
            "security and data-integrity",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)


class QualityConvergenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.implement_skill = (ROOT / "skills/spec-implement/SKILL.md").read_text()

    def test_important_findings_are_grouped_and_evidence_based(self):
        for phrase in (
            "stable finding ID",
            "violated invariant",
            "reachable",
            "concrete impact",
            "existing\nvalidation",
            "Variants checked:",
            "root-cause remedy",
            "duplicate archive members",
            "partial\nwrites",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)


class ReviewerPromptContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec_agent = (ROOT / "agents/review-spec.md").read_text()
        cls.quality_agent = (ROOT / "agents/review-quality.md").read_text()
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.implement_skill = (ROOT / "skills/spec-implement/SKILL.md").read_text()

    def test_locked_models_and_read_only_permissions_are_preserved(self):
        self.assertIn("model: ibm-ica/gpt-5.6-luna", self.spec_agent)
        self.assertIn("model: ibm-ica/gpt-5.6-sol", self.quality_agent)
        for agent in (self.spec_agent, self.quality_agent):
            self.assertIn("temperature: 0", agent)
            for permission in ("edit: deny", "bash: deny", "task: deny", "question: deny"):
                with self.subTest(permission=permission):
                    self.assertIn(permission, agent)

    def test_both_reviewers_validate_envelopes_and_block_bad_context(self):
        for agent in (self.spec_agent, self.quality_agent):
            for phrase in (
                "review envelope",
                "first",
                "BLOCKED",
                "wrong spec",
                "stale",
                "Do not reconstruct",
                "changed-file list",
                "unobserved",
            ):
                with self.subTest(phrase=phrase):
                    self.assertIn(phrase, agent)

    def test_spec_reviewer_has_initial_and_incremental_boundaries(self):
        for phrase in (
            "initial",
            "every acceptance criterion",
            "complete feature\n  diff",
            "incremental",
            "affected criteria",
            "Carried forward",
            "extra scope",
            "MISSING",
            "EXTRA",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.spec_agent)

    def test_quality_reviewer_requires_same_state_pass_and_targeted_follow_up(self):
        for phrase in (
            "fresh spec PASS",
            "same governing spec",
            "same reviewed state",
            "initial",
            "follow-up",
            "stable finding ID",
            "invariant",
            "Important regressions",
            "unrelated Minor or Nitpick",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.quality_agent)

    def test_initial_important_findings_are_one_batch(self):
        for phrase in (
            "fix all",
            "select finding IDs",
            "appeal",
            "accept documented risk",
            "one batch",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.implement_skill)

    def test_follow_up_is_targeted(self):
        for phrase in (
            "Mode: follow-up",
            "accepted Important finding IDs",
            "Important regressions",
            "unchanged code",
            "unrelated Minor or Nitpick",
            "verified as resolved",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)


class AdHocCompatibilityContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = (ROOT / "commands/review.md").read_text()
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.implement_skill = (ROOT / "skills/spec-implement/SKILL.md").read_text()

    def test_review_command_constructs_an_ad_hoc_envelope(self):
        self.assertIn("agent: build", self.command)
        for phrase in (
            "advisory",
            "read-only",
            "pasted\ndiff",
            "acceptance criteria",
            "ad-hoc review envelope",
            "spec-first",
            "fresh spec PASS",
            "requested severities",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.command)

    def test_ad_hoc_mode_does_not_require_integrated_plan_state(self):
        for phrase in (
            "explicit ad-hoc markers",
            "does not require a\ngoverning plan",
            "all requested severities",
            "remains advisory",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)

    def test_existing_risk_gate_and_legacy_handling_remain(self):
        for phrase in (
            "mandatory for every L-sized task",
            "mandatory for every M-sized task",
            "security`, `data`, `concurrency`, or",
            "optional",
            "S-sized tasks tagged",
            "legacy task that omits risk",
            "Risk is read from the plan and never inferred",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)
        self.assertIn("legacy task has no risk tag", self.implement_skill)
        self.assertIn("Never infer risk", self.implement_skill)


class CrossWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.implement_skill = (ROOT / "skills/spec-implement/SKILL.md").read_text()
        cls.tests_readme = (ROOT / "tests/README.md").read_text()

    def test_spec_first_review_still_precedes_staging(self):
        spec_gate = self.implement_skill.index("### Step 5.5 — Run the Code-Review Gate")
        staging = self.implement_skill.index("### Step 6 — Stage Changes")
        self.assertLess(spec_gate, staging)
        self.assertIn("runs `review-spec` first", self.implement_skill)
        self.assertIn("only after a fresh spec `PASS`", self.implement_skill)

    def test_current_pass_staleness_does_not_discard_valid_baseline(self):
        for document in (self.review_skill, self.implement_skill):
            contract = normalized(document).lower()
            self.assertIn("remediation stales the current spec pass", contract)
            self.assertIn("preserves the immutable baseline", contract)
            self.assertIn("spec or plan change invalidates both", contract)
            self.assertNotIn("any implementation or plan change makes the baseline stale", contract)

    def test_quality_template_and_prompt_both_require_summary(self):
        quality_stage = section(
            self.review_skill,
            "## Step 4 — Run Quality Review After PASS",
            "## Step 5 — Return the Gate Result",
        )
        self.assertIn("Summary: <concise judgment>", quality_stage)
        quality_prompt = normalized((ROOT / "agents/review-quality.md").read_text())
        self.assertIn("concise summary", quality_prompt)

    def test_high_risk_rules_are_scoped_and_non_contradictory(self):
        spec_stage = section(
            self.review_skill,
            "## Step 2 — Run Spec Review",
            "## Step 3 — Apply the Spec Gate",
        )
        quality_stage = section(
            self.review_skill,
            "## Step 4 — Run Quality Review After PASS",
            "## Step 5 — Return the Gate Result",
        )
        integration = section(
            self.implement_skill,
            "### Step 5.5 — Run the Code-Review Gate",
            "### Step 6 — Stage Changes",
        )
        self.assertIn("initial mode", spec_stage.lower())
        self.assertIn("every acceptance criterion", spec_stage)
        self.assertIn("incremental mode", spec_stage.lower())
        self.assertIn("remediation diff", spec_stage)
        self.assertNotIn("carry forward when impact is uncertain", spec_stage.lower())
        self.assertIn("follow-up quality mode", quality_stage.lower())
        self.assertIn("do not restart unrestricted review", quality_stage.lower())
        self.assertNotIn("follow-up may review unchanged code", quality_stage.lower())
        self.assertIn("Allow at most two remediation and follow-up rounds", integration)
        self.assertIn("After round two, stop automatic iteration", integration)

    def test_required_workflow_skills_and_commands_still_exist(self):
        for path in (
            "skills/spec-define/SKILL.md",
            "skills/spec-plan/SKILL.md",
            "skills/spec-implement/SKILL.md",
            "skills/code-review/SKILL.md",
            "skills/debug/SKILL.md",
            "commands/define.md",
            "commands/plan.md",
            "commands/implement.md",
            "commands/review.md",
            "commands/debug.md",
        ):
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file())

    def test_contract_tests_document_evidence_limits(self):
        self.assertIn("test_code_review_workflow.py", self.tests_readme)
        self.assertIn("Markdown contract tests", self.tests_readme)
        self.assertIn("do not prove runtime", self.tests_readme)
        self.assertIn("observed\ncommand output", self.tests_readme)


class ReviewReadmeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = (ROOT / "README.md").read_text()
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.implement_skill = (ROOT / "skills/spec-implement/SKILL.md").read_text()

    def test_readme_explains_modes_and_initial_coverage(self):
        for phrase in (
            "Initial review",
            "Incremental review",
            "Follow-up quality",
            "complete feature diff",
            "security and data-integrity",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.readme)

    def test_readme_explains_envelope_and_spec_first_gate(self):
        for phrase in (
            "self-contained review envelope",
            "stable criterion",
            "fingerprints",
            "wrong-spec",
            "fresh spec PASS",
            "read-only",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.readme)

    def test_readme_explains_blocking_batching_and_convergence(self):
        for phrase in (
            "unresolved Important",
            "Minor",
            "advisory",
            "Nitpick",
            "hidden by default",
            "one batch",
            "two remediation",
            "explicit\nuser decision",
            "`/review`",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.readme)

    def test_only_important_blocks_integrated_staging(self):
        for phrase in (
            "only unresolved `Important`",
            "Minor",
            "advisory",
            "Nitpick",
            "hidden by default",
            "pure style preferences",
            "pre-existing",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)

    def test_finding_identity_and_two_round_limit_converge(self):
        for phrase in (
            "equivalent finding",
            "retain its existing finding ID",
            "do not reset",
            "at most two remediation",
            "accept remaining risk",
            "revise the\nimplementation",
            "revise the spec or plan",
            "stop implementation",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.implement_skill)

    def test_quality_report_has_mode_status_and_grouped_fields(self):
        for phrase in (
            "Status: PASS|IMPORTANT_FINDINGS",
            "Invariant:",
            "Path:",
            "Impact:",
            "Variants checked:",
            "Remedy:",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)

    def test_legacy_criteria_receive_stable_session_ids(self):
        for phrase in (
            "descriptive criterion IDs",
            "normalized criterion text",
            "collision\nsuffix",
            "legacy",
            "Do not rewrite",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)

    def test_incremental_mode_maps_direct_and_transitive_impact(self):
        for phrase in (
            "Mode: incremental",
            "remediation diff",
            "interface",
            "permission boundary",
            "data contract",
            "error\ncontract",
            "output contract",
            "MISSING or EXTRA",
            "impact reasons",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)

    def test_carry_forward_and_fallback_are_bounded(self):
        for phrase in (
            "Carried forward:",
            "baseline spec review passed",
            "full initial review",
            "Extra work in remediation: NONE",
            "uncertain",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)
                self.assertIn(phrase, self.implement_skill)

    def test_spec_result_formats_are_concise(self):
        for phrase in (
            "Criteria: <met>/<total> MET",
            "Evidence groups:",
            "Baseline fingerprint:",
            "Revalidated:",
            "detail only",
            "Current review fingerprint:",
            "Immutable baseline fingerprint:",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.review_skill)


class DeterministicReviewScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture_path = ROOT / "tests/fixtures/code_review/scenarios.json"
        cls.scenarios = {case["id"]: case for case in json.loads(fixture_path.read_text())}

    def assert_case(self, case_id, expected):
        self.assertIn(case_id, self.scenarios)
        self.assertEqual(expected, self.scenarios[case_id]["expected"])

    def test_initial_and_incremental_selection_cases(self):
        self.assert_case("initial-full-review", "initial")
        self.assert_case("valid-remediation-baseline", "incremental")
        self.assert_case("stale-spec-fingerprint", "fallback-initial")
        self.assert_case("invalid-diff-base", "fallback-initial")

    def test_transitive_impact_and_carry_forward_cases(self):
        impact = self.scenarios["transitive-impact"]
        self.assertEqual(
            ["interface", "permission", "data", "error", "output"],
            impact["inputs"]["contract_changes"],
        )
        self.assertEqual("revalidate-mapped-criteria", impact["expected"])
        self.assert_case("unaffected-criteria", "carry-forward-count")
        self.assert_case("uncertain-impact", "revalidate")

    def test_invalid_envelope_cases(self):
        self.assert_case("missing-envelope-field", "blocked")
        self.assert_case("wrong-spec-slug", "blocked")
        self.assert_case("contradictory-mode", "blocked")

    def test_grouping_batching_and_follow_up_cases(self):
        self.assert_case("shared-invariant-variants", "one-finding-id")
        self.assert_case("initial-important-findings", "one-user-batch")
        self.assert_case("accepted-finding-follow-up", "verify-ids-and-regressions")
        self.assert_case("unrelated-follow-up-minor", "exclude")

    def test_severity_identity_and_convergence_cases(self):
        self.assert_case("minor-only", "advisory")
        self.assert_case("integrated-nitpick", "hidden")
        self.assert_case("equivalent-recurring-finding", "retain-id-and-round")
        self.assert_case("first-remediation", "allow-targeted-follow-up")
        self.assert_case("second-remediation-unresolved", "stop-for-user-decision")


if __name__ == "__main__":
    unittest.main()

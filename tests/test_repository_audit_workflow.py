import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def normalized(text):
    return re.sub(r"\s+", " ", text).strip()


class AuditWorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.command = (ROOT / "commands/audit.md").read_text()
        cls.skill = (ROOT / "skills/repository-audit/SKILL.md").read_text()
        fixture = ROOT / "tests/fixtures/repository_audit/scenarios.json"
        cls.scenarios = {case["id"]: case for case in json.loads(fixture.read_text())}

    def test_required_contract_phrases_are_present(self):
        documents = {
            "skill": normalized(self.skill),
            "rules": normalized((ROOT / "AGENTS.md").read_text()),
        }
        for case in self.scenarios.values():
            with self.subTest(case=case["id"]):
                contract = documents[case["document"]]
                for expected in case["expected"]:
                    self.assertIn(expected, contract)

    def test_command_routes_to_distinct_audit_skill(self):
        self.assertIn("agent: build", self.command)
        self.assertIn("`repository-audit` skill", self.command)
        self.assertIn("$ARGUMENTS", self.command)
        self.assertNotIn("`code-review` skill", self.command)

    def test_clean_dirty_and_optional_scope_contract(self):
        contract = normalized(self.skill)
        for phrase in (
            "clean or dirty",
            "does not require a diff or acceptance criteria",
            "whole repository",
            "optional directory or concern",
            "attribution context, never the audit boundary",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract)

    def test_instructions_are_inspected_before_code(self):
        contract = normalized(self.skill)
        self.assertLess(contract.index("## 2. Inspect Instructions First"), contract.index("## 3. Gather Evidence"))
        self.assertIn("AGENTS.md", self.skill)
        self.assertIn("report the limitation", contract)

    def test_all_applicable_health_concerns_are_named(self):
        for concern in (
            "correctness", "security", "data integrity", "error handling",
            "maintainability", "duplication", "coupling", "naming", "tests",
            "configuration", "documentation consistency",
        ):
            with self.subTest(concern=concern):
                self.assertIn(concern, self.skill.lower())

    def test_verification_distinguishes_observed_and_unobserved_results(self):
        contract = normalized(self.skill)
        for phrase in (
            "non-destructive tests and validation commands",
            "Observed verification",
            "Unobserved recommendations",
            "must not be described as passing",
            "unavailable or not permitted",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract)

    def test_findings_are_deterministic_evidence_based_and_ordered(self):
        contract = normalized(self.skill)
        for phrase in (
            "Important, Minor, then Nitpick",
            "Optional improvements",
            "AUDIT-",
            "not from a line number alone",
            "File and line",
            "Evidence:",
            "Impact:",
            "Remedy:",
            "Findings: NONE",
            "Do not invent findings",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract)

    def test_audit_is_advisory_and_handoff_requires_selection(self):
        contract = normalized(self.skill)
        for phrase in (
            "never edit",
            "never automatically fix",
            "explicitly select stable finding IDs",
            "only selected IDs",
            "separate spec and plan",
            "Do not invoke an edit-capable implementation",
            "Do not persist findings",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract)


class AuditReviewerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = (ROOT / "agents/review-audit.md").read_text()
        cls.skill = (ROOT / "skills/repository-audit/SKILL.md").read_text()

    def test_reviewer_is_dedicated_and_edit_denied(self):
        for phrase in (
            "mode: subagent",
            "model: ibm-ica/gpt-5.6-sol",
            "temperature: 0",
            "read: allow",
            "glob: allow",
            "grep: allow",
            "edit: deny",
            "bash: deny",
            "task: deny",
            "question: deny",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.agent)

    def test_reviewer_covers_pre_existing_health_without_fabrication(self):
        for phrase in (
            "pre-existing code",
            "whole repository",
            "correctness",
            "security",
            "data integrity",
            "error handling",
            "maintainability",
            "duplication",
            "coupling",
            "naming",
            "tests",
            "configuration",
            "documentation consistency",
            "Do not invent findings",
            "Findings: NONE",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.agent)

    def test_reviewer_allows_best_reference_when_line_is_not_verifiable(self):
        contract = normalized(self.agent)
        self.assertIn("when verifiable", contract)
        self.assertIn("best repository reference", contract)
        self.assertIn("location limitation", contract)

    def test_host_executes_commands_and_missing_reviewer_blocks(self):
        contract = normalized(self.skill)
        self.assertIn("The reviewer has no shell access", contract)
        self.assertIn("If it is unavailable, return `BLOCKED`", contract)
        self.assertIn("do not substitute `review-spec` or `review-quality`", contract)


class ReviewPreservationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit_command = (ROOT / "commands/audit.md").read_text()
        cls.review_command = (ROOT / "commands/review.md").read_text()
        cls.review_skill = (ROOT / "skills/code-review/SKILL.md").read_text()
        cls.spec_agent = (ROOT / "agents/review-spec.md").read_text()
        cls.quality_agent = (ROOT / "agents/review-quality.md").read_text()

    def test_review_and_audit_do_not_cross_route(self):
        self.assertNotIn("repository-audit", self.review_command)
        self.assertNotIn("code-review", self.audit_command)

    def test_review_still_requires_diff_criteria_and_spec_first_order(self):
        command = normalized(self.review_command)
        skill = normalized(self.review_skill)
        self.assertIn("diff", command)
        self.assertIn("acceptance criteria", command)
        self.assertIn("complete diff", skill)
        self.assertIn("acceptance criteria", skill)
        self.assertLess(skill.index("review-spec"), skill.index("review-quality"))
        self.assertIn("never apply fixes", command)

    def test_existing_reviewer_models_and_edit_denial_remain(self):
        self.assertIn("model: ibm-ica/gpt-5.6-luna", self.spec_agent)
        self.assertIn("model: ibm-ica/gpt-5.6-sol", self.quality_agent)
        for agent in (self.spec_agent, self.quality_agent):
            self.assertIn("edit: deny", agent)


class ProgressUpdateContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = normalized((ROOT / "AGENTS.md").read_text())

    def test_one_kickoff_and_material_triggers_only(self):
        for phrase in (
            "at most one kickoff update",
            "materially new evidence",
            "a blocker",
            "a changed plan",
            "a user decision",
            "Continue silently when there is no new information",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.rules)

    def test_conclusions_are_combined_and_not_repeated(self):
        for phrase in (
            "Combine related discoveries into one update",
            "Do not restate or paraphrase a conclusion already communicated",
            "Do not repeat progress conclusions in the final response",
            "concise and factual",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, self.rules)


class AuditReadmeContractTests(unittest.TestCase):
    def test_readme_distinguishes_audit_from_review_and_documents_handoff(self):
        readme = normalized((ROOT / "README.md").read_text())
        for phrase in (
            "`/audit`",
            "clean or dirty",
            "whole repository",
            "optional directory or concern",
            "`/review` requires a diff and acceptance criteria",
            "read-only and advisory",
            "Observed verification",
            "Unobserved recommendations",
            "AUDIT-",
            "Findings: NONE",
            "explicitly selected finding IDs",
            "separate spec and plan",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, readme)


if __name__ == "__main__":
    unittest.main()

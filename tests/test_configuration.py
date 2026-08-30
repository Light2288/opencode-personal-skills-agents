import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArtifactHygieneTests(unittest.TestCase):
    def test_runtime_artifacts_are_ignored(self):
        ignored = (ROOT / ".gitignore").read_text()
        for pattern in (
            "docs/evidence/",
            "docs/deliverables/",
            "tests/fixtures/document_workflows/generated/",
            ".venv/",
        ):
            self.assertIn(pattern, ignored)

    def test_runtime_artifacts_are_not_tracked(self):
        tracked = subprocess.run(
            ["git", "ls-files", "docs/evidence", "docs/deliverables"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        self.assertEqual("", tracked)


class ModelConfigurationTests(unittest.TestCase):
    def test_gpt_sol_declares_confirmed_multimodal_inputs(self):
        config = json.loads((ROOT / "opencode.json").read_text())
        model = config["provider"]["ibm-ica"]["models"]["gpt-5.6-sol"]
        self.assertIs(model["attachment"], True)
        self.assertEqual(["text", "image", "pdf"], model["modalities"]["input"])
        self.assertEqual(["text"], model["modalities"]["output"])

    def test_doc_analyst_stays_on_gpt_sol(self):
        definition = (ROOT / "agents/doc-analyst.md").read_text()
        self.assertIn("model: ibm-ica/gpt-5.6-sol", definition)

    def test_haiku_operational_routing_is_replaced_by_gpt_luna(self):
        config = json.loads((ROOT / "opencode.json").read_text())
        models = config["provider"]["ibm-ica"]["models"]
        self.assertIn("gpt-5.6-luna", models)
        self.assertNotIn("claude-haiku-4-5", models)
        self.assertNotIn("gpt-5.6-luna-dzus", models)
        self.assertEqual("ibm-ica/gpt-5.6-luna", config["small_model"])

        operational_files = [ROOT / "opencode.json"]
        for directory in ("agents", "commands", "skills"):
            operational_files.extend((ROOT / directory).rglob("*.md"))
        for path in operational_files:
            content = path.read_text()
            self.assertNotIn("claude-haiku-4-5", content, str(path))
            self.assertNotIn("Claude Haiku 4.5", content, str(path))

        for agent in ("explore", "general", "title", "summary"):
            self.assertEqual("ibm-ica/gpt-5.6-luna", config["agent"][agent]["model"])
        for agent in ("spec-definer", "spec-implementer-lite", "review-spec"):
            self.assertIn("model: ibm-ica/gpt-5.6-luna", (ROOT / "agents" / (agent + ".md")).read_text())


class DocumentWorkerTests(unittest.TestCase):
    def test_worker_is_local_only_and_write_scoped(self):
        definition = (ROOT / "agents/document-worker.md").read_text()
        for expected in (
            "model: ibm-ica/gpt-5.6-sol",
            '"*": deny',
            '"docs/evidence/**": allow',
            '"docs/deliverables/**": allow',
            "glob: deny",
            "grep: deny",
            "bash: deny",
            "task: deny",
            "question: deny",
            "webfetch: deny",
            "untrusted evidence",
        ):
            self.assertIn(expected, definition)
        self.assertNotIn('"docs/analysis/**": allow', definition)
        self.assertNotIn("read: allow", definition)


class CommandRoutingMixin:
    def assert_command_routes_to(self, command, skill):
        definition = (ROOT / "commands" / (command + ".md")).read_text()
        self.assertIn("agent: build", definition)
        self.assertIn("`{}` skill".format(skill), definition)
        self.assertIn("$ARGUMENTS", definition)


class WorkflowRoutingTests(CommandRoutingMixin, unittest.TestCase):

    def test_ingest_routes_to_doc_ingest(self):
        self.assert_command_routes_to("ingest", "doc-ingest")

    def test_ingest_skill_defines_safety_and_evidence_contract(self):
        skill = (ROOT / "skills/doc-ingest/SKILL.md").read_text()
        for expected in (
            "docs/evidence/<topic>/manifest.md",
            "sources/S<n>/",
            "intermediates/S<n>/",
            "document_ingest.py check-dependencies",
            "document_ingest.py normalize",
            "document-worker",
            "COMPLETE",
            "PARTIAL",
            "Requirements",
            "Constraints",
            "Assumptions",
            "Decisions",
            "Risks",
            "Contradictions",
            "Ambiguities",
            "Gaps",
            "Open Questions",
            "untrusted",
            "Never silently overwrite",
        ):
            self.assertIn(expected, skill)


class InstallationAndDocumentationTests(CommandRoutingMixin, unittest.TestCase):
    def test_installer_syncs_tools_without_installing_dependencies(self):
        installer = (ROOT / "install.sh").read_text()
        self.assertIn("SYNC_DIRS=(agents skills commands tools)", installer)
        self.assertNotIn("--delete", installer)
        self.assertNotIn("| grep", installer)
        self.assertNotIn("pip install", installer)
        self.assertNotIn("brew install", installer)
        for exclusion in ("__pycache__/", "*.pyc", "*.pyo"):
            self.assertIn("--exclude '{}'".format(exclusion), installer)
            self.assertEqual(1, installer.count("--exclude '{}'".format(exclusion)))
        self.assertIn("--exclude '.venv/'", installer)

    def test_installer_produces_complete_isolated_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            home = temporary / "home"
            source = temporary / "source"
            shutil.copytree(str(ROOT), str(source), ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "*.pyo"))
            cache = source / "tools/__pycache__"
            cache.mkdir(exist_ok=True)
            (cache / "should-not-install.pyc").write_bytes(b"cache")
            (source / "tools/should-not-install.pyo").write_bytes(b"cache")
            (source / "tools/.venv").mkdir()
            (source / "tools/.venv/secret").write_text("local")
            env = os.environ.copy()
            env["HOME"] = str(home)
            subprocess.run([str(source / "install.sh")], cwd=source, env=env, check=True, capture_output=True, text=True)
            destination = home / ".config/opencode"
            for relative in (
                "agents/document-worker.md",
                "commands/ingest.md",
                "commands/summarize.md",
                "commands/estimate.md",
                "commands/compare.md",
                "skills/doc-ingest/SKILL.md",
                "skills/doc-summarize/SKILL.md",
                "skills/doc-estimate/SKILL.md",
                "skills/arch-compare/SKILL.md",
                "tools/document_ingest.py",
                "opencode.json",
            ):
                self.assertTrue((destination / relative).is_file(), relative)
            self.assertFalse(list(destination.rglob("__pycache__")))
            self.assertFalse(list(destination.rglob("*.pyc")))
            self.assertFalse(list(destination.rglob("*.pyo")))
            self.assertFalse((destination / "tools/.venv").exists())

    def test_installer_preserves_unrelated_files(self):
        with tempfile.TemporaryDirectory() as home:
            unrelated = Path(home) / ".config/opencode/agents/local-only.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("local")
            env = os.environ.copy()
            env["HOME"] = home
            subprocess.run([str(ROOT / "install.sh")], cwd=ROOT, env=env, check=True, capture_output=True, text=True)
            self.assertEqual("local", unrelated.read_text())

    def test_all_command_and_skill_frontmatter_is_bounded(self):
        for path in list((ROOT / "commands").glob("*.md")) + list((ROOT / "skills").glob("*/SKILL.md")):
            text = path.read_text()
            self.assertTrue(text.startswith("---\n"), str(path))
            self.assertIn("\n---\n", text[4:], str(path))

    def test_ingest_writes_normalizer_output_at_evidence_root(self):
        skill = (ROOT / "skills/doc-ingest/SKILL.md").read_text()
        self.assertIn("target to `docs/evidence/<topic>/`", skill)
        self.assertNotIn("--output docs/evidence/<topic>/intermediates", skill)

    def test_ingest_updates_through_fresh_sibling_and_atomic_replacement(self):
        skill = (ROOT / "skills/doc-ingest/SKILL.md").read_text()
        for expected in ("fresh sibling temporary directory", "Promotion renames", "only after successful", "preserve the existing evidence set"):
            self.assertIn(expected, skill)
        self.assertIn("--output docs/evidence/.<topic>-update-<unique>", skill)

    def test_readme_documents_document_workflows(self):
        readme = (ROOT / "README.md").read_text()
        for expected in (
            "Local multimodal document workflows",
            "`/ingest`",
            "`/summarize`",
            "`/estimate`",
            "`/compare`",
            "DOCX",
            "XLSX",
            "PPTX",
            "DOC, XLS, and PPT",
            "docs/evidence/<topic>/",
            "docs/deliverables/",
            "PARTIAL",
            "LibreOffice",
            "restart OpenCode",
            "session_message.seq",
        ):
            self.assertIn(expected, readme)

    def test_analyze_reuses_ingested_evidence_without_duplicate_conversion(self):
        skill = (ROOT / "skills/doc-analyze/SKILL.md").read_text()
        self.assertIn("docs/evidence/<topic>/manifest.md", skill)
        self.assertIn("load and follow the `doc-ingest` skill directly", skill)
        self.assertIn("capture the resulting `docs/evidence/<topic>/` path", skill)
        self.assertNotIn("run `/ingest` first", skill)
        self.assertIn("Do not duplicate conversion", skill)
        self.assertIn("docs/analysis/<topic>.md", skill)

    def test_summary_command_and_templates(self):
        self.assert_command_routes_to("summarize", "doc-summarize")
        skill = (ROOT / "skills/doc-summarize/SKILL.md").read_text()
        for expected in (
            "docs/deliverables/summaries/",
            "meeting|executive|technical|general",
            "Participants",
            "Action Items",
            "Business Impact",
            "Decisions Required",
            "Current State",
            "Architecture",
            "General",
            "document-worker",
            "Every factual statement needs an evidence",
            "citation with source",
            "distinguish facts",
            "source claims, and inference",
            "ask before",
            "overwriting any existing summary",
        ):
            self.assertIn(expected, skill)

    def test_estimate_command_and_contract(self):
        self.assert_command_routes_to("estimate", "doc-estimate")
        skill = (ROOT / "skills/doc-estimate/SKILL.md").read_text()
        for expected in (
            "docs/deliverables/estimates/",
            "Scope",
            "Exclusions",
            "Assumptions",
            "Unresolved Questions",
            "Work Breakdown",
            "Optimistic",
            "Likely",
            "Pessimistic",
            "Estimation Unit",
            "Team Assumptions",
            "Confidence",
            "Dependencies",
            "Risks",
            "Contingency Rationale",
            "Timeline Implications",
            "materially change",
            "false precision",
            "document-worker",
            "ask before",
        ):
            self.assertIn(expected, skill)

    def test_compare_command_and_adr_boundary(self):
        self.assert_command_routes_to("compare", "arch-compare")
        skill = (ROOT / "skills/arch-compare/SKILL.md").read_text()
        for expected in (
            "docs/deliverables/comparisons/",
            "Options",
            "Drivers",
            "Mandatory Constraints",
            "Tradeoffs",
            "Costs",
            "Operational Consequences",
            "Risks",
            "Reversibility",
            "Evidence Gaps",
            "Decision Matrix",
            "score",
            "weight",
            "Sensitivity Analysis",
            "Accepted ADRs",
            "Proposed ADRs",
            "non-authoritative",
            "`/adr`",
            "must not create",
            "document-worker",
        ):
            self.assertIn(expected, skill)
        self.assertIn("primary build host", skill)
        self.assertIn("only ADR paths explicitly selected by the user", skill)
        self.assertIn("pass their content and validated statuses", skill)

    def test_privacy_language_describes_configured_provider_accurately(self):
        paths = (
            "README.md",
            "agents/document-worker.md",
            "skills/doc-ingest/SKILL.md",
            "skills/doc-summarize/SKILL.md",
            "skills/doc-estimate/SKILL.md",
            "skills/arch-compare/SKILL.md",
        )
        combined = "\n".join((ROOT / path).read_text() for path in paths)
        self.assertIn("configured IBM ICA endpoint", combined)
        self.assertIn("approved for that material", combined)
        self.assertIn("no cloud document conversion", combined.lower())
        self.assertIn("webfetch", combined)
        self.assertNotIn("All processing remains local", combined)
        self.assertNotIn("Never access the web or external APIs", combined)

    def test_update_workflow_uses_backup_swap_command(self):
        skill = (ROOT / "skills/doc-ingest/SKILL.md").read_text()
        self.assertIn("promote", skill)
        self.assertIn("unique backup", skill)
        self.assertIn("restore the backup", skill)
        self.assertIn("delete the backup only after successful", skill)
        self.assertIn("For both new and updated evidence sets", skill)
        self.assertNotIn("For a new set, the fresh output may instead be `docs/evidence/<topic>`", skill)


if __name__ == "__main__":
    unittest.main()

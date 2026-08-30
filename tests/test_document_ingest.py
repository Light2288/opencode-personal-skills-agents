import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/document_ingest.py"
GENERATOR = ROOT / "tests/fixtures/document_workflows/generate.py"


class DocumentIngestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.sources = root / "sources"
        self.output = root / "output"
        subprocess.run([sys.executable, str(GENERATOR), "--output", str(self.sources)], check=True)

    def tearDown(self):
        self.temp.cleanup()

    def normalize(self, output=None):
        output = output or self.output
        result = subprocess.run(
            [sys.executable, str(TOOL), "normalize", str(self.sources), "--output", str(output)],
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_discovers_supported_and_legacy_formats_deterministically(self):
        first = self.normalize()
        second = self.normalize(Path(self.temp.name) / "second")
        first_registry = [(s["id"], s["path"]) for s in first["sources"]]
        second_registry = [(s["id"], s["path"]) for s in second["sources"]]
        self.assertEqual(first_registry, second_registry)
        self.assertEqual(sorted(path for _, path in first_registry), [path for _, path in first_registry])
        self.assertEqual("PARTIAL", first["status"])
        issues = {s["path"]: s["reason"] for s in first["sources"] if s["status"] != "COMPLETE"}
        for name in ("old.doc", "old.xls", "old.ppt"):
            self.assertEqual("unsupported legacy Office format", issues[name])
        self.assertIn("unreadable", issues["unreadable.docx"])

    def test_normalizes_office_structures_and_visuals(self):
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        docx = (self.output / by_path["brief.docx"]["normalized"]).read_text()
        self.assertIn("Component", docx)
        self.assertTrue(by_path["brief.docx"]["assets"])
        xlsx = (self.output / by_path["capacity.xlsx"]["normalized"]).read_text()
        self.assertIn("Sheet: Capacity", xlsx)
        self.assertIn("Sheet: Costs", xlsx)
        self.assertIn("B2", xlsx)
        self.assertIn("Formula: A2*2", xlsx)
        self.assertIn("Capacity table CapacityTable range A1:B2", xlsx)
        self.assertIn("Capacity chart", xlsx)
        pptx = (self.output / by_path["roadmap.pptx"]["normalized"]).read_text()
        self.assertIn("Slide 1", pptx)
        self.assertIn("Synthetic speaker note", pptx)
        self.assertTrue(by_path["roadmap.pptx"]["assets"])
        self.assertEqual("direct PDF input", by_path["visual.pdf"]["method"])
        self.assertEqual("direct image input", by_path["diagram.png"]["method"])

    def test_never_modifies_sources_and_confines_outputs(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.sources.iterdir() if p.is_file()}
        report = self.normalize()
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.sources.iterdir() if p.is_file()}
        self.assertEqual(before, after)
        output_root = self.output.resolve()
        for source in report["sources"]:
            for relative in ([source.get("normalized")] if source.get("normalized") else []) + source.get("assets", []):
                resolved = (output_root / relative).resolve()
                self.assertEqual(str(output_root), os.path.commonpath([str(output_root), str(resolved)]))

    def test_rejects_output_inside_source(self):
        result = subprocess.run(
            [sys.executable, str(TOOL), "normalize", str(self.sources), "--output", str(self.sources / "output")],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("outside the source directory", result.stderr)

    def test_rejects_suspiciously_compressed_members(self):
        bomb = self.sources / "compressed.docx"
        with ZipFile(str(bomb), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/compressed.bin", b"A" * (65 * 1024 * 1024))
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "compressed.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("suspicious compression ratio", item["reason"])

    def test_inline_strings_and_relationship_order_are_preserved(self):
        workbook = self.sources / "relationships.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="First" r:id="rSecond"/><sheet name="Second" r:id="rFirst"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="rFirst" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rSecond" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><c r="A1" t="inlineStr"><is><t>SECOND</t></is></c></worksheet>')
            archive.writestr("xl/worksheets/sheet2.xml", '<worksheet><c r="A1" t="inlineStr"><is><t>FIRST</t></is></c></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "relationships.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertLess(content.index("Sheet: First"), content.index("Sheet: Second"))
        self.assertIn("First range A1 = FIRST", content)
        self.assertIn("Second range A1 = SECOND", content)

    def test_missing_sheet_relationship_is_partial_without_positional_fallback(self):
        workbook = self.sources / "missing-sheet-rel.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Missing" r:id="absent"/></sheets></workbook>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><c r="A1"><v>wrongly-associated</v></c></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "missing-sheet-rel.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertNotIn("wrongly-associated", content)
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("relationship" in warning for warning in item["warnings"]))

    def test_missing_renderer_is_disclosed_as_partial_for_office_sources(self):
        module = self.load_tool("document_ingest_missing_renderer_deterministic")
        with mock.patch.object(module.shutil, "which", return_value=None):
            report = module.normalize(self.sources, self.output)
        office = [source for source in report["sources"] if source["format"] in {"docx", "xlsx", "pptx"} and source["path"] != "unreadable.docx"]
        for source in office:
            self.assertIn("layout rendering not performed", source["warnings"])
            self.assertEqual("PARTIAL", source["coverage"])

    def test_external_office_relationship_skips_render_and_continues(self):
        document = self.sources / "external.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", '<document><p>Structured remains</p></document>')
            archive.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship Id="external" Type="hyperlink" Target="https://sensitive.example/path" TargetMode="External"/></Relationships>')
        module = self.load_tool("document_ingest_external_render")
        with mock.patch.object(module.shutil, "which", return_value="/fake/libreoffice"), mock.patch.object(module.subprocess, "run") as run:
            report = module.normalize(self.sources, self.output)
        rendered_sources = [str(call.args[0][-1]) for call in run.call_args_list]
        self.assertFalse(any(path.endswith("external.docx") for path in rendered_sources))
        item = next(source for source in report["sources"] if source["path"] == "external.docx")
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("external relationships prevented safe rendering" in warning for warning in item["warnings"]))
        self.assertNotIn("sensitive.example", " ".join(item["warnings"]))
        self.assertIn("Structured remains", (self.output / item["normalized"]).read_text())
        self.assertTrue(any(source["status"] == "COMPLETE" for source in report["sources"] if source["path"] != "external.docx"))

    def test_declared_broken_pptx_slide_does_not_ingest_orphan(self):
        presentation = self.sources / "orphan-slide.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="missing"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="missing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/missing.xml"/></Relationships>')
            archive.writestr("ppt/slides/slide99.xml", '<slide><text>ORPHAN MUST NOT APPEAR</text></slide>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "orphan-slide.pptx")
        self.assertNotIn("ORPHAN MUST NOT APPEAR", (self.output / item["normalized"]).read_text())
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("missing slide" in warning for warning in item["warnings"]))

    def test_pptx_declared_ordinals_and_orphan_reachability(self):
        presentation = self.sources / "ordinal-orphan.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="missing"/><sldId r:id="slide2"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="missing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/missing.xml"/><Relationship Id="slide2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide2.xml"/></Relationships>')
            archive.writestr("ppt/slides/slide2.xml", '<slide xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><text>DECLARED TWO</text><pic r:embed="declaredImage"/></slide>')
            archive.writestr("ppt/slides/_rels/slide2.xml.rels", '<Relationships><Relationship Id="declaredImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/declared.png"/><Relationship Id="notes" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide2.xml"/></Relationships>')
            archive.writestr("ppt/notesSlides/notesSlide2.xml", '<notes><text>NOTES TWO</text></notes>')
            archive.writestr("ppt/media/declared.png", b"declared")
            archive.writestr("ppt/slides/slide99.xml", '<slide xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><text>ORPHAN TEXT</text><pic r:embed="orphanImage"/><graphicFrame r:id="orphanChart"/></slide>')
            archive.writestr("ppt/slides/_rels/slide99.xml.rels", '<Relationships><Relationship Id="orphanImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/orphan.png"/><Relationship Id="orphanChart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/orphan.xml"/></Relationships>')
            archive.writestr("ppt/media/orphan.png", b"orphan")
            archive.writestr("ppt/charts/orphan.xml", '<chart><title>ORPHAN CHART</title></chart>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "ordinal-orphan.pptx")
        content = (self.output / item["normalized"]).read_text()
        self.assertIn("Slide 2", content)
        self.assertIn("Slide 2 speaker notes: NOTES TWO", content)
        self.assertNotIn("Slide 1\n\nDECLARED TWO", content)
        self.assertTrue(any(visual["owner"] == "PPTX slide 2" and visual["target"].endswith("declared.png") for visual in item["visuals"]))
        self.assertTrue(any("slide 1" in warning.lower() for warning in item["warnings"]))
        self.assertNotIn("ORPHAN TEXT", content)
        self.assertNotIn("ORPHAN CHART", content)
        self.assertFalse(any(asset.endswith("orphan.png") for asset in item["assets"]))
        self.assertFalse(any("orphan" in visual["target"] for visual in item["visuals"]))

    def test_xlsx_absolute_anchor_ownership_and_unresolved_warning(self):
        workbook = self.sources / "absolute-anchor.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Canvas" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><absoluteAnchor><pos x="100" y="200"/><ext cx="300" cy="400"/><pic r:embed="image"/><graphicFrame r:id="chart"/></absoluteAnchor><absoluteAnchor><pos x="1" y="2"/><ext cx="3" cy="4"/><pic r:embed="missing"/></absoluteAnchor></drawing>')
            archive.writestr("xl/drawings/_rels/drawing1.xml.rels", '<Relationships><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image.png"/><Relationship Id="chart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart.xml"/></Relationships>')
            archive.writestr("xl/media/image.png", b"image")
            archive.writestr("xl/charts/chart.xml", '<chart><title>Absolute Chart</title></chart>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "absolute-anchor.xlsx")
        owners = [visual["owner"] for visual in item["visuals"] if visual["target"].endswith(("image.png", "chart.xml"))]
        self.assertEqual(2, len(owners))
        self.assertTrue(all("XLSX sheet Canvas" in owner and "absolute position x=100 y=200 extent cx=300 cy=400" in owner for owner in owners))
        self.assertFalse(any(":" in owner.split("absolute position", 1)[0] for owner in owners))
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("unresolved absoluteAnchor relationship" in warning for warning in item["warnings"]))

    def test_xlsx_drawing_target_and_absolute_anchor_validation(self):
        workbook = self.sources / "absolute-validation.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Canvas" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing r:id="missingDrawing"/><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="missingDrawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/missing.xml"/><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><absoluteAnchor><pos x="bad" y="-1"/><ext cx="-2" cy="4"/><pic r:embed="image"/><a r:id="link"/></absoluteAnchor></drawing>')
            archive.writestr("xl/drawings/_rels/drawing1.xml.rels", '<Relationships><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image.png"/><Relationship Id="link" Type="hyperlink" Target="https://example.com" TargetMode="External"/></Relationships>')
            archive.writestr("xl/media/image.png", b"image")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "absolute-validation.xlsx")
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("unresolved drawing relationship target" in warning for warning in item["warnings"]))
        self.assertTrue(any("uninterpretable absoluteAnchor" in warning for warning in item["warnings"]))
        self.assertFalse(any("example.com" in visual["target"] for visual in item["visuals"]))

    def test_absolute_anchor_chart_text_uses_location_and_visual_order_is_stable(self):
        workbook = self.sources / "absolute-order.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Canvas" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><absoluteAnchor><pos x="1" y="2"/><ext cx="3" cy="4"/><pic r:embed="zImage"/><graphicFrame r:id="aChart"/></absoluteAnchor></drawing>')
            archive.writestr("xl/drawings/_rels/drawing1.xml.rels", '<Relationships><Relationship Id="zImage" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image.png"/><Relationship Id="aChart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart.xml"/></Relationships>')
            archive.writestr("xl/media/image.png", b"image")
            archive.writestr("xl/charts/chart.xml", '<chart><title>Located</title></chart>')
        first = self.normalize()
        first_item = next(source for source in first["sources"] if source["path"] == "absolute-order.xlsx")
        content = (self.output / first_item["normalized"]).read_text()
        self.assertIn("absolute position x=1 y=2 extent cx=3 cy=4", content)
        second = self.normalize(Path(self.temp.name) / "second-order")
        second_item = next(source for source in second["sources"] if source["path"] == "absolute-order.xlsx")
        self.assertEqual(first_item["visuals"], second_item["visuals"])

    def test_xlsx_one_cell_anchor_records_start_and_extent(self):
        workbook = self.sources / "one-cell-anchor.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Canvas" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><oneCellAnchor><from><col>1</col><row>2</row></from><ext cx="300" cy="400"/><pic r:embed="image"/></oneCellAnchor></drawing>')
            archive.writestr("xl/drawings/_rels/drawing1.xml.rels", '<Relationships><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image.png"/></Relationships>')
            archive.writestr("xl/media/image.png", b"image")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "one-cell-anchor.xlsx")
        owner = next(visual["owner"] for visual in item["visuals"] if visual["target"].endswith("image.png"))
        self.assertIn("start B3 extent cx=300 cy=400", owner)

    def test_excel_1900_date_boundary_is_honest(self):
        workbook = self.sources / "date-boundary.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><workbookPr date1904="0"/><sheets><sheet name="Dates" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/styles.xml", '<styleSheet><cellXfs><xf numFmtId="14"/></cellXfs></styleSheet>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><c r="A1" s="0"><v>1</v></c><c r="A2" s="0"><v>59</v></c><c r="A3" s="0"><v>60</v></c><c r="A4" s="0"><v>61</v></c></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "date-boundary.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertIn("A1 = 1900-01-01", content)
        self.assertIn("A2 = 1900-02-28", content)
        self.assertIn("A3 = AMBIGUOUS EXCEL DATE 60", content)
        self.assertIn("A4 = 1900-03-01", content)
        self.assertEqual("PARTIAL", item["coverage"])

    def test_external_pptx_slide_warning_does_not_disclose_target(self):
        presentation = self.sources / "external-slide.pptx"
        secret = "https://sensitive.example/client/path"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="external"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="external" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="{}" TargetMode="External"/></Relationships>'.format(secret))
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "external-slide.pptx")
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertNotIn(secret, " ".join(item["warnings"]))
        self.assertTrue(any("external slide relationship" in warning for warning in item["warnings"]))

    def test_direct_binary_size_checked_before_read_or_output_creation(self):
        module = self.load_tool("document_ingest_direct_order")
        source = self.sources / "too-large.pdf"
        source.write_bytes(b"%PDF-1.4\n%%EOF")
        with mock.patch.object(module, "MAX_DIRECT_BINARY_BYTES", 1), mock.patch.object(module.Path, "open", side_effect=AssertionError("payload read")):
            with self.assertRaisesRegex(ValueError, "size limit"):
                module.normalize_one(source, self.output, "S1")
        self.assertFalse(self.output.exists())

    def test_oversized_direct_inputs_fail_only_the_source(self):
        module = self.load_tool("document_ingest_direct_limits")
        (self.sources / "small.txt").write_text("ok")
        (self.sources / "large.txt").write_bytes(b"x" * 11)
        (self.sources / "large.pdf").write_bytes(b"%PDF-1.4\n" + b"x" * 20 + b"%%EOF")
        (self.sources / "large.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"x" * 20 + b"IEND\xaeB`\x82")
        with mock.patch.object(module, "MAX_TEXT_BYTES", 10), mock.patch.object(module, "MAX_DIRECT_BINARY_BYTES", 10):
            report = module.normalize(self.sources, self.output)
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("large.txt", "large.pdf", "large.png"):
            self.assertEqual("FAILED", by_path[name]["status"])
            self.assertIn("size limit", by_path[name]["reason"])
        self.assertEqual("PARTIAL", report["status"])
        self.assertEqual("COMPLETE", by_path["small.txt"]["status"])

    def test_encrypted_member_fails_only_its_source(self):
        encrypted = self.sources / "encrypted.docx"
        with ZipFile(str(encrypted), "w") as archive:
            archive.writestr("word/document.xml", "<document/>")
        data = bytearray(encrypted.read_bytes())
        data[6:8] = (1).to_bytes(2, "little")
        central = data.find(b"PK\x01\x02")
        data[central + 8:central + 10] = (1).to_bytes(2, "little")
        encrypted.write_bytes(data)
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "encrypted.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("encrypted", item["reason"])
        self.assertTrue(any(source["status"] == "COMPLETE" for source in report["sources"]))

    def test_docx_table_text_is_not_duplicated_as_paragraph(self):
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "brief.docx")
        content = (self.output / item["normalized"]).read_text()
        self.assertEqual(1, content.count("Component"))

    def test_symlink_is_reported_as_partial_input_issue(self):
        link = self.sources / "linked.txt"
        try:
            link.symlink_to(self.sources / "notes.txt")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "linked.txt")
        self.assertEqual("SKIPPED", item["status"])
        self.assertIn("symbolic link", item["reason"])
        self.assertEqual("PARTIAL", report["status"])

    def test_same_media_basename_preserves_both_assets(self):
        document = self.sources / "duplicate-media.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document><p>media</p></document>")
            archive.writestr("word/media/group-a/image.png", b"first")
            archive.writestr("word/media/group-b/image.png", b"second")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "duplicate-media.docx")
        self.assertEqual(2, len(item["assets"]))
        self.assertNotEqual(item["assets"][0], item["assets"][1])
        self.assertEqual({b"first", b"second"}, {(self.output / path).read_bytes() for path in item["assets"]})

    def test_destination_oserror_is_actionable_without_traceback(self):
        blocked = Path(self.temp.name) / "blocked"
        blocked.write_text("not a directory")
        result = subprocess.run(
            [sys.executable, str(TOOL), "normalize", str(self.sources), "--output", str(blocked / "output")],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertIn("filesystem error", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_contextual_runtime_error_is_actionable_without_traceback(self):
        module = self.load_tool("document_ingest_cli_runtime")
        with mock.patch.object(module, "normalize", side_effect=RuntimeError("operation failed; recovery failed")), mock.patch.object(sys, "argv", ["document_ingest.py", "normalize", str(self.sources), "--output", str(self.output)]), self.assertRaises(SystemExit):
            with mock.patch("sys.stderr", new_callable=io.StringIO) as stderr:
                module.main()
        self.assertIn("operation failed; recovery failed", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_fixture_generator_refuses_nonempty_output(self):
        occupied = Path(self.temp.name) / "occupied"
        occupied.mkdir()
        marker = occupied / "notes.txt"
        marker.write_text("keep")
        result = subprocess.run(
            [sys.executable, str(GENERATOR), "--output", str(occupied)],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(0, result.returncode)
        self.assertEqual("keep", marker.read_text())
        self.assertIn("absent or empty", result.stderr)

    def test_fixture_generator_rejects_file_output_without_traceback(self):
        occupied = Path(self.temp.name) / "occupied-file"
        occupied.write_text("keep")
        result = subprocess.run([sys.executable, str(GENERATOR), "--output", str(occupied)], capture_output=True, text=True)
        self.assertNotEqual(0, result.returncode)
        self.assertIn("must be a directory", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_duplicate_archive_members_fail_the_source(self):
        document = self.sources / "duplicate-member.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/image.png", b"first")
            archive.writestr("word/media/image.png", b"second")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "duplicate-member.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("duplicate archive member", item["reason"])

    def test_absolute_media_remainder_cannot_escape_output(self):
        escaped = Path(self.temp.name) / "outside-output/escape.png"
        document = self.sources / "absolute-media.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/{}".format(escaped.as_posix()), b"escape")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "absolute-media.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("unsafe media member", item["reason"])
        self.assertFalse(escaped.exists())

    def test_internal_relationship_targets_cannot_escape_package(self):
        document = self.sources / "relationship-traversal.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", '<document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><body><p><drawing r:embed="image"/></p></body></document>')
            archive.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../../evil.png"/></Relationships>')
            archive.writestr("../evil.png", b"evil")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "relationship-traversal.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("unsafe internal relationship target", item["reason"])

    def test_false_positive_relationship_types_never_authorize_evidence(self):
        document = self.sources / "false-types.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", '<document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><body><p><drawing r:embed="bad"/></p></body></document>')
            archive.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship Id="bad" Type="https://example.invalid/image" Target="media/bad.png"/></Relationships>')
            archive.writestr("word/media/bad.png", b"bad")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "false-types.docx")
        self.assertFalse(any(visual["owner"].startswith("DOCX paragraph") for visual in item["visuals"]))

    def test_false_positive_xlsx_and_pptx_relationship_types_are_not_evidence(self):
        workbook = self.sources / "false-types.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Fake" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="fake-worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><c r="A1"><v>FAKE WORKSHEET</v></c></worksheet>')
        presentation = self.sources / "false-types.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="slide"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="slide" Type="fake-slide" Target="slides/slide1.xml"/></Relationships>')
            archive.writestr("ppt/slides/slide1.xml", '<slide><text>FAKE SLIDE</text></slide>')
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        self.assertNotIn("FAKE WORKSHEET", (self.output / by_path["false-types.xlsx"]["normalized"]).read_text())
        self.assertNotIn("FAKE SLIDE", (self.output / by_path["false-types.pptx"]["normalized"]).read_text())
        self.assertEqual("PARTIAL", by_path["false-types.xlsx"]["coverage"])
        self.assertEqual("PARTIAL", by_path["false-types.pptx"]["coverage"])

    def test_relationship_kind_cannot_authorize_wrong_package_location(self):
        workbook = self.sources / "wrong-location.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Bad" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="../evil.xml"/></Relationships>')
            archive.writestr("evil.xml", '<worksheet><c r="A1"><v>EVIL</v></c></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "wrong-location.xlsx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("invalid package location", item["reason"])

    def test_traversal_relationships_cannot_authorize_xlsx_or_pptx_parts(self):
        workbook = self.sources / "traversal.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Bad" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="../../evil-sheet.xml"/></Relationships>')
            archive.writestr("../evil-sheet.xml", '<worksheet><c r="A1"><v>EVIL SHEET</v></c></worksheet>')
        presentation = self.sources / "traversal.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="slide"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="slide" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="../../evil-slide.xml"/></Relationships>')
            archive.writestr("../evil-slide.xml", '<slide><text>EVIL SLIDE</text></slide>')
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        self.assertEqual("FAILED", by_path["traversal.xlsx"]["status"])
        self.assertEqual("FAILED", by_path["traversal.pptx"]["status"])
        self.assertIn("unsafe internal relationship target", by_path["traversal.xlsx"]["reason"])
        self.assertIn("unsafe internal relationship target", by_path["traversal.pptx"]["reason"])

    def test_svg_url_references_are_checked_in_every_attribute(self):
        for attribute in ("fill", "stroke", "filter", "mask", "clip-path"):
            (self.sources / (attribute.replace("-", "") + ".svg")).write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect {}="url(file.svg#x)"/></svg>'.format(attribute))
        (self.sources / "valid-local.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g"/></defs><rect fill="url(#g)"/></svg>')
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for attribute in ("fill", "stroke", "filter", "mask", "clippath"):
            self.assertEqual("FAILED", by_path[attribute + ".svg"]["status"])
        self.assertEqual("COMPLETE", by_path["valid-local.svg"]["status"])

    def test_svg_css_escapes_are_rejected(self):
        (self.sources / "escaped-url.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect style="fill:u\\72l(https://example.invalid/x)"/></svg>')
        (self.sources / "escaped-import.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><style>\\40 import url(https://example.invalid/x)</style></svg>')
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("escaped-url.svg", "escaped-import.svg"):
            self.assertEqual("FAILED", by_path[name]["status"])
            self.assertIn("CSS escape", by_path[name]["reason"])

    def test_traversal_media_member_fails_before_assets_are_written(self):
        document = self.sources / "traversal-media.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/good.png", b"good")
            archive.writestr("word/media/../escape.png", b"escape")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "traversal-media.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("unsafe media member", item["reason"])
        self.assertFalse(any((self.output / "intermediates" / item["id"]).glob("**/*")))

    def test_media_alias_collision_fails_before_assets_are_written(self):
        document = self.sources / "alias-media.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/image.png", b"first")
            archive.writestr("word/media/./image.png", b"second")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "alias-media.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("duplicate media target", item["reason"])
        self.assertFalse(any((self.output / "intermediates" / item["id"]).glob("**/*")))

    def test_media_file_directory_collision_fails_only_the_source(self):
        document = self.sources / "prefix-media.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/item", b"file")
            archive.writestr("word/media/item/image.png", b"nested")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "prefix-media.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("media target hierarchy collision", item["reason"])
        self.assertFalse(any((self.output / "intermediates" / item["id"]).glob("**/*")))
        self.assertTrue(any(source["status"] == "COMPLETE" for source in report["sources"]))

    def test_media_target_must_be_below_asset_root(self):
        document = self.sources / "root-media.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/.", b"file")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "root-media.docx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("unsafe media member", item["reason"])
        self.assertFalse((self.output / "intermediates" / item["id"]).exists())

    def test_media_reads_complete_before_any_asset_write(self):
        spec = importlib.util.spec_from_file_location("document_ingest_atomic", str(TOOL))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        class FailingArchive:
            def namelist(self):
                return ["word/media/first.png", "word/media/second.png"]

            def open(self, name):
                if name.endswith("second.png"):
                    raise BadZipFile("CRC failure")
                return io.BytesIO(b"first")

        with self.assertRaises(BadZipFile):
            module.extract_media(FailingArchive(), "word/media/", self.output, "S1")
        self.assertFalse((self.output / "intermediates/S1").exists())

    def test_media_extraction_streams_without_archive_read(self):
        module = self.load_tool("document_ingest_stream_media")

        class StreamingArchive:
            def namelist(self):
                return ["word/media/image.bin"]

            def read(self, name):
                raise AssertionError("media must not be buffered with archive.read")

            def open(self, name):
                return io.BytesIO(b"payload")

        assets, members = module.extract_media(StreamingArchive(), "word/media/", self.output, "S1")
        self.assertEqual(["word/media/image.bin"], members)
        self.assertEqual(b"payload", (self.output / assets[0]).read_bytes())

    def test_fatal_output_error_cleans_fresh_normalization_output(self):
        spec = importlib.util.spec_from_file_location("document_ingest_cleanup", str(TOOL))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_write = module.write_markdown

        def fail_after_media(output, source_id, heading, lines):
            if (output / "intermediates" / source_id).exists():
                raise OSError(28, "disk full", str(output / "sources" / source_id / "content.md"))
            return original_write(output, source_id, heading, lines)

        module.write_markdown = fail_after_media
        with self.assertRaises(OSError):
            module.normalize(self.sources, self.output)
        self.assertFalse(self.output.exists())

    def test_cleanup_failure_reports_original_and_cleanup_errors(self):
        spec = importlib.util.spec_from_file_location("document_ingest_cleanup_failure", str(TOOL))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def fail_output(path, output, source_id):
            raise OSError(28, "disk full", str(output / "content.md"))

        original_cleanup = module.shutil.rmtree

        def fail_cleanup(path, **kwargs):
            raise OSError(13, "permission denied", str(path))

        module.normalize_one = fail_output
        module.shutil.rmtree = fail_cleanup
        try:
            with self.assertRaisesRegex(RuntimeError, "normalization failed.*cleanup failed"):
                module.normalize(self.sources, self.output)
        finally:
            module.shutil.rmtree = original_cleanup

    def test_unexpected_runtime_error_is_not_reported_as_unreadable_source(self):
        spec = importlib.util.spec_from_file_location("document_ingest_runtime", str(TOOL))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        def fail_unexpectedly(path, output, source_id):
            raise RuntimeError("implementation failure")

        module.normalize_one = fail_unexpectedly
        with self.assertRaisesRegex(RuntimeError, "implementation failure"):
            module.normalize(self.sources, self.output)
        self.assertFalse(self.output.exists())

    def test_source_oserror_is_partial_but_output_oserror_propagates(self):
        spec = importlib.util.spec_from_file_location("document_ingest", str(TOOL))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.normalize_one

        def fail_source(path, output, source_id):
            if path.name == "notes.txt":
                raise OSError(5, "source failed", str(path))
            return original(path, output, source_id)

        module.normalize_one = fail_source
        report = module.normalize(self.sources, self.output)
        item = next(source for source in report["sources"] if source["path"] == "notes.txt")
        self.assertEqual("FAILED", item["status"])

        second_output = Path(self.temp.name) / "output-two"
        def fail_output(path, output, source_id):
            raise OSError(28, "disk full", str(output / "content.md"))
        module.normalize_one = fail_output
        with self.assertRaises(OSError):
            module.normalize(self.sources, second_output)

    def load_tool(self, name="document_ingest_extra"):
        spec = importlib.util.spec_from_file_location(name, str(TOOL))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def empty_report(self, output):
        return json.dumps({"status": "COMPLETE", "source_root": "/source", "output_root": str(output), "sources": []})

    def test_renderer_missing_is_partial_and_actionable(self):
        module = self.load_tool("document_ingest_render_missing")
        with mock.patch.object(module.shutil, "which", return_value=None):
            result = module.render_with_libreoffice(self.sources / "brief.docx", self.output / "intermediates/S1")
        self.assertFalse(result["rendered"])
        self.assertIn("not found", result["warning"])

    def test_renderer_setup_failure_is_partial_not_fatal(self):
        module = self.load_tool("document_ingest_render_setup")
        with mock.patch.object(module.shutil, "which", return_value="/fake/libreoffice"), mock.patch.object(module.tempfile, "mkdtemp", side_effect=OSError("profile unavailable")):
            result = module.render_with_libreoffice(self.sources / "brief.docx", self.output / "intermediates/S1")
        self.assertFalse(result["rendered"])
        self.assertIn("setup error", result["warning"])

    def test_renderer_failure_does_not_expose_stderr(self):
        module = self.load_tool("document_ingest_render_stderr")
        secret = "https://sensitive.example/client /private/client/path"
        failure = subprocess.CalledProcessError(7, ["libreoffice"], stderr=secret)
        with mock.patch.object(module.shutil, "which", return_value="/fake/libreoffice"), mock.patch.object(module.subprocess, "run", side_effect=failure):
            result = module.render_with_libreoffice(self.sources / "brief.docx", self.output / "intermediates/S1")
        self.assertFalse(result["rendered"])
        self.assertIn("exit code 7", result["warning"])
        self.assertNotIn(secret, result["warning"])

    def test_renderer_available_uses_headless_isolated_profile(self):
        module = self.load_tool("document_ingest_render_available")
        destination = self.output / "intermediates/S1"

        def fake_run(arguments, **kwargs):
            outdir = Path(arguments[arguments.index("--outdir") + 1])
            (outdir / "brief.pdf").write_bytes(b"%PDF rendered")
            return subprocess.CompletedProcess(arguments, 0, "", "")

        with mock.patch.object(module.shutil, "which", return_value="/fake/libreoffice"), mock.patch.object(module.subprocess, "run", side_effect=fake_run) as called:
            result = module.render_with_libreoffice(self.sources / "brief.docx", destination)
        self.assertTrue(result["rendered"])
        self.assertTrue((destination.parent / "S1-libreoffice-render/rendered.pdf").is_file())
        arguments = called.call_args[0][0]
        self.assertIn("--headless", arguments)
        self.assertTrue(any(value.startswith("-env:UserInstallation=file://") for value in arguments))
        self.assertIsNone(called.call_args[1].get("shell"))
        self.assertGreater(called.call_args[1]["timeout"], 0)

    def test_renderer_cleanup_failure_does_not_override_render_result(self):
        module = self.load_tool("document_ingest_render_cleanup")
        destination = self.output / "intermediates/S1"

        def fake_run(arguments, **kwargs):
            outdir = Path(arguments[arguments.index("--outdir") + 1])
            (outdir / "brief.pdf").write_bytes(b"%PDF rendered")
            return subprocess.CompletedProcess(arguments, 0, "", "")

        with mock.patch.object(module.shutil, "which", return_value="/fake/libreoffice"), mock.patch.object(module.subprocess, "run", side_effect=fake_run), mock.patch.object(module.shutil, "rmtree", side_effect=OSError("cleanup failed")):
            result = module.render_with_libreoffice(self.sources / "brief.docx", destination)
        self.assertTrue(result["rendered"])
        self.assertIn("profile cleanup failed", result["warning"])

    def test_successful_render_cleanup_warning_is_recorded(self):
        module = self.load_tool("document_ingest_render_cleanup_report")
        with mock.patch.object(module, "render_with_libreoffice", return_value={"rendered": True, "asset": "intermediates/S1/render/rendered.pdf", "warning": "profile cleanup failed"}):
            report = module.normalize(self.sources, self.output)
        item = next(source for source in report["sources"] if source["path"] == "brief.docx")
        self.assertIn("profile cleanup failed", item["warnings"])
        self.assertEqual("PARTIAL", item["coverage"])

    def test_render_output_does_not_collide_with_embedded_media(self):
        document = self.sources / "render-collision.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/rendered.pdf", b"embedded")
        module = self.load_tool("document_ingest_render_collision")

        def fake_run(arguments, **kwargs):
            outdir = Path(arguments[arguments.index("--outdir") + 1])
            (outdir / "render-collision.pdf").write_bytes(b"render")
            return subprocess.CompletedProcess(arguments, 0, "", "")

        with mock.patch.object(module.shutil, "which", return_value="/fake/libreoffice"), mock.patch.object(module.subprocess, "run", side_effect=fake_run):
            report = module.normalize(self.sources, self.output)
        item = next(source for source in report["sources"] if source["path"] == "render-collision.docx")
        self.assertIn("intermediates/{}/rendered.pdf".format(item["id"]), item["assets"])
        self.assertIn("intermediates/{}-libreoffice-render/rendered.pdf".format(item["id"]), item["assets"])
        self.assertEqual(b"embedded", (self.output / "intermediates" / item["id"] / "rendered.pdf").read_bytes())

    def test_render_namespace_cannot_collide_with_package_media(self):
        document = self.sources / "render-namespace.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", "<document/>")
            archive.writestr("word/media/render/rendered.pdf", b"embedded")
        module = self.load_tool("document_ingest_render_namespace")
        def fake_run(arguments, **kwargs):
            outdir = Path(arguments[arguments.index("--outdir") + 1])
            (outdir / "render-namespace.pdf").write_bytes(b"render")
            return subprocess.CompletedProcess(arguments, 0, "", "")
        with mock.patch.object(module.shutil, "which", return_value="/fake/libreoffice"), mock.patch.object(module.subprocess, "run", side_effect=fake_run):
            report = module.normalize(self.sources, self.output)
        item = next(source for source in report["sources"] if source["path"] == "render-namespace.docx")
        package_asset = self.output / "intermediates" / item["id"] / "render/rendered.pdf"
        render_asset = self.output / next(asset for asset in item["assets"] if "libreoffice-render" in asset)
        self.assertEqual(b"embedded", package_asset.read_bytes())
        self.assertEqual(b"render", render_asset.read_bytes())

    def test_svg_active_content_and_external_references_fail(self):
        (self.sources / "script.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
        (self.sources / "event.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>')
        (self.sources / "external.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="https://example.com/x.png"/></svg>')
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("script.svg", "event.svg", "external.svg"):
            self.assertEqual("FAILED", by_path[name]["status"])

    def test_broken_office_relationships_warn_and_remain_partial(self):
        presentation = self.sources / "broken-rel.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="missing"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="missing" Target="slides/missing.xml"/></Relationships>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "broken-rel.pptx")
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("missing slide" in warning for warning in item["warnings"]))

    def test_missing_docx_and_pptx_visual_relationships_are_partial(self):
        document = self.sources / "broken-visual.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", '<document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><body><p><drawing r:embed="missing"/></p></body></document>')
            archive.writestr("word/_rels/document.xml.rels", '<Relationships/>')
        presentation = self.sources / "broken-visual.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="slide"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="slide" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>')
            archive.writestr("ppt/slides/slide1.xml", '<slide xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><pic r:embed="missing"/></slide>')
            archive.writestr("ppt/slides/_rels/slide1.xml.rels", '<Relationships/>')
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("broken-visual.docx", "broken-visual.pptx"):
            self.assertEqual("PARTIAL", by_path[name]["coverage"])
            self.assertTrue(any("unresolved visual relationship" in warning for warning in by_path[name]["warnings"]))

    def test_duplicate_or_missing_relationship_ids_fail_source(self):
        for filename, relationships_xml in (
            ("duplicate-rel.docx", '<Relationships><Relationship Id="dup" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/a.png"/><Relationship Id="dup" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/b.png"/></Relationships>'),
            ("missing-rel.docx", '<Relationships><Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/a.png"/></Relationships>'),
        ):
            with ZipFile(str(self.sources / filename), "w", ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", "<document/>")
                archive.writestr("word/_rels/document.xml.rels", relationships_xml)
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("duplicate-rel.docx", "missing-rel.docx"):
            self.assertEqual("FAILED", by_path[name]["status"])
            self.assertIn("relationship ID", by_path[name]["reason"])

    def test_docx_external_hyperlink_is_not_missing_visual(self):
        document = self.sources / "hyperlink.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", '<document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><body><p><drawing><a r:id="link"/></drawing></p></body></document>')
            archive.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship Id="link" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="https://example.com" TargetMode="External"/></Relationships>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "hyperlink.docx")
        self.assertFalse(any("visual relationship" in warning for warning in item["warnings"]))

    def test_svg_css_and_data_references_fail(self):
        (self.sources / "css-import.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><style>@import url(https://example.com/x.css)</style></svg>')
        (self.sources / "css-attribute.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect style="fill:url(https://example.com/x.svg)"/></svg>')
        (self.sources / "data-reference.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"><image href="data:text/html,unsafe"/></svg>')
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("css-import.svg", "css-attribute.svg", "data-reference.svg"):
            self.assertEqual("FAILED", by_path[name]["status"])

    def test_xlsx_tables_and_charts_include_owning_sheet(self):
        workbook = self.sources / "owned-table-chart.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Sales" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><tableParts><tablePart r:id="table"/></tableParts><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="table" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table" Target="../tables/table1.xml"/><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/tables/table1.xml", '<table name="SalesTable" ref="A1:B2"/>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><twoCellAnchor><from><col>0</col><row>0</row></from><to><col>1</col><row>1</row></to><graphicFrame r:id="chart"/></twoCellAnchor></drawing>')
            archive.writestr("xl/drawings/_rels/drawing1.xml.rels", '<Relationships><Relationship Id="chart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart1.xml"/></Relationships>')
            archive.writestr("xl/charts/chart1.xml", '<chart><title>Revenue</title></chart>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "owned-table-chart.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertIn("Sales table SalesTable range A1:B2", content)
        self.assertIn("Sales chart", content)

    def test_unowned_xlsx_table_and_chart_are_not_evidence(self):
        workbook = self.sources / "orphan-parts.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Clean" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet/>')
            archive.writestr("xl/tables/orphan.xml", '<table name="ORPHAN_TABLE" ref="A1:B2"/>')
            archive.writestr("xl/charts/orphan.xml", '<chart><title>ORPHAN_CHART</title></chart>')
            archive.writestr("xl/media/orphan.png", b"orphan")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "orphan-parts.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertNotIn("ORPHAN_TABLE", content)
        self.assertNotIn("ORPHAN_CHART", content)
        self.assertFalse(any(visual["target"].endswith("orphan.xml") for visual in item["visuals"]))
        self.assertFalse(any(asset.endswith("orphan.png") for asset in item["assets"]))
        self.assertFalse(any(visual["target"].endswith("orphan.png") for visual in item["visuals"]))
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("unreferenced package table" in warning for warning in item["warnings"]))
        self.assertTrue(any("unreferenced package chart" in warning for warning in item["warnings"]))

    def test_pptx_requires_internal_typed_note_and_visual_relationships(self):
        presentation = self.sources / "typed-relations.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="slide"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="slide" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>')
            archive.writestr("ppt/slides/slide1.xml", '<slide xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><pic r:embed="badImage"/></slide>')
            archive.writestr("ppt/slides/_rels/slide1.xml.rels", '<Relationships><Relationship Id="badImage" Type="hyperlink" Target="../media/bad.png"/><Relationship Id="badNotes" Type="hyperlink" Target="../notesSlides/notesSlide1.xml"/></Relationships>')
            archive.writestr("ppt/media/bad.png", b"bad")
            archive.writestr("ppt/notesSlides/notesSlide1.xml", '<notes><text>BAD NOTES</text></notes>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "typed-relations.pptx")
        content = (self.output / item["normalized"]).read_text()
        self.assertNotIn("BAD NOTES", content)
        self.assertFalse(any(visual["target"].endswith("bad.png") for visual in item["visuals"]))

    def test_promote_metadata_failure_rolls_back_target(self):
        module = self.load_tool("document_ingest_promote_metadata_failure")
        target = Path(self.temp.name) / "evidence/topic"
        target.mkdir(parents=True)
        (target / "manifest.md").write_text("old")
        fresh = target.parent / ".topic-update"
        fresh.mkdir()
        (fresh / "manifest.md").write_text("new")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        original_write = module.Path.write_text
        def fail_promoted_report(path, *args, **kwargs):
            if path == target / "extraction-report.json.tmp":
                raise OSError("metadata write failed")
            return original_write(path, *args, **kwargs)
        with mock.patch.object(module.Path, "write_text", new=fail_promoted_report):
            with self.assertRaisesRegex(OSError, "metadata write failed"):
                module.promote_evidence(fresh, target)
        self.assertEqual("old", (target / "manifest.md").read_text())

    def test_promote_metadata_rollback_failure_preserves_context(self):
        module = self.load_tool("document_ingest_promote_metadata_rollback")
        target = Path(self.temp.name) / "evidence/topic"
        target.mkdir(parents=True)
        (target / "manifest.md").write_text("old")
        fresh = target.parent / ".topic-update"
        fresh.mkdir()
        (fresh / "manifest.md").write_text("new")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        real_write = module.Path.write_text
        real_replace = module.os.replace
        def fail_write(path, *args, **kwargs):
            if path == target / "extraction-report.json.tmp":
                raise OSError("metadata failed")
            return real_write(path, *args, **kwargs)
        def fail_target_recovery(source, destination):
            if Path(source) == target and Path(destination) == fresh:
                raise OSError("rollback failed")
            return real_replace(source, destination)
        with mock.patch.object(module.Path, "write_text", new=fail_write), mock.patch.object(module.os, "replace", side_effect=fail_target_recovery):
            with self.assertRaisesRegex(RuntimeError, "metadata failed.*rollback failed"):
                module.promote_evidence(fresh, target)

    def test_normalize_office_adds_render_or_exact_warning(self):
        module = self.load_tool("document_ingest_render_integration")
        with mock.patch.object(module, "render_with_libreoffice", return_value={"rendered": True, "asset": "intermediates/S1/rendered.pdf"}):
            report = module.normalize(self.sources, self.output)
        item = next(source for source in report["sources"] if source["path"] == "brief.docx")
        self.assertIn("intermediates/{}/rendered.pdf".format(item["id"]), item["assets"])
        self.assertNotIn("layout rendering not performed", item["warnings"])

    def test_multi_megabyte_worksheet_is_allowed_but_oversized_xml_fails(self):
        valid = self.sources / "large-valid.xlsx"
        cells = "".join('<c r="A{}"><v>{}</v></c>'.format(index, index) for index in range(1, 70000))
        with ZipFile(str(valid), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Large" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", "<worksheet>{}</worksheet>".format(cells))
        oversized = self.sources / "oversized.docx"
        with ZipFile(str(oversized), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", b"A" * (65 * 1024 * 1024))
        report = self.normalize()
        by_path = {item["path"]: item for item in report["sources"]}
        self.assertEqual("COMPLETE", by_path["large-valid.xlsx"]["status"])
        self.assertEqual("FAILED", by_path["oversized.docx"]["status"])

    def test_excessive_worksheet_cells_fail_with_actionable_limit(self):
        workbook = self.sources / "too-many-cells.xlsx"
        cells = "".join('<c r="A{}"><v>{}</v></c>'.format(index, index) for index in range(1, 100002))
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Large" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", "<worksheet>{}</worksheet>".format(cells))
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "too-many-cells.xlsx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("cell limit", item["reason"])

    def test_xlsx_types_visibility_filters_and_shared_formulas_are_explicit(self):
        workbook = self.sources / "typed.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><workbookPr date1904="0"/><sheets><sheet name="Typed" state="hidden" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/styles.xml", '<styleSheet><cellXfs><xf numFmtId="0"/><xf numFmtId="14"/></cellXfs></styleSheet>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><dimension ref="A1:F3"/><cols><col min="2" max="2" hidden="1"/></cols><sheetData><row r="1" hidden="1"><c r="A1" t="b"><v>1</v></c><c r="B1" t="e"><v>#DIV/0!</v></c><c r="C1" s="1"><v>43831</v></c><c r="D1"><f t="shared" si="0" ref="D1:D2">A1+1</f><v>2</v></c></row><row r="2"><c r="D2"><f t="shared" si="0"/><v>3</v></c></row></sheetData><autoFilter ref="A1:F3"/></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "typed.xlsx")
        content = (self.output / item["normalized"]).read_text()
        for expected in ("visibility: hidden", "dimension: A1:F3", "hidden row: 1", "hidden columns: B:B", "filter: A1:F3", "A1 = TRUE", "B1 = ERROR #DIV/0!", "C1 = 2020-01-01", "shared formula 0 anchor", "shared formula 0 follower"):
            self.assertIn(expected, content)
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertTrue(any("shared formula follower" in warning for warning in item["warnings"]))

    def test_xlsx_literal_date_tokens_do_not_convert_numbers(self):
        workbook = self.sources / "literal-format.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Literal" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/styles.xml", '<styleSheet><numFmts><numFmt numFmtId="165" formatCode="0 &quot;days dd&quot;"/></numFmts><cellXfs><xf numFmtId="165"/></cellXfs></styleSheet>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><c r="A1" s="0"><v>43831</v></c></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "literal-format.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertIn("A1 = 43831", content)
        self.assertNotIn("A1 = 2020", content)

    def test_xlsx_time_and_duration_formats_remain_explicit(self):
        workbook = self.sources / "time-formats.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Time" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/styles.xml", '<styleSheet><cellXfs><xf numFmtId="20"/><xf numFmtId="46"/></cellXfs></styleSheet>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><c r="A1" s="0"><v>0.5</v></c><c r="B1" s="1"><v>1.5</v></c></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "time-formats.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertIn("A1 = TIME 0.5", content)
        self.assertIn("B1 = ELAPSED 1.5", content)
        self.assertEqual("PARTIAL", item["coverage"])

    def test_xlsx_extraction_warning_remains_partial_when_render_succeeds(self):
        workbook = self.sources / "shared-warning.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Shared" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><sheetData><row r="1"><c r="A1"><f t="shared" si="0" ref="A1:A2">1+1</f><v>2</v></c></row><row r="2"><c r="A2"><f t="shared" si="0"/><v>2</v></c></row></sheetData></worksheet>')
        module = self.load_tool("document_ingest_warning_coverage")
        with mock.patch.object(module, "render_with_libreoffice", return_value={"rendered": True, "asset": "intermediates/S1/rendered.pdf"}):
            report = module.normalize(self.sources, self.output)
        item = next(source for source in report["sources"] if source["path"] == "shared-warning.xlsx")
        self.assertEqual("PARTIAL", item["coverage"])
        self.assertEqual("PARTIAL", report["status"])

    def test_visual_ownership_is_recorded_and_unreferenced_media_separated(self):
        document = self.sources / "owned.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", '<document xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><body><p><drawing r:embed="rImg"/></p></body></document>')
            archive.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship Id="rImg" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/used.png"/></Relationships>')
            archive.writestr("word/media/used.png", b"used")
            archive.writestr("word/media/orphan.png", b"orphan")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "owned.docx")
        self.assertTrue(any(visual["owner"] == "DOCX paragraph 1" and visual["target"].endswith("used.png") for visual in item["visuals"]))
        self.assertTrue(any(visual["owner"] == "unreferenced package media" and visual["target"].endswith("orphan.png") for visual in item["visuals"]))

    def test_plain_id_attribute_is_not_a_relationship_reference(self):
        document = self.sources / "plain-id.docx"
        with ZipFile(str(document), "w", ZIP_DEFLATED) as archive:
            archive.writestr("word/document.xml", '<document><body><p><drawing><shape id="rImg"/></drawing></p></body></document>')
            archive.writestr("word/_rels/document.xml.rels", '<Relationships><Relationship Id="rImg" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/image.png"/></Relationships>')
            archive.writestr("word/media/image.png", b"image")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "plain-id.docx")
        self.assertFalse(any(visual["owner"].startswith("DOCX paragraph") for visual in item["visuals"]))

    def test_plain_sheet_id_does_not_override_relationship_id(self):
        workbook = self.sources / "plain-sheet-id.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Correct" id="wrong" r:id="right"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="right" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="wrong" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet><c r="A1"><v>correct</v></c></worksheet>')
            archive.writestr("xl/worksheets/sheet2.xml", '<worksheet><c r="A1"><v>wrong</v></c></worksheet>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "plain-sheet-id.xlsx")
        content = (self.output / item["normalized"]).read_text()
        self.assertIn("A1 = correct", content)
        self.assertNotIn("A1 = wrong", content)

    def test_plain_drawing_id_does_not_override_relationship_id(self):
        workbook = self.sources / "plain-drawing-id.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Owned" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing id="wrong" r:id="right"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="right" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing/>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "plain-drawing-id.xlsx")
        self.assertFalse(any("unresolved drawing" in warning for warning in item["warnings"]))

    def test_xlsx_and_pptx_visuals_are_associated_with_owner(self):
        workbook = self.sources / "owned.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Owned" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><twoCellAnchor><from><col>0</col><row>1</row></from><to><col>2</col><row>4</row></to><graphicFrame r:id="chart"/><pic r:embed="image"/></twoCellAnchor></drawing>')
            archive.writestr("xl/drawings/_rels/drawing1.xml.rels", '<Relationships><Relationship Id="chart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart1.xml"/><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.png"/></Relationships>')
            archive.writestr("xl/charts/chart1.xml", '<chart/>')
            archive.writestr("xl/media/image1.png", b"image")
        presentation = self.sources / "owned.pptx"
        with ZipFile(str(presentation), "w", ZIP_DEFLATED) as archive:
            archive.writestr("ppt/presentation.xml", '<presentation xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sldIdLst><sldId r:id="slide"/></sldIdLst></presentation>')
            archive.writestr("ppt/_rels/presentation.xml.rels", '<Relationships><Relationship Id="slide" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>')
            archive.writestr("ppt/slides/slide1.xml", '<slide xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><pic r:embed="image"/><graphicFrame r:id="chart"/></slide>')
            archive.writestr("ppt/slides/_rels/slide1.xml.rels", '<Relationships><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image1.png"/><Relationship Id="chart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart1.xml"/></Relationships>')
            archive.writestr("ppt/media/image1.png", b"image")
            archive.writestr("ppt/media/orphan.png", b"orphan")
            archive.writestr("ppt/charts/chart1.xml", '<chart/>')
        report = self.normalize()
        by_path = {item["path"]: item for item in report["sources"]}
        self.assertTrue(any(v["owner"].startswith("XLSX sheet Owned") and "A2:C5" in v["owner"] for v in by_path["owned.xlsx"]["visuals"]))
        self.assertTrue(any(v["owner"] == "PPTX slide 1" and v["target"].endswith("image1.png") for v in by_path["owned.pptx"]["visuals"]))
        self.assertFalse(any(v["target"].endswith("orphan.png") for v in by_path["owned.pptx"]["visuals"]))

    def test_promote_evidence_success_and_rollback(self):
        module = self.load_tool("document_ingest_promote")
        target = Path(self.temp.name) / "evidence/topic"
        target.mkdir(parents=True)
        (target / "manifest.md").write_text("old")
        fresh = target.parent / ".topic-update"
        fresh.mkdir()
        (fresh / "manifest.md").write_text("new")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        result = module.promote_evidence(fresh, target)
        self.assertEqual("new", (target / "manifest.md").read_text())
        self.assertFalse(Path(result["backup"]).exists())

        failed_fresh = target.parent / ".topic-failed"
        failed_fresh.mkdir()
        (failed_fresh / "manifest.md").write_text("failed")
        (failed_fresh / "extraction-report.json").write_text(self.empty_report(failed_fresh))
        real_replace = module.os.replace
        calls = []
        def fail_promotion(source, destination):
            calls.append((Path(source), Path(destination)))
            if Path(source) == failed_fresh:
                raise OSError("promotion failed")
            return real_replace(source, destination)
        with mock.patch.object(module.os, "replace", side_effect=fail_promotion):
            with self.assertRaisesRegex(OSError, "promotion failed"):
                module.promote_evidence(failed_fresh, target)
        self.assertEqual("new", (target / "manifest.md").read_text())
        self.assertTrue(failed_fresh.exists())
        self.assertEqual(failed_fresh.resolve(), Path(json.loads((failed_fresh / "extraction-report.json").read_text())["output_root"]).resolve())

    def test_promote_requires_completed_sibling(self):
        module = self.load_tool("document_ingest_promote_validation")
        target = Path(self.temp.name) / "evidence/topic"
        fresh = target.parent / ".topic-invalid"
        fresh.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "manifest.md"):
            module.promote_evidence(fresh, target)

    def test_promote_validates_report_and_referenced_artifacts(self):
        module = self.load_tool("document_ingest_promote_report")
        target = Path(self.temp.name) / "evidence/topic"
        fresh = target.parent / ".topic-invalid-report"
        fresh.mkdir(parents=True)
        (fresh / "manifest.md").write_text("manifest")
        report = {"status": "COMPLETE", "source_root": "/source", "output_root": str(fresh), "sources": [{"id":"S1","path":"source.txt","format":"txt","status":"COMPLETE","coverage":"COMPLETE","method":"direct","normalized":"sources/S1/missing.md","assets":[],"visuals":[]}]}
        (fresh / "extraction-report.json").write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "referenced artifact"):
            module.promote_evidence(fresh, target)
        (fresh / "extraction-report.json").write_text("not json")
        with self.assertRaisesRegex(ValueError, "valid JSON"):
            module.promote_evidence(fresh, target)

    def test_direct_pdf_image_and_svg_validation(self):
        (self.sources / "bad.pdf").write_bytes(b"not pdf")
        (self.sources / "bad.png").write_bytes(b"not png")
        (self.sources / "bad.svg").write_text("not svg")
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("bad.pdf", "bad.png", "bad.svg"):
            self.assertEqual("FAILED", by_path[name]["status"])
        self.assertEqual("PARTIAL", report["status"])

    def test_truncated_pdf_and_raster_signatures_fail(self):
        (self.sources / "truncated.pdf").write_bytes(b"%PDF-")
        (self.sources / "truncated.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (self.sources / "truncated.jpg").write_bytes(b"\xff\xd8\xff")
        (self.sources / "truncated.gif").write_bytes(b"GIF89a")
        (self.sources / "truncated.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBP")
        report = self.normalize()
        by_path = {source["path"]: source for source in report["sources"]}
        for name in ("truncated.pdf", "truncated.png", "truncated.jpg", "truncated.gif", "truncated.webp"):
            self.assertEqual("FAILED", by_path[name]["status"])

    def test_promote_requires_strict_report_schema_and_no_symlinks(self):
        module = self.load_tool("document_ingest_promote_schema")
        target = Path(self.temp.name) / "evidence/topic"
        for index, report in enumerate(("{}", '{"sources":[null]}', '{"sources":[{"normalized":1,"assets":null}]}')):
            fresh = target.parent / ".invalid-{}".format(index)
            fresh.mkdir(parents=True)
            (fresh / "manifest.md").write_text("manifest")
            (fresh / "extraction-report.json").write_text(report)
            with self.assertRaises(ValueError):
                module.promote_evidence(fresh, target)
        real = target.parent / ".real"
        real.mkdir()
        (real / "manifest.md").write_text("manifest")
        (real / "extraction-report.json").write_text(self.empty_report(fresh))
        linked = target.parent / ".linked"
        try:
            linked.symlink_to(real, target_is_directory=True)
        except (OSError, NotImplementedError):
            return
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            module.promote_evidence(linked, target)

    def test_promote_rejects_symlinked_metadata_tree_target_and_incomplete_sources(self):
        module = self.load_tool("document_ingest_promote_strict")
        target = Path(self.temp.name) / "evidence/topic"
        real_report = Path(self.temp.name) / "outside-report.json"
        fresh = target.parent / ".strict-update"
        fresh.mkdir(parents=True)
        real_report.write_text(self.empty_report(fresh))
        (fresh / "manifest.md").write_text("manifest")
        try:
            (fresh / "extraction-report.json").symlink_to(real_report)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            module.promote_evidence(fresh, target)
        (fresh / "extraction-report.json").unlink()
        invalid = json.loads(self.empty_report(fresh))
        invalid["sources"] = [{}]
        (fresh / "extraction-report.json").write_text(json.dumps(invalid))
        with self.assertRaisesRegex(ValueError, "required fields"):
            module.promote_evidence(fresh, target)
        (fresh / "unreferenced-link").symlink_to(real_report)
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            module.promote_evidence(fresh, target)
        shutil.rmtree(str(fresh))
        real_target = target.parent / "outside-target"
        real_target.mkdir()
        target.symlink_to(real_target, target_is_directory=True)
        fresh.mkdir()
        (fresh / "manifest.md").write_text("manifest")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        with self.assertRaisesRegex(ValueError, "target.*symbolic link"):
            module.promote_evidence(fresh, target)

    def test_wide_xlsx_visual_anchor_uses_excel_column_names(self):
        workbook = self.sources / "wide-owned.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Wide" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><twoCellAnchor><from><col>26</col><row>0</row></from><to><col>27</col><row>1</row></to><pic r:embed="image"/></twoCellAnchor></drawing>')
            archive.writestr("xl/drawings/_rels/drawing1.xml.rels", '<Relationships><Relationship Id="image" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image.png"/></Relationships>')
            archive.writestr("xl/media/image.png", b"image")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "wide-owned.xlsx")
        self.assertTrue(any("AA1:AB2" in visual["owner"] for visual in item["visuals"]))

    def test_oversized_svg_fails_before_xml_parse(self):
        oversized = self.sources / "oversized.svg"
        with oversized.open("wb") as output:
            output.seek(65 * 1024 * 1024)
            output.write(b"x")
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "oversized.svg")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("size limit", item["reason"])

    def test_promote_rejects_same_path_file_target_and_invalid_contract(self):
        module = self.load_tool("document_ingest_promote_contract")
        root = Path(self.temp.name) / "evidence"
        fresh = root / "fresh"
        fresh.mkdir(parents=True)
        (fresh / "manifest.md").write_text("manifest")
        valid = {"status": "COMPLETE", "source_root": "/source", "output_root": str(fresh), "sources": []}
        (fresh / "extraction-report.json").write_text(json.dumps(valid))
        with self.assertRaisesRegex(ValueError, "different"):
            module.promote_evidence(fresh, fresh)
        file_target = root / "file-target"
        file_target.write_text("keep")
        with self.assertRaisesRegex(ValueError, "directory"):
            module.promote_evidence(fresh, file_target)
        invalid = dict(valid)
        invalid["status"] = "UNKNOWN"
        (fresh / "extraction-report.json").write_text(json.dumps(invalid))
        with self.assertRaisesRegex(ValueError, "status"):
            module.promote_evidence(fresh, root / "target")

    def test_promote_rejects_inconsistent_status_coverage(self):
        module = self.load_tool("document_ingest_promote_consistency")
        target = Path(self.temp.name) / "evidence/topic"
        fresh = target.parent / ".topic-update"
        fresh.mkdir(parents=True)
        (fresh / "manifest.md").write_text("manifest")
        report = {"status": "COMPLETE", "source_root": "/source", "output_root": str(fresh), "sources": [{"id": "S1", "path": "bad.doc", "format": "doc", "status": "FAILED", "coverage": "FAILED", "method": "none", "normalized": None, "assets": [], "visuals": []}]}
        (fresh / "extraction-report.json").write_text(json.dumps(report))
        with self.assertRaisesRegex(ValueError, "overall.*PARTIAL"):
            module.promote_evidence(fresh, target)

    def test_normalize_rejects_symlinked_source_or_output_root(self):
        module = self.load_tool("document_ingest_root_links")
        linked_source = Path(self.temp.name) / "linked-source"
        linked_output = Path(self.temp.name) / "linked-output"
        try:
            linked_source.symlink_to(self.sources, target_is_directory=True)
            linked_output.symlink_to(Path(self.temp.name) / "actual-output", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "source.*symbolic link"):
            module.normalize(linked_source, self.output)
        with self.assertRaisesRegex(ValueError, "output.*symbolic link"):
            module.normalize(self.sources, linked_output)

    def test_invalid_xlsx_drawing_anchor_fails_source(self):
        workbook = self.sources / "invalid-anchor.xlsx"
        with ZipFile(str(workbook), "w", ZIP_DEFLATED) as archive:
            archive.writestr("xl/workbook.xml", '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Bad" r:id="sheet"/></sheets></workbook>')
            archive.writestr("xl/_rels/workbook.xml.rels", '<Relationships><Relationship Id="sheet" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
            archive.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><drawing r:id="drawing"/></worksheet>')
            archive.writestr("xl/worksheets/_rels/sheet1.xml.rels", '<Relationships><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>')
            archive.writestr("xl/drawings/drawing1.xml", '<drawing><twoCellAnchor><from><col>-1</col><row>0</row></from><to><col>1</col><row>1</row></to></twoCellAnchor></drawing>')
        report = self.normalize()
        item = next(source for source in report["sources"] if source["path"] == "invalid-anchor.xlsx")
        self.assertEqual("FAILED", item["status"])
        self.assertIn("drawing anchor", item["reason"])

    def test_promote_rewrites_output_root_and_cleans_failed_backup_container(self):
        module = self.load_tool("document_ingest_promote_metadata")
        target = Path(self.temp.name) / "evidence/topic"
        target.mkdir(parents=True)
        (target / "manifest.md").write_text("old")
        fresh = target.parent / ".topic-update"
        fresh.mkdir()
        (fresh / "manifest.md").write_text("new")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        module.promote_evidence(fresh, target)
        self.assertEqual(str(target.resolve()), json.loads((target / "extraction-report.json").read_text())["output_root"])

        failed_target = target.parent / "failed"
        failed_target.mkdir()
        (failed_target / "manifest.md").write_text("old")
        failed_fresh = target.parent / ".failed-update"
        failed_fresh.mkdir()
        (failed_fresh / "manifest.md").write_text("new")
        (failed_fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        with mock.patch.object(module.os, "replace", side_effect=OSError("first rename failed")):
            with self.assertRaises(OSError):
                module.promote_evidence(failed_fresh, failed_target)
        self.assertFalse(list(target.parent.glob(".failed-backup-*")))

    def test_promote_without_prior_target_leaves_no_backup_container(self):
        module = self.load_tool("document_ingest_promote_new")
        target = Path(self.temp.name) / "evidence/topic"
        fresh = target.parent / ".topic-update"
        fresh.mkdir(parents=True)
        (fresh / "manifest.md").write_text("manifest")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        result = module.promote_evidence(fresh, target)
        self.assertIsNone(result["backup"])
        self.assertFalse(list(target.parent.glob(".topic-backup-*")))

    def test_post_promotion_backup_cleanup_failure_preserves_backup(self):
        module = self.load_tool("document_ingest_promote_cleanup")
        target = Path(self.temp.name) / "evidence/topic"
        target.mkdir(parents=True)
        (target / "manifest.md").write_text("old")
        fresh = target.parent / ".topic-update"
        fresh.mkdir()
        (fresh / "manifest.md").write_text("new")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        real_rmtree = module.shutil.rmtree
        def fail_backup_cleanup(path):
            if "backup" in str(path):
                raise OSError("cleanup failed")
            return real_rmtree(path)
        with mock.patch.object(module.shutil, "rmtree", side_effect=fail_backup_cleanup):
            result = module.promote_evidence(fresh, target)
        self.assertEqual("new", (target / "manifest.md").read_text())
        self.assertIn("cleanup failed", result["warning"])
        self.assertTrue(Path(result["backup"]).exists())

    def test_promote_uses_collision_free_backup_and_reports_failed_rollback(self):
        module = self.load_tool("document_ingest_promote_failures")
        target = Path(self.temp.name) / "evidence/topic"
        target.mkdir(parents=True)
        (target / "manifest.md").write_text("old")
        fresh = target.parent / ".topic-update"
        fresh.mkdir()
        (fresh / "manifest.md").write_text("new")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        existing_backup = target.parent / ".topic-backup-existing"
        existing_backup.mkdir()
        (existing_backup / "keep").write_text("keep")
        real_replace = module.os.replace
        def fail_swap_and_restore(source, destination):
            source = Path(source)
            destination = Path(destination)
            if source == fresh or source.name == "previous":
                raise OSError("rename failure")
            return real_replace(str(source), str(destination))
        with mock.patch.object(module.os, "replace", side_effect=fail_swap_and_restore):
            with self.assertRaisesRegex(RuntimeError, "promotion failed.*rollback failed"):
                module.promote_evidence(fresh, target)
        self.assertEqual("keep", (existing_backup / "keep").read_text())

    def test_promote_keeps_backup_container_reserved(self):
        module = self.load_tool("document_ingest_promote_reserved")
        target = Path(self.temp.name) / "evidence/topic"
        target.mkdir(parents=True)
        (target / "manifest.md").write_text("old")
        fresh = target.parent / ".topic-update"
        fresh.mkdir()
        (fresh / "manifest.md").write_text("new")
        (fresh / "extraction-report.json").write_text(self.empty_report(fresh))
        real_replace = module.os.replace
        calls = []
        def observe_replace(source, destination):
            calls.append((Path(source), Path(destination)))
            return real_replace(source, destination)
        with mock.patch.object(module.os, "replace", side_effect=observe_replace):
            module.promote_evidence(fresh, target)
        self.assertEqual("previous", calls[0][1].name)
        self.assertIn("backup", calls[0][1].parent.name)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
import argparse
import json
import struct
import zlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


SYNTHETIC = "Synthetic fixture; contains no client information."


def png_bytes():
    raw = b"\x00\xff\xff\xff"  # filter byte + one white RGB pixel
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def write_zip(path, entries):
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, content)


def generate(output):
    if output.exists() and not output.is_dir():
        raise ValueError("output must be a directory")
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    (output / "notes.txt").write_text(f"{SYNTHETIC}\nRequirement: retain audit records.\n")
    (output / "overview.md").write_text(f"# Synthetic overview\n\n{SYNTHETIC}\n")
    image = png_bytes()
    (output / "diagram.png").write_bytes(image)
    # Minimal ZIP fixtures preserve the structures the normalizer consumes.
    write_zip(output / "brief.docx", {
        "word/document.xml": f"<document><p>{SYNTHETIC}</p><tbl><tr><tc>Component</tc><tc>Owner</tc></tr></tbl></document>",
        "word/media/image1.png": image,
    })
    write_zip(output / "capacity.xlsx", {
        "xl/workbook.xml": '<workbook xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Capacity" r:id="sheet1"/><sheet name="Costs" r:id="sheet2"/></sheets></workbook>',
        "xl/_rels/workbook.xml.rels": '<Relationships><Relationship Id="sheet1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="sheet2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/></Relationships>',
        "xl/worksheets/sheet1.xml": '<worksheet xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><c r="A1"><v>Users</v></c><c r="B2"><f>A2*2</f><v>20</v></c><tableParts><tablePart r:id="table"/></tableParts><drawing r:id="drawing"/></worksheet>',
        "xl/worksheets/_rels/sheet1.xml.rels": '<Relationships><Relationship Id="table" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/table" Target="../tables/table1.xml"/><Relationship Id="drawing" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/drawing" Target="../drawings/drawing1.xml"/></Relationships>',
        "xl/drawings/drawing1.xml": '<drawing xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><twoCellAnchor><from><col>0</col><row>0</row></from><to><col>1</col><row>1</row></to><graphicFrame r:id="chart"/></twoCellAnchor></drawing>',
        "xl/drawings/_rels/drawing1.xml.rels": '<Relationships><Relationship Id="chart" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/chart" Target="../charts/chart1.xml"/></Relationships>',
        "xl/worksheets/sheet2.xml": '<worksheet><c r="A1"><v>Cost</v></c></worksheet>',
        "xl/tables/table1.xml": '<table ref="A1:B2" name="CapacityTable"><tableColumns><tableColumn name="Users"/><tableColumn name="Capacity"/></tableColumns></table>',
        "xl/charts/chart1.xml": '<chart><title>Synthetic capacity</title></chart>',
    })
    write_zip(output / "roadmap.pptx", {
        "ppt/slides/slide1.xml": f"<slide><text>{SYNTHETIC}</text></slide>",
        "ppt/slides/_rels/slide1.xml.rels": '<Relationships><Relationship Id="notes" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" Target="../notesSlides/notesSlide1.xml"/></Relationships>',
        "ppt/notesSlides/notesSlide1.xml": '<notes><text>Synthetic speaker note</text></notes>',
        "ppt/media/image1.png": image,
    })
    # A tiny valid PDF and explicit failure cases are enough for routing tests.
    pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n"
    (output / "visual.pdf").write_bytes(pdf)
    for legacy in ("old.doc", "old.xls", "old.ppt"):
        (output / legacy).write_text(SYNTHETIC)
    (output / "unreadable.docx").write_bytes(b"not a zip")
    (output / "fixture-manifest.json").write_text(json.dumps({
        "synthetic": True,
        "features": ["embedded-visual", "multi-sheet", "formula", "chart", "speaker-notes", "unreadable"],
    }, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() == Path(__file__).resolve().parent:
        parser.error("output must not overwrite the checked-in fixture definition directory")
    try:
        generate(args.output.resolve())
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
